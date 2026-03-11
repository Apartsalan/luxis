"""E2E Intake Test — tests the full intake pipeline: email → detect → process → approve/reject.

Runs inside the backend container against the real database.
AI extraction is mocked for speed and determinism.

Usage:
    python -m scripts.e2e_intake_test              # Run all 4 scenarios
    python -m scripts.e2e_intake_test --dry-run     # Print scenarios without DB
    python -m scripts.e2e_intake_test --cleanup     # Remove all [E2E-INTAKE] test data
"""

import argparse
import asyncio
import logging
import os
import sys
import traceback
import uuid
import warnings

# Suppress SQL echo and SQLAlchemy warnings BEFORE importing app modules
os.environ["APP_DEBUG"] = "false"
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlalchemy")
warnings.filterwarnings("ignore", message=".*relationship.*overlaps.*", category=Warning)
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Import ALL models so SQLAlchemy mappers are fully configured.
# Mirrors backend/alembic/env.py to avoid "failed to locate a name" errors.
from app.ai_agent.followup_models import FollowupRecommendation  # noqa: F401
from app.ai_agent.models import EmailClassification, ResponseTemplate  # noqa: F401
from app.documents.models import DocumentTemplate, GeneratedDocument  # noqa: F401
from app.email.attachment_models import EmailAttachment  # noqa: F401
from app.incasso.models import IncassoPipelineStep  # noqa: F401
from app.invoices.models import Expense, Invoice, InvoiceLine, InvoicePayment  # noqa: F401
from app.relations.kyc_models import KycVerification  # noqa: F401
from app.relations.models import Contact, ContactLink  # noqa: F401

# Suppress SQLAlchemy SQL echo — we only want our test output
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
from app.time_entries.models import TimeEntry  # noqa: F401
from app.trust_funds.models import TrustTransaction  # noqa: F401
from app.workflow.models import WorkflowRule, WorkflowStatus, WorkflowTask, WorkflowTransition  # noqa: F401,E501

from app.ai_agent.intake_models import IntakeRequest, IntakeStatus
from app.ai_agent.intake_service import (
    approve_intake,
    detect_intake_emails,
    process_intake,
    reject_intake,
)
from app.auth.models import Tenant, User  # noqa: F811
from app.cases.models import Case, CaseActivity
from app.collections.models import Claim
from app.database import async_session
from app.email.oauth_models import EmailAccount
from app.email.synced_email_models import SyncedEmail

# =============================================================================
# Constants
# =============================================================================
TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

# Deterministic UUID namespace (different from seed script to avoid collision)
NS = uuid.UUID("e2e10000-cafe-babe-dead-e2e1a4ce0000")
MARKER = "[E2E-INTAKE]"


def _uid(name: str) -> uuid.UUID:
    return uuid.uuid5(NS, name)


# Deterministic IDs
CLIENT_CONTACT_ID = _uid("e2e-client-contact")
CLIENT_CASE_ID = _uid("e2e-client-case")
EMAIL_ACCOUNT_ID = _uid("e2e-email-account")

# Fake AI response — all fields populated (used in happy path + edit scenarios)
FAKE_AI_RESPONSE = {
    "debtor_name": "E2E Debiteur B.V.",
    "debtor_email": "debiteur@e2e-test.nl",
    "debtor_kvk": "99887766",
    "debtor_address": "Teststraat 42",
    "debtor_city": "Amsterdam",
    "debtor_postcode": "1000 AA",
    "debtor_type": "company",
    "invoice_number": "E2E-F-2026-001",
    "invoice_date": "2026-01-15",
    "due_date": "2026-02-15",
    "principal_amount": 5000.00,
    "description": "E2E test factuur — consultancy diensten",
    "confidence": 0.93,
    "reasoning": f"{MARKER} Alle gegevens geëxtraheerd uit email en factuur.",
}


# =============================================================================
# Helpers
# =============================================================================


class ScenarioResult:
    """Result of a single test scenario."""

    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error: str | None = None
        self.details: list[str] = []

    def check(self, condition: bool, message: str) -> None:
        """Assert a condition, record detail."""
        status = "OK" if condition else "FAIL"
        self.details.append(f"  {status}: {message}")
        if not condition:
            self.passed = False
            self.error = self.error or message

    def mark_passed(self) -> None:
        self.passed = True


async def _create_prerequisites(db: AsyncSession) -> None:
    """Create the shared prerequisites: client contact + case + email account."""
    # Client contact (the "opdrachtgever" whose emails trigger intake)
    client = Contact(
        id=CLIENT_CONTACT_ID,
        tenant_id=TENANT_ID,
        contact_type="company",
        name=f"{MARKER} E2E Test Opdrachtgever B.V.",
        email="e2e-client@testintake.nl",
    )
    db.add(client)
    await db.flush()

    # Existing case with this client (makes them a "known client" for detection)
    case = Case(
        id=CLIENT_CASE_ID,
        tenant_id=TENANT_ID,
        case_number="E2E-9999",
        case_type="incasso",
        debtor_type="b2b",
        status="sommatie",
        client_id=CLIENT_CONTACT_ID,
        assigned_to_id=USER_ID,
        date_opened=date.today(),
        description=f"{MARKER} E2E prerequisite case",
    )
    db.add(case)
    await db.flush()

    # Email account — use provider="e2e_test" to avoid unique constraint
    # collision with the real outlook account in production
    account = EmailAccount(
        id=EMAIL_ACCOUNT_ID,
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        provider="e2e_test",
        email_address="e2e-test@kestinglegal.nl",
        access_token_enc=b"e2e_dummy_token",
        refresh_token_enc=b"e2e_dummy_refresh",
    )
    db.add(account)
    await db.flush()


async def _create_synced_email(
    db: AsyncSession,
    key: str,
    *,
    from_email: str = "e2e-client@testintake.nl",
    subject: str = "E2E Intake Test Email",
    body: str = "Bijgaand de factuur van E2E Debiteur B.V. Bedrag EUR 5.000.",
    case_id: uuid.UUID | None = None,
) -> SyncedEmail:
    """Create a synced email for testing."""
    email = SyncedEmail(
        id=_uid(f"email-{key}"),
        tenant_id=TENANT_ID,
        email_account_id=EMAIL_ACCOUNT_ID,
        provider_message_id=f"e2e-intake-{key}",
        subject=f"{MARKER} {subject}",
        from_email=from_email,
        from_name="E2E Client",
        body_text=body,
        body_html="",
        direction="inbound",
        email_date=datetime.now(UTC) - timedelta(hours=1),
        case_id=case_id,
    )
    db.add(email)
    await db.flush()
    return email


# =============================================================================
# Scenario 1: Happy Path
# =============================================================================


async def scenario_happy_path(db: AsyncSession) -> ScenarioResult:
    """Full pipeline: email → detect → process (mocked AI) → approve → verify."""
    result = ScenarioResult("Happy Path (email → detect → process → approve → dossier)")

    # 1. Create email from known client
    email = await _create_synced_email(db, "happy")
    await db.commit()

    # 2. Detect
    detected = await detect_intake_emails(db, TENANT_ID)
    result.check(detected >= 1, f"detect_intake_emails returned {detected} (expected ≥1)")

    # Find the intake request
    intake_result = await db.execute(
        select(IntakeRequest).where(IntakeRequest.synced_email_id == email.id)
    )
    intake = intake_result.scalar_one_or_none()
    result.check(intake is not None, "IntakeRequest was created")
    if not intake:
        return result

    result.check(
        intake.status == IntakeStatus.DETECTED,
        f"Status is '{intake.status}' (expected 'detected')",
    )
    result.check(
        intake.client_contact_id == CLIENT_CONTACT_ID,
        "client_contact_id matches known client",
    )

    # 3. Process with mocked AI
    with patch(
        "app.ai_agent.intake_service.call_intake_ai",
        new_callable=AsyncMock,
        return_value=(FAKE_AI_RESPONSE, "e2e-mock-model"),
    ):
        processed = await process_intake(db, intake.id, TENANT_ID)
    await db.commit()

    result.check(processed is not None, "process_intake returned result")
    if not processed:
        return result

    result.check(
        processed.status == IntakeStatus.PENDING_REVIEW,
        f"Status is '{processed.status}' (expected 'pending_review')",
    )
    result.check(
        processed.debtor_name == "E2E Debiteur B.V.",
        f"debtor_name='{processed.debtor_name}'",
    )
    result.check(
        processed.principal_amount == Decimal("5000.00"),
        f"principal_amount={processed.principal_amount}",
    )
    result.check(
        processed.invoice_number == "E2E-F-2026-001",
        f"invoice_number='{processed.invoice_number}'",
    )
    result.check(
        processed.ai_model == "e2e-mock-model",
        f"ai_model='{processed.ai_model}'",
    )

    # 4. Approve
    approved = await approve_intake(
        db, intake.id, TENANT_ID, USER_ID, note=f"{MARKER} Goedgekeurd via E2E test"
    )
    await db.commit()

    result.check(approved is not None, "approve_intake returned result")
    if not approved:
        return result

    result.check(
        approved.status == IntakeStatus.APPROVED,
        f"Status is '{approved.status}' (expected 'approved')",
    )
    result.check(
        approved.created_case_id is not None,
        "created_case_id is set",
    )
    result.check(
        approved.created_contact_id is not None,
        "created_contact_id is set",
    )

    # 5. Verify created case
    if approved.created_case_id:
        case_result = await db.execute(
            select(Case).where(Case.id == approved.created_case_id)
        )
        case = case_result.scalar_one_or_none()
        result.check(case is not None, "Created case exists in DB")
        if case:
            result.check(case.case_type == "incasso", f"case_type='{case.case_type}'")
            result.check(case.debtor_type == "b2b", f"debtor_type='{case.debtor_type}'")
            result.check(case.status == "nieuw", f"case_status='{case.status}'")
            result.check(
                case.total_principal == Decimal("5000.00"),
                f"total_principal={case.total_principal}",
            )
            result.check(
                case.client_id == CLIENT_CONTACT_ID,
                "case.client_id matches known client",
            )

            # Verify claim
            claim_result = await db.execute(
                select(Claim).where(Claim.case_id == case.id)
            )
            claim = claim_result.scalar_one_or_none()
            result.check(claim is not None, "Claim was created")
            if claim:
                result.check(
                    claim.principal_amount == Decimal("5000.00"),
                    f"claim.principal_amount={claim.principal_amount}",
                )
                result.check(
                    claim.invoice_number == "E2E-F-2026-001",
                    f"claim.invoice_number='{claim.invoice_number}'",
                )

    # 6. Verify debtor contact
    if approved.created_contact_id:
        contact_result = await db.execute(
            select(Contact).where(Contact.id == approved.created_contact_id)
        )
        contact = contact_result.scalar_one_or_none()
        result.check(contact is not None, "Debtor contact exists in DB")
        if contact:
            result.check(
                contact.name == "E2E Debiteur B.V.",
                f"contact.name='{contact.name}'",
            )
            result.check(
                contact.kvk_number == "99887766",
                f"contact.kvk_number='{contact.kvk_number}'",
            )
            result.check(
                contact.contact_type == "company",
                f"contact.contact_type='{contact.contact_type}'",
            )

    result.mark_passed()
    return result


# =============================================================================
# Scenario 2: Email Without Usable Body
# =============================================================================


async def scenario_empty_body(db: AsyncSession) -> ScenarioResult:
    """Email with empty body → detect succeeds, process fails."""
    result = ScenarioResult("Email zonder bruikbare body (→ failed)")

    email = await _create_synced_email(
        db, "empty-body",
        body="",
        subject="Lege email",
    )
    await db.commit()

    # Detect
    detected = await detect_intake_emails(db, TENANT_ID)
    result.check(detected >= 1, f"detect_intake_emails returned {detected}")

    intake_result = await db.execute(
        select(IntakeRequest).where(IntakeRequest.synced_email_id == email.id)
    )
    intake = intake_result.scalar_one_or_none()
    result.check(intake is not None, "IntakeRequest was created")
    if not intake:
        return result

    result.check(
        intake.status == IntakeStatus.DETECTED,
        f"Status is '{intake.status}' (expected 'detected')",
    )

    # Process — should fail because empty body
    processed = await process_intake(db, intake.id, TENANT_ID)
    await db.commit()

    result.check(processed is not None, "process_intake returned result")
    if not processed:
        return result

    result.check(
        processed.status == IntakeStatus.FAILED,
        f"Status is '{processed.status}' (expected 'failed')",
    )
    result.check(
        processed.error_message is not None and "leesbare inhoud" in processed.error_message,
        f"error_message='{processed.error_message}'",
    )

    result.mark_passed()
    return result


# =============================================================================
# Scenario 3: Edit Before Approve
# =============================================================================


async def scenario_edit_before_approve(db: AsyncSession) -> ScenarioResult:
    """Seed pending_review intake → edit fields → approve → verify corrected data."""
    result = ScenarioResult("Edit-before-approve (data corrigeren, dan goedkeuren)")

    # Create email + intake directly in pending_review with incomplete data
    email = await _create_synced_email(
        db, "edit-approve",
        body="Debiteur naam onbekend, factuur bijgevoegd.",
    )
    await db.flush()

    intake = IntakeRequest(
        id=_uid("intake-edit-approve"),
        tenant_id=TENANT_ID,
        synced_email_id=email.id,
        client_contact_id=CLIENT_CONTACT_ID,
        status=IntakeStatus.PENDING_REVIEW,
        debtor_name="Onbekend",
        debtor_type="company",
        principal_amount=Decimal("3000.00"),
        due_date=date.today() - timedelta(days=30),
        ai_model="e2e-mock",
        ai_confidence=0.50,
        ai_reasoning=f"{MARKER} Incomplete extractie, handmatige correctie nodig.",
        raw_extraction="{}",
    )
    db.add(intake)
    await db.commit()

    # Edit: correct the debtor name and add address
    intake.debtor_name = "Gecorrigeerd Bedrijf B.V."
    intake.debtor_address = "Handmatig Toegevoegd 10"
    intake.debtor_city = "Rotterdam"
    intake.debtor_postcode = "3000 AB"
    intake.debtor_kvk = "11223344"
    intake.invoice_number = "EDIT-001"
    await db.commit()

    result.check(
        intake.debtor_name == "Gecorrigeerd Bedrijf B.V.",
        "debtor_name updated to corrected value",
    )

    # Approve
    approved = await approve_intake(
        db, intake.id, TENANT_ID, USER_ID,
        note=f"{MARKER} Handmatig gecorrigeerd en goedgekeurd",
    )
    await db.commit()

    result.check(approved is not None, "approve_intake returned result")
    if not approved:
        return result

    result.check(
        approved.status == IntakeStatus.APPROVED,
        f"Status is '{approved.status}' (expected 'approved')",
    )

    # Verify the CORRECTED data ended up in the contact
    if approved.created_contact_id:
        contact_result = await db.execute(
            select(Contact).where(Contact.id == approved.created_contact_id)
        )
        contact = contact_result.scalar_one_or_none()
        result.check(contact is not None, "Debtor contact exists")
        if contact:
            result.check(
                contact.name == "Gecorrigeerd Bedrijf B.V.",
                f"contact.name='{contact.name}' (expected corrected name)",
            )
            result.check(
                contact.visit_address == "Handmatig Toegevoegd 10",
                f"contact.visit_address='{contact.visit_address}'",
            )
            result.check(
                contact.kvk_number == "11223344",
                f"contact.kvk_number='{contact.kvk_number}'",
            )

    # Verify case
    if approved.created_case_id:
        case_result = await db.execute(
            select(Case).where(Case.id == approved.created_case_id)
        )
        case = case_result.scalar_one_or_none()
        result.check(case is not None, "Created case exists")
        if case:
            result.check(
                case.total_principal == Decimal("3000.00"),
                f"total_principal={case.total_principal}",
            )

            # Verify claim has the edited invoice number
            claim_result = await db.execute(
                select(Claim).where(Claim.case_id == case.id)
            )
            claim = claim_result.scalar_one_or_none()
            result.check(claim is not None, "Claim was created")
            if claim:
                result.check(
                    claim.invoice_number == "EDIT-001",
                    f"claim.invoice_number='{claim.invoice_number}'",
                )

    result.mark_passed()
    return result


# =============================================================================
# Scenario 4: Reject Flow
# =============================================================================


async def scenario_reject(db: AsyncSession) -> ScenarioResult:
    """Seed pending_review intake → reject → verify no case/contact created."""
    result = ScenarioResult("Reject flow (afwijzen, geen dossier)")

    email = await _create_synced_email(
        db, "reject",
        body="Dit is geen incasso-opdracht, gewoon een vraag.",
        subject="Vraag over factuur",
    )
    await db.flush()

    intake = IntakeRequest(
        id=_uid("intake-reject"),
        tenant_id=TENANT_ID,
        synced_email_id=email.id,
        client_contact_id=CLIENT_CONTACT_ID,
        status=IntakeStatus.PENDING_REVIEW,
        debtor_name="Geen Debiteur",
        debtor_type="company",
        ai_model="e2e-mock",
        ai_confidence=0.35,
        ai_reasoning=f"{MARKER} Lage confidence, waarschijnlijk geen intake.",
        raw_extraction="{}",
    )
    db.add(intake)
    await db.commit()

    # Reject
    rejected = await reject_intake(
        db, intake.id, TENANT_ID, USER_ID,
        note=f"{MARKER} Geen incasso-opdracht, afgewezen",
    )
    await db.commit()

    result.check(rejected is not None, "reject_intake returned result")
    if not rejected:
        return result

    result.check(
        rejected.status == IntakeStatus.REJECTED,
        f"Status is '{rejected.status}' (expected 'rejected')",
    )
    result.check(
        rejected.reviewed_by_id == USER_ID,
        "reviewed_by_id is set",
    )
    result.check(
        rejected.review_note is not None and "Geen incasso-opdracht" in rejected.review_note,
        f"review_note='{rejected.review_note}'",
    )
    result.check(
        rejected.created_case_id is None,
        "No case was created (created_case_id is None)",
    )
    result.check(
        rejected.created_contact_id is None,
        "No contact was created (created_contact_id is None)",
    )

    result.mark_passed()
    return result


# =============================================================================
# Cleanup
# =============================================================================


async def cleanup() -> None:
    """Remove all E2E intake test data identified by the [E2E-INTAKE] marker.

    Uses raw SQL for proper FK ordering:
    1. Unlink synced_emails from created cases (set case_id = NULL)
    2. Delete intake_requests
    3. Delete claims on created cases
    4. Delete case_activities on created cases
    5. Delete created cases
    6. Delete created debtor contacts
    7. Delete test synced_emails
    8. Delete prerequisites (case, contact, email_account)
    """
    async with async_session() as db:
        # 1. Find all intake requests with marker
        intake_result = await db.execute(
            select(IntakeRequest).where(
                IntakeRequest.ai_reasoning.like(f"%{MARKER}%")
            )
        )
        intakes = list(intake_result.scalars().all())

        created_case_ids = [i.created_case_id for i in intakes if i.created_case_id]
        created_contact_ids = [i.created_contact_id for i in intakes if i.created_contact_id]
        intake_ids = [i.id for i in intakes]

        # 2. Unlink synced_emails from created cases (breaks FK before case deletion)
        if created_case_ids:
            await db.execute(
                text("UPDATE synced_emails SET case_id = NULL WHERE case_id = ANY(:ids)"),
                {"ids": created_case_ids},
            )

        # 3. Delete claims
        claims_deleted = 0
        if created_case_ids:
            r = await db.execute(
                delete(Claim).where(Claim.case_id.in_(created_case_ids)).returning(Claim.id)
            )
            claims_deleted = len(r.fetchall())

        # 4. Delete case activities
        activities_deleted = 0
        if created_case_ids:
            r = await db.execute(
                delete(CaseActivity)
                .where(CaseActivity.case_id.in_(created_case_ids))
                .returning(CaseActivity.id)
            )
            activities_deleted = len(r.fetchall())

        # 5. Delete intake requests
        intakes_deleted = 0
        if intake_ids:
            r = await db.execute(
                delete(IntakeRequest)
                .where(IntakeRequest.id.in_(intake_ids))
                .returning(IntakeRequest.id)
            )
            intakes_deleted = len(r.fetchall())

        # 6. Delete created cases
        cases_deleted = 0
        if created_case_ids:
            r = await db.execute(
                delete(Case).where(Case.id.in_(created_case_ids)).returning(Case.id)
            )
            cases_deleted = len(r.fetchall())

        # 7. Delete created debtor contacts
        contacts_deleted = 0
        if created_contact_ids:
            r = await db.execute(
                delete(Contact)
                .where(Contact.id.in_(created_contact_ids))
                .returning(Contact.id)
            )
            contacts_deleted = len(r.fetchall())

        # 8. Delete synced emails with marker in subject
        r = await db.execute(
            delete(SyncedEmail)
            .where(SyncedEmail.subject.like(f"%{MARKER}%"))
            .returning(SyncedEmail.id)
        )
        emails_deleted = len(r.fetchall())

        # 9. Delete prerequisites — unlink emails from prerequisite case first
        await db.execute(
            text("UPDATE synced_emails SET case_id = NULL WHERE case_id = :id"),
            {"id": CLIENT_CASE_ID},
        )
        await db.execute(delete(Case).where(Case.id == CLIENT_CASE_ID))
        await db.execute(delete(Contact).where(Contact.id == CLIENT_CONTACT_ID))
        await db.execute(delete(EmailAccount).where(EmailAccount.id == EMAIL_ACCOUNT_ID))

        await db.commit()

        print("=" * 60)
        print("E2E Intake Test — Cleanup Report")
        print("=" * 60)
        print()
        print(f"  Intake requests deleted:  {intakes_deleted}")
        print(f"  Claims deleted:           {claims_deleted}")
        print(f"  Case activities deleted:  {activities_deleted}")
        print(f"  Cases deleted:            {cases_deleted}")
        print(f"  Debtor contacts deleted:  {contacts_deleted}")
        print(f"  Synced emails deleted:    {emails_deleted}")
        print(f"  Prerequisites removed:    client + case + email account")
        print()
        print("  Cleanup complete.")


# =============================================================================
# Main runner
# =============================================================================


SCENARIOS = [
    ("1. Happy Path", scenario_happy_path),
    ("2. Empty Body", scenario_empty_body),
    ("3. Edit Before Approve", scenario_edit_before_approve),
    ("4. Reject Flow", scenario_reject),
]


def print_dry_run() -> None:
    """Print scenario descriptions without running them."""
    print("=" * 60)
    print("E2E Intake Test — Dry Run")
    print("=" * 60)
    print()
    print("Scenario's die getest worden:")
    print()
    print("  1. Happy Path")
    print("     Email van bekende cliënt → detect → process (AI mock) → approve")
    print("     → verify: case, contact, claim correct aangemaakt")
    print()
    print("  2. Email zonder bruikbare body")
    print("     Lege email → detect → process → FAILED (geen leesbare inhoud)")
    print()
    print("  3. Edit-before-approve")
    print("     Incomplete extractie → handmatig corrigeren → approve")
    print("     → verify: gecorrigeerde data in case/contact")
    print()
    print("  4. Reject flow")
    print("     Geen incasso-opdracht → reject → geen case/contact aangemaakt")
    print()
    print(f"  Marker: {MARKER}")
    print(f"  Tenant: {TENANT_ID}")
    print(f"  User:   {USER_ID}")
    print()
    print("  Gebruik 'python scripts/e2e_intake_test.py' om de tests uit te voeren.")


async def run_all() -> bool:
    """Run all scenarios and report results. Returns True if all pass."""
    print("=" * 60)
    print("E2E Intake Test — Running")
    print("=" * 60)
    print()

    results: list[ScenarioResult] = []

    # Always cleanup first to remove stale data from previous runs
    print("  Cleaning up stale data from previous runs...")
    await cleanup()

    # Create shared prerequisites in their own session
    print("  Setting up prerequisites...")
    async with async_session() as db:
        await _create_prerequisites(db)
        await db.commit()
    print("  Prerequisites created.\n")

    # Run each scenario in its own independent session
    for name, scenario_fn in SCENARIOS:
        print(f"  Running: {name}...")
        try:
            async with async_session() as db:
                result = await scenario_fn(db)
            results.append(result)
            status = "PASS" if result.passed else "FAIL"
            print(f"  → {status}")
        except Exception as e:
            r = ScenarioResult(name)
            r.error = str(e)
            results.append(r)
            print(f"  → ERROR: {e}")
            traceback.print_exc()
        print()

    # Cleanup
    print("  Cleaning up test data...")
    await cleanup()
    print()

    # Report
    print("=" * 60)
    print("E2E Intake Test — Results")
    print("=" * 60)
    print()

    all_passed = True
    for r in results:
        status = "PASS ✓" if r.passed else "FAIL ✗"
        print(f"  {status}  {r.name}")
        if not r.passed:
            all_passed = False
            if r.error:
                print(f"         Error: {r.error}")
        for detail in r.details:
            print(f"       {detail}")
        print()

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"  Result: {passed}/{total} scenarios passed")
    print()

    return all_passed


async def main() -> None:
    parser = argparse.ArgumentParser(description="E2E Intake Test")
    parser.add_argument("--dry-run", action="store_true", help="Print scenarios without running")
    parser.add_argument("--cleanup", action="store_true", help="Remove all E2E test data")
    args = parser.parse_args()

    if args.dry_run:
        print_dry_run()
        return

    if args.cleanup:
        await cleanup()
        return

    all_passed = await run_all()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
