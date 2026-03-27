"""Tests for AI Intake Agent — dossier intake from client emails.

All tests mock call_intake_ai() to avoid real API calls.
Covers: detection, processing, approve/reject, case creation,
multi-tenant isolation, pending count, and API endpoints.
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.intake_models import IntakeRequest, IntakeStatus
from app.ai_agent.intake_service import (
    approve_intake,
    detect_intake_emails,
    get_intake_by_id,
    get_intake_requests,
    get_pending_intake_count,
    process_intake,
    reject_intake,
)
from app.auth.models import Tenant, User
from app.cases.models import Case
from app.collections.models import Claim
from app.email.oauth_models import EmailAccount
from app.email.synced_email_models import SyncedEmail
from app.relations.models import Contact

# Fake AI response for intake extraction
FAKE_INTAKE_RESPONSE = {
    "debtor_name": "Janssen B.V.",
    "debtor_email": "info@janssen.nl",
    "debtor_kvk": "12345678",
    "debtor_address": "Keizersgracht 100",
    "debtor_city": "Amsterdam",
    "debtor_postcode": "1015 AA",
    "debtor_type": "company",
    "invoice_number": "F-2026-001",
    "invoice_date": "2026-01-15",
    "due_date": "2026-02-15",
    "principal_amount": 2500.00,
    "description": "Onbetaalde factuur voor consultancy diensten",
    "confidence": 0.95,
    "reasoning": "Alle gegevens duidelijk geëxtraheerd uit email en factuur-PDF.",
}

FAKE_PARTIAL_RESPONSE = {
    "debtor_name": "Pietersen",
    "debtor_email": None,
    "debtor_kvk": None,
    "debtor_address": None,
    "debtor_city": None,
    "debtor_postcode": None,
    "debtor_type": "person",
    "invoice_number": None,
    "invoice_date": None,
    "due_date": None,
    "principal_amount": 500.00,
    "description": "Onbetaalde rekening",
    "confidence": 0.55,
    "reasoning": "Alleen naam en bedrag gevonden, rest ontbreekt.",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


async def _create_client_with_case(
    db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[Contact, Case]:
    """Create a client contact that has an existing case (making them a known client)."""
    client = Contact(
        tenant_id=tenant_id,
        contact_type="company",
        name="Opdrachtgever B.V.",
        email="client@opdrachtgever.nl",
    )
    db.add(client)
    await db.flush()

    case = Case(
        tenant_id=tenant_id,
        case_number="2026-00099",
        case_type="incasso",
        debtor_type="b2b",
        status="sommatie",
        client_id=client.id,
        assigned_to_id=user_id,
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()
    return client, case


async def _create_email_account(
    db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> EmailAccount:
    """Create a test email account."""
    account = EmailAccount(
        tenant_id=tenant_id,
        user_id=user_id,
        provider="gmail",
        email_address="test@kestinglegal.nl",
        access_token_enc=b"dummy_access_token",
        refresh_token_enc=b"dummy_refresh_token",
    )
    db.add(account)
    await db.flush()
    return account


async def _create_inbound_email(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email_account_id: uuid.UUID,
    from_email: str = "client@opdrachtgever.nl",
    case_id: uuid.UUID | None = None,
    subject: str = "Nieuwe incasso-opdracht",
    body: str = "Bijgaand onze factuur voor Janssen B.V. Bedrag EUR 2.500.",
) -> SyncedEmail:
    """Create a test inbound email."""
    email = SyncedEmail(
        tenant_id=tenant_id,
        email_account_id=email_account_id,
        provider_message_id=f"msg_{uuid.uuid4().hex[:8]}",
        subject=subject,
        from_email=from_email,
        from_name="Client Contact",
        body_text=body,
        direction="inbound",
        email_date=datetime.now(UTC),
        case_id=case_id,
    )
    db.add(email)
    await db.flush()
    return email


# ---------------------------------------------------------------------------
# Tests — Detection
# ---------------------------------------------------------------------------


class TestIntakeDetection:
    """Tests for detect_intake_emails()."""

    async def test_detect_email_from_known_client(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """Inbound email from a known client (without case link) → detected."""
        client, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(db, test_tenant.id, account.id, from_email=client.email)
        await db.commit()

        count = await detect_intake_emails(db, test_tenant.id)
        assert count == 1

        # Check IntakeRequest was created
        result = await db.execute(
            select(IntakeRequest).where(IntakeRequest.synced_email_id == email.id)
        )
        intake = result.scalar_one()
        assert intake.status == IntakeStatus.DETECTED
        assert intake.client_contact_id == client.id

    async def test_skip_email_already_linked_to_case(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """Email already linked to a case should be skipped."""
        client, case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        await _create_inbound_email(
            db,
            test_tenant.id,
            account.id,
            from_email=client.email,
            case_id=case.id,
        )
        await db.commit()

        count = await detect_intake_emails(db, test_tenant.id)
        assert count == 0

    async def test_skip_email_from_unknown_sender(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """Email from unknown sender (not a client) should be skipped."""
        await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        await _create_inbound_email(
            db,
            test_tenant.id,
            account.id,
            from_email="random@stranger.nl",
        )
        await db.commit()

        count = await detect_intake_emails(db, test_tenant.id)
        assert count == 0

    async def test_skip_already_processed_email(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """Already processed emails should not be detected again."""
        client, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(db, test_tenant.id, account.id, from_email=client.email)

        # Create existing intake for this email
        existing_intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            status=IntakeStatus.PENDING_REVIEW,
        )
        db.add(existing_intake)
        await db.commit()

        count = await detect_intake_emails(db, test_tenant.id)
        assert count == 0

    async def test_skip_dismissed_email(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """Dismissed emails should be skipped."""
        client, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(db, test_tenant.id, account.id, from_email=client.email)
        email.is_dismissed = True
        await db.commit()

        count = await detect_intake_emails(db, test_tenant.id)
        assert count == 0


# ---------------------------------------------------------------------------
# Tests — Processing (AI extraction)
# ---------------------------------------------------------------------------


class TestIntakeProcessing:
    """Tests for process_intake() — AI extraction with mocked calls."""

    @patch("app.ai_agent.intake_service.call_intake_ai")
    async def test_process_extracts_all_fields(
        self, mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """Full extraction: all fields populated from AI response."""
        mock_ai.return_value = (FAKE_INTAKE_RESPONSE, "kimi-2.5")

        client, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(db, test_tenant.id, account.id, from_email=client.email)
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            client_contact_id=client.id,
            status=IntakeStatus.DETECTED,
        )
        db.add(intake)
        await db.commit()

        result = await process_intake(db, intake.id, test_tenant.id)
        assert result is not None
        assert result.status == IntakeStatus.PENDING_REVIEW
        assert result.debtor_name == "Janssen B.V."
        assert result.debtor_kvk == "12345678"
        assert result.principal_amount == Decimal("2500.00")
        assert result.invoice_number == "F-2026-001"
        assert result.due_date == date(2026, 2, 15)
        assert result.ai_model == "kimi-2.5"
        assert result.ai_confidence == pytest.approx(0.95, abs=0.01)

    @patch("app.ai_agent.intake_service.call_intake_ai")
    async def test_process_partial_extraction(
        self, mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """Partial extraction: only name + amount, still succeeds."""
        mock_ai.return_value = (FAKE_PARTIAL_RESPONSE, "claude-haiku-4-5")

        client, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(db, test_tenant.id, account.id, from_email=client.email)
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            client_contact_id=client.id,
            status=IntakeStatus.DETECTED,
        )
        db.add(intake)
        await db.commit()

        result = await process_intake(db, intake.id, test_tenant.id)
        assert result is not None
        assert result.status == IntakeStatus.PENDING_REVIEW
        assert result.debtor_name == "Pietersen"
        assert result.debtor_type == "person"
        assert result.principal_amount == Decimal("500.00")
        assert result.invoice_number is None
        assert result.ai_model == "claude-haiku-4-5"

    @patch("app.ai_agent.intake_service.call_intake_ai")
    async def test_process_ai_failure(
        self, mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """AI failure → status becomes FAILED with error message."""
        mock_ai.side_effect = ValueError("All AI providers failed")

        client, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(db, test_tenant.id, account.id, from_email=client.email)
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            client_contact_id=client.id,
            status=IntakeStatus.DETECTED,
        )
        db.add(intake)
        await db.commit()

        result = await process_intake(db, intake.id, test_tenant.id)
        assert result is not None
        assert result.status == IntakeStatus.FAILED
        assert "AI extractie mislukt" in result.error_message

    async def test_process_empty_email_body(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """Email with empty body → FAILED."""
        client, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(
            db,
            test_tenant.id,
            account.id,
            from_email=client.email,
            body="",
        )
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            client_contact_id=client.id,
            status=IntakeStatus.DETECTED,
        )
        db.add(intake)
        await db.commit()

        result = await process_intake(db, intake.id, test_tenant.id)
        assert result is not None
        assert result.status == IntakeStatus.FAILED
        assert "leesbare inhoud" in result.error_message


# ---------------------------------------------------------------------------
# Tests — Approve
# ---------------------------------------------------------------------------


class TestIntakeApprove:
    """Tests for approve_intake() — case + contact creation."""

    @patch("app.ai_agent.intake_service.call_intake_ai")
    async def test_approve_creates_case_and_contact(
        self, mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """Approving creates a debtor contact, an incasso case, and a claim."""
        mock_ai.return_value = (FAKE_INTAKE_RESPONSE, "kimi-2.5")

        client, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(db, test_tenant.id, account.id, from_email=client.email)
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            client_contact_id=client.id,
            status=IntakeStatus.DETECTED,
        )
        db.add(intake)
        await db.commit()

        # Process first
        await process_intake(db, intake.id, test_tenant.id)
        await db.commit()

        # Approve
        result = await approve_intake(
            db, intake.id, test_tenant.id, test_user.id, note="Ziet er goed uit"
        )
        await db.commit()

        assert result is not None
        assert result.status == IntakeStatus.APPROVED
        assert result.created_case_id is not None
        assert result.created_contact_id is not None
        assert result.reviewed_by_id == test_user.id
        assert result.review_note == "Ziet er goed uit"

        # Verify case was created
        case_result = await db.execute(select(Case).where(Case.id == result.created_case_id))
        case = case_result.scalar_one()
        assert case.case_type == "incasso"
        assert case.debtor_type == "b2b"
        assert case.status == "nieuw"
        assert case.client_id == client.id
        assert case.opposing_party_id == result.created_contact_id
        assert case.total_principal == Decimal("2500.00")

        # Verify contact was created
        contact_result = await db.execute(
            select(Contact).where(Contact.id == result.created_contact_id)
        )
        contact = contact_result.scalar_one()
        assert contact.name == "Janssen B.V."
        assert contact.kvk_number == "12345678"
        assert contact.contact_type == "company"

        # Verify claim was created
        claim_result = await db.execute(select(Claim).where(Claim.case_id == case.id))
        claim = claim_result.scalar_one()
        assert claim.principal_amount == Decimal("2500.00")
        assert claim.invoice_number == "F-2026-001"

        # Verify email was linked to case
        email_result = await db.execute(select(SyncedEmail).where(SyncedEmail.id == email.id))
        updated_email = email_result.scalar_one()
        assert updated_email.case_id == case.id

    @patch("app.ai_agent.intake_service.call_intake_ai")
    async def test_approve_person_debtor_type(
        self, mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """Person debtor → case gets debtor_type=b2c."""
        mock_ai.return_value = (FAKE_PARTIAL_RESPONSE, "claude-haiku-4-5")

        client, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(db, test_tenant.id, account.id, from_email=client.email)
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            client_contact_id=client.id,
            status=IntakeStatus.DETECTED,
        )
        db.add(intake)
        await db.commit()

        await process_intake(db, intake.id, test_tenant.id)
        await db.commit()

        result = await approve_intake(db, intake.id, test_tenant.id, test_user.id)
        await db.commit()

        case_result = await db.execute(select(Case).where(Case.id == result.created_case_id))
        case = case_result.scalar_one()
        assert case.debtor_type == "b2c"

    @patch("app.ai_agent.intake_service.call_intake_ai")
    async def test_approve_reuses_existing_debtor_by_kvk(
        self, mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """If debtor contact with same KvK exists, reuse it."""
        mock_ai.return_value = (FAKE_INTAKE_RESPONSE, "kimi-2.5")

        # Pre-create the debtor contact with same KvK
        existing_debtor = Contact(
            tenant_id=test_tenant.id,
            contact_type="company",
            name="Janssen BV (oud)",
            kvk_number="12345678",
        )
        db.add(existing_debtor)

        client, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(db, test_tenant.id, account.id, from_email=client.email)
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            client_contact_id=client.id,
            status=IntakeStatus.DETECTED,
        )
        db.add(intake)
        await db.commit()

        await process_intake(db, intake.id, test_tenant.id)
        await db.commit()

        result = await approve_intake(db, intake.id, test_tenant.id, test_user.id)
        await db.commit()

        # Should reuse the existing contact, not create new
        assert result.created_contact_id == existing_debtor.id


# ---------------------------------------------------------------------------
# Tests — Reject
# ---------------------------------------------------------------------------


class TestIntakeReject:
    """Tests for reject_intake()."""

    @patch("app.ai_agent.intake_service.call_intake_ai")
    async def test_reject_sets_status(
        self, mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """Rejecting sets status to REJECTED with reviewer info."""
        mock_ai.return_value = (FAKE_INTAKE_RESPONSE, "kimi-2.5")

        client, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(db, test_tenant.id, account.id, from_email=client.email)
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            client_contact_id=client.id,
            status=IntakeStatus.DETECTED,
        )
        db.add(intake)
        await db.commit()

        await process_intake(db, intake.id, test_tenant.id)
        await db.commit()

        result = await reject_intake(
            db, intake.id, test_tenant.id, test_user.id, note="Geen incasso-opdracht"
        )
        assert result is not None
        assert result.status == IntakeStatus.REJECTED
        assert result.reviewed_by_id == test_user.id
        assert result.review_note == "Geen incasso-opdracht"
        assert result.created_case_id is None


# ---------------------------------------------------------------------------
# Tests — Query helpers
# ---------------------------------------------------------------------------


class TestIntakeQueries:
    """Tests for query helpers."""

    async def test_pending_count(self, db: AsyncSession, test_tenant: Tenant, test_user: User):
        """pending_intake_count returns correct count."""
        account = await _create_email_account(db, test_tenant.id, test_user.id)

        for i in range(3):
            email = await _create_inbound_email(
                db,
                test_tenant.id,
                account.id,
                from_email=f"client{i}@test.nl",
            )
            intake = IntakeRequest(
                tenant_id=test_tenant.id,
                synced_email_id=email.id,
                status=IntakeStatus.PENDING_REVIEW,
            )
            db.add(intake)

        # One in different status
        email4 = await _create_inbound_email(
            db, test_tenant.id, account.id, from_email="other@test.nl"
        )
        db.add(
            IntakeRequest(
                tenant_id=test_tenant.id,
                synced_email_id=email4.id,
                status=IntakeStatus.APPROVED,
            )
        )
        await db.commit()

        count = await get_pending_intake_count(db, test_tenant.id)
        assert count == 3

    async def test_get_intake_requests_filtered(
        self, db: AsyncSession, test_tenant: Tenant, test_user: User
    ):
        """get_intake_requests filters by status."""
        account = await _create_email_account(db, test_tenant.id, test_user.id)

        for status_val in [IntakeStatus.PENDING_REVIEW, IntakeStatus.APPROVED]:
            email = await _create_inbound_email(
                db,
                test_tenant.id,
                account.id,
                from_email=f"{status_val}@test.nl",
            )
            db.add(
                IntakeRequest(
                    tenant_id=test_tenant.id,
                    synced_email_id=email.id,
                    status=status_val,
                )
            )
        await db.commit()

        # Filter pending
        intakes, total = await get_intake_requests(db, test_tenant.id, status="pending_review")
        assert total == 1
        assert len(intakes) == 1
        assert intakes[0].status == IntakeStatus.PENDING_REVIEW


# ---------------------------------------------------------------------------
# Tests — Multi-tenant isolation
# ---------------------------------------------------------------------------


class TestIntakeMultiTenant:
    """Tests for multi-tenant isolation."""

    async def test_tenant_isolation(
        self,
        db: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
        second_tenant: Tenant,
        second_user: User,
    ):
        """Intakes from one tenant are invisible to another."""
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(
            db, test_tenant.id, account.id, from_email="test@test.nl"
        )
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            status=IntakeStatus.PENDING_REVIEW,
        )
        db.add(intake)
        await db.commit()

        # Tenant 1 sees it
        count = await get_pending_intake_count(db, test_tenant.id)
        assert count == 1

        # Tenant 2 does not
        count = await get_pending_intake_count(db, second_tenant.id)
        assert count == 0

        # Can't fetch by ID from wrong tenant
        result = await get_intake_by_id(db, intake.id, second_tenant.id)
        assert result is None


# ---------------------------------------------------------------------------
# Tests — API Endpoints
# ---------------------------------------------------------------------------


class TestIntakeAPI:
    """Tests for intake API endpoints."""

    async def test_list_intakes(
        self,
        client,
        db: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
        auth_headers: dict,
    ):
        """GET /api/intake returns intake list."""
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(
            db, test_tenant.id, account.id, from_email="test@test.nl"
        )
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            debtor_name="Test Debiteur",
            status=IntakeStatus.PENDING_REVIEW,
        )
        db.add(intake)
        await db.commit()

        response = await client.get("/api/intake", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["debtor_name"] == "Test Debiteur"

    async def test_get_pending_count(
        self,
        client,
        db: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
        auth_headers: dict,
    ):
        """GET /api/intake/pending-count returns correct count."""
        response = await client.get("/api/intake/pending-count", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["count"] == 0

    async def test_approve_endpoint(
        self,
        client,
        db: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
        auth_headers: dict,
    ):
        """POST /api/intake/{id}/approve creates case."""
        # Create client + email + intake in pending_review
        client_contact, _case = await _create_client_with_case(db, test_tenant.id, test_user.id)
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(
            db, test_tenant.id, account.id, from_email=client_contact.email
        )
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            client_contact_id=client_contact.id,
            debtor_name="API Test Debiteur",
            debtor_type="company",
            principal_amount=Decimal("1000.00"),
            due_date=date.today(),
            status=IntakeStatus.PENDING_REVIEW,
        )
        db.add(intake)
        await db.commit()

        response = await client.post(
            f"/api/intake/{intake.id}/approve",
            headers=auth_headers,
            json={"note": "Goedgekeurd"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["created_case_id"] is not None

    async def test_reject_endpoint(
        self,
        client,
        db: AsyncSession,
        test_tenant: Tenant,
        test_user: User,
        auth_headers: dict,
    ):
        """POST /api/intake/{id}/reject sets status."""
        account = await _create_email_account(db, test_tenant.id, test_user.id)
        email = await _create_inbound_email(
            db, test_tenant.id, account.id, from_email="test@test.nl"
        )
        intake = IntakeRequest(
            tenant_id=test_tenant.id,
            synced_email_id=email.id,
            debtor_name="Afwijzen",
            status=IntakeStatus.PENDING_REVIEW,
        )
        db.add(intake)
        await db.commit()

        response = await client.post(
            f"/api/intake/{intake.id}/reject",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
