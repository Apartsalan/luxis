"""Intake service — detect, process, approve, and reject dossier intake requests."""

import json
import logging
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai_agent.intake_models import IntakeRequest, IntakeStatus
from app.ai_agent.intake_prompts import INTAKE_SYSTEM_PROMPT, build_intake_prompt
from app.ai_agent.kimi_client import call_intake_ai
from app.ai_agent.pdf_extract import extract_text_from_pdf
from app.ai_agent.prompts import strip_html
from app.cases.models import Case, CaseActivity
from app.cases.service import generate_case_number
from app.collections.models import Claim
from app.email.synced_email_models import SyncedEmail
from app.relations.models import Contact

logger = logging.getLogger(__name__)

# Path where email attachments are stored
ATTACHMENTS_BASE = "/app/uploads/email_attachments"


# ---------------------------------------------------------------------------
# Detection — find new intake-eligible emails
# ---------------------------------------------------------------------------


async def detect_intake_emails(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> int:
    """Detect inbound emails from known clients that could be intake requests.

    An email qualifies as a potential intake if:
    1. It's inbound
    2. It's not linked to any existing case
    3. The sender matches a known client contact
    4. It hasn't been processed for intake yet
    5. It's not dismissed

    Returns the number of new intake requests created.
    """
    # Already processed email IDs
    already_processed = select(IntakeRequest.synced_email_id).where(
        IntakeRequest.tenant_id == tenant_id
    )

    # Find eligible emails
    result = await db.execute(
        select(SyncedEmail)
        .options(selectinload(SyncedEmail.attachments))
        .where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.direction == "inbound",
            SyncedEmail.case_id.is_(None),  # Not linked to a case
            SyncedEmail.is_dismissed.is_(False),
            SyncedEmail.id.notin_(already_processed),
        )
        .order_by(SyncedEmail.email_date.asc())
        .limit(10)  # Process max 10 per batch
    )
    emails = list(result.scalars().all())

    if not emails:
        return 0

    # Get all client contacts for this tenant (to match sender emails)
    client_result = await db.execute(
        select(Contact)
        .join(Case, Case.client_id == Contact.id)
        .where(
            Contact.tenant_id == tenant_id,
            Contact.email.isnot(None),
        )
        .distinct()
    )
    client_contacts = {c.email.lower(): c for c in client_result.scalars().all() if c.email}

    created = 0
    for email in emails:
        sender = email.from_email.lower()
        if sender not in client_contacts:
            continue

        client_contact = client_contacts[sender]

        intake = IntakeRequest(
            tenant_id=tenant_id,
            synced_email_id=email.id,
            client_contact_id=client_contact.id,
            status=IntakeStatus.DETECTED,
        )
        db.add(intake)
        created += 1

    if created:
        await db.flush()
        logger.info(
            "Intake detection: %d new intake requests for tenant %s",
            created,
            tenant_id,
        )

    return created


# ---------------------------------------------------------------------------
# Processing — AI extraction
# ---------------------------------------------------------------------------


async def process_intake(
    db: AsyncSession,
    intake_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> IntakeRequest | None:
    """Process a detected intake request: extract data from email + PDF via AI.

    Returns the updated IntakeRequest or None if not found.
    """
    result = await db.execute(
        select(IntakeRequest)
        .options(
            selectinload(IntakeRequest.synced_email).selectinload(SyncedEmail.attachments),
        )
        .where(
            IntakeRequest.id == intake_id,
            IntakeRequest.tenant_id == tenant_id,
            IntakeRequest.status == IntakeStatus.DETECTED,
        )
    )
    intake = result.scalar_one_or_none()
    if not intake:
        return None

    intake.status = IntakeStatus.PROCESSING
    await db.flush()

    email = intake.synced_email
    if not email:
        intake.status = IntakeStatus.FAILED
        intake.error_message = "Email niet gevonden"
        await db.flush()
        return intake

    # Get email body
    body = email.body_text or strip_html(email.body_html) or ""
    if not body.strip():
        intake.status = IntakeStatus.FAILED
        intake.error_message = "Email heeft geen leesbare inhoud"
        await db.flush()
        return intake

    # Extract text from PDF attachments
    pdf_text = None
    if email.attachments:
        for att in email.attachments:
            if att.content_type == "application/pdf" or att.filename.lower().endswith(".pdf"):
                file_path = f"{ATTACHMENTS_BASE}/{tenant_id}/{email.id}/{att.stored_filename}"
                extracted = extract_text_from_pdf(file_path)
                if extracted:
                    pdf_text = extracted
                    intake.has_pdf_data = True
                    break  # Use first PDF

    # Build prompt
    user_message = build_intake_prompt(
        sender_name=email.from_name or email.from_email,
        sender_email=email.from_email,
        email_subject=email.subject,
        email_date=email.email_date.strftime("%d-%m-%Y %H:%M"),
        email_body=body,
        pdf_text=pdf_text,
    )

    # Call AI
    try:
        ai_result, model_name = await call_intake_ai(INTAKE_SYSTEM_PROMPT, user_message)
    except Exception as e:
        logger.error("Intake AI failed for %s: %s", intake_id, e)
        intake.status = IntakeStatus.FAILED
        intake.error_message = f"AI extractie mislukt: {e}"
        await db.flush()
        return intake

    # Apply extracted data
    intake.ai_model = model_name
    intake.raw_extraction = json.dumps(ai_result, ensure_ascii=False)
    intake.ai_confidence = min(max(float(ai_result.get("confidence", 0.5)), 0.0), 1.0)
    intake.ai_reasoning = ai_result.get("reasoning", "")

    intake.debtor_name = ai_result.get("debtor_name")
    intake.debtor_email = ai_result.get("debtor_email")
    intake.debtor_kvk = ai_result.get("debtor_kvk")
    intake.debtor_address = ai_result.get("debtor_address")
    intake.debtor_city = ai_result.get("debtor_city")
    intake.debtor_postcode = ai_result.get("debtor_postcode")
    intake.debtor_type = ai_result.get("debtor_type", "company")
    if intake.debtor_type not in ("company", "person"):
        intake.debtor_type = "company"

    intake.invoice_number = ai_result.get("invoice_number")
    intake.description = ai_result.get("description")

    # Parse dates safely
    intake.invoice_date = _parse_date(ai_result.get("invoice_date"))
    intake.due_date = _parse_date(ai_result.get("due_date"))

    # Parse amount safely (Decimal precision)
    raw_amount = ai_result.get("principal_amount")
    if raw_amount is not None:
        try:
            intake.principal_amount = Decimal(str(raw_amount)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            intake.principal_amount = None

    intake.status = IntakeStatus.PENDING_REVIEW
    await db.flush()

    logger.info(
        "Intake processed %s → debtor=%s amount=%s confidence=%.0f%% model=%s",
        intake_id,
        intake.debtor_name,
        intake.principal_amount,
        (intake.ai_confidence or 0) * 100,
        model_name,
    )
    return intake


async def process_detected_intakes(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> int:
    """Process all detected (unprocessed) intake requests for a tenant.

    Returns the number successfully processed.
    """
    result = await db.execute(
        select(IntakeRequest.id)
        .where(
            IntakeRequest.tenant_id == tenant_id,
            IntakeRequest.status == IntakeStatus.DETECTED,
        )
        .order_by(IntakeRequest.created_at.asc())
        .limit(5)  # Process max 5 per batch to limit API costs
    )
    intake_ids = list(result.scalars().all())

    processed = 0
    for intake_id in intake_ids:
        intake = await process_intake(db, intake_id, tenant_id)
        if intake and intake.status == IntakeStatus.PENDING_REVIEW:
            processed += 1

    return processed


# ---------------------------------------------------------------------------
# Approve — create case + contact from extracted data
# ---------------------------------------------------------------------------


async def approve_intake(
    db: AsyncSession,
    intake_id: uuid.UUID,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    note: str | None = None,
) -> IntakeRequest | None:
    """Approve an intake request: create debtor contact + incasso case.

    Returns the updated IntakeRequest with created_case_id and created_contact_id.
    """
    result = await db.execute(
        select(IntakeRequest)
        .options(selectinload(IntakeRequest.synced_email))
        .where(
            IntakeRequest.id == intake_id,
            IntakeRequest.tenant_id == tenant_id,
            IntakeRequest.status == IntakeStatus.PENDING_REVIEW,
        )
    )
    intake = result.scalar_one_or_none()
    if not intake:
        return None

    # Validate minimum required data
    if not intake.debtor_name:
        intake.error_message = "Debiteurnaam is verplicht"
        return intake

    # 1. Create debtor contact (or find existing by KvK/email)
    debtor_contact = await _find_or_create_debtor(db, tenant_id, intake)
    intake.created_contact_id = debtor_contact.id

    # 2. Create incasso case
    case_number = await generate_case_number(db, tenant_id)

    # Determine debtor_type for case
    debtor_type = "b2b" if intake.debtor_type == "company" else "b2c"

    case = Case(
        tenant_id=tenant_id,
        case_number=case_number,
        case_type="incasso",
        debtor_type=debtor_type,
        status="nieuw",
        description=intake.description or f"Incassodossier {intake.debtor_name}",
        client_id=intake.client_contact_id,
        opposing_party_id=debtor_contact.id,
        assigned_to_id=user_id,
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()

    # 3. Create claim if we have amount + due date
    if intake.principal_amount and intake.principal_amount > 0:
        claim_desc = f"Factuur {intake.invoice_number or 'onbekend'}"
        if intake.invoice_date:
            claim_desc += f" dd. {intake.invoice_date.strftime('%d-%m-%Y')}"

        claim = Claim(
            tenant_id=tenant_id,
            case_id=case.id,
            description=claim_desc,
            principal_amount=intake.principal_amount,
            default_date=intake.due_date or date.today(),
            invoice_number=intake.invoice_number,
            invoice_date=intake.invoice_date,
        )
        db.add(claim)

        # Update case total_principal
        case.total_principal = intake.principal_amount

    # 4. Link the source email to the new case
    if intake.synced_email:
        intake.synced_email.case_id = case.id

    # 5. Log activity
    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case.id,
        user_id=user_id,
        activity_type="ai_action",
        title="Dossier aangemaakt via AI Intake",
        description=(
            f"Automatisch aangemaakt op basis van email.\n"
            f"Debiteur: {intake.debtor_name}\n"
            f"Bedrag: EUR {intake.principal_amount or '?'}\n"
            f"Model: {intake.ai_model}"
        ),
    )
    db.add(activity)

    # 6. Update intake status
    intake.created_case_id = case.id
    intake.status = IntakeStatus.APPROVED
    intake.reviewed_by_id = user_id
    intake.reviewed_at = datetime.now(UTC)
    intake.review_note = note

    await db.flush()

    logger.info(
        "Intake %s approved → case %s, contact %s",
        intake_id,
        case_number,
        debtor_contact.name,
    )
    return intake


# ---------------------------------------------------------------------------
# Reject
# ---------------------------------------------------------------------------


async def reject_intake(
    db: AsyncSession,
    intake_id: uuid.UUID,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    note: str | None = None,
) -> IntakeRequest | None:
    """Reject an intake request."""
    result = await db.execute(
        select(IntakeRequest).where(
            IntakeRequest.id == intake_id,
            IntakeRequest.tenant_id == tenant_id,
            IntakeRequest.status == IntakeStatus.PENDING_REVIEW,
        )
    )
    intake = result.scalar_one_or_none()
    if not intake:
        return None

    intake.status = IntakeStatus.REJECTED
    intake.reviewed_by_id = user_id
    intake.reviewed_at = datetime.now(UTC)
    intake.review_note = note

    await db.flush()
    return intake


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


async def get_intake_requests(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[IntakeRequest], int]:
    """Get intake requests with optional status filter, paginated."""
    query = (
        select(IntakeRequest)
        .options(
            selectinload(IntakeRequest.synced_email),
            selectinload(IntakeRequest.client_contact),
            selectinload(IntakeRequest.reviewed_by),
            selectinload(IntakeRequest.created_case),
            selectinload(IntakeRequest.created_contact),
        )
        .where(IntakeRequest.tenant_id == tenant_id)
    )
    count_query = (
        select(func.count()).select_from(IntakeRequest).where(IntakeRequest.tenant_id == tenant_id)
    )

    if status:
        query = query.where(IntakeRequest.status == status)
        count_query = count_query.where(IntakeRequest.status == status)

    query = (
        query.order_by(IntakeRequest.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    result = await db.execute(query)
    intakes = list(result.scalars().all())
    total = (await db.execute(count_query)).scalar() or 0

    return intakes, total


async def get_intake_by_id(
    db: AsyncSession,
    intake_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> IntakeRequest | None:
    """Get a single intake request by ID."""
    result = await db.execute(
        select(IntakeRequest)
        .options(
            selectinload(IntakeRequest.synced_email),
            selectinload(IntakeRequest.client_contact),
            selectinload(IntakeRequest.reviewed_by),
            selectinload(IntakeRequest.created_case),
            selectinload(IntakeRequest.created_contact),
        )
        .where(
            IntakeRequest.id == intake_id,
            IntakeRequest.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_pending_intake_count(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> int:
    """Get number of pending review intake requests."""
    result = await db.execute(
        select(func.count())
        .select_from(IntakeRequest)
        .where(
            IntakeRequest.tenant_id == tenant_id,
            IntakeRequest.status == IntakeStatus.PENDING_REVIEW,
        )
    )
    return result.scalar() or 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _find_or_create_debtor(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    intake: IntakeRequest,
) -> Contact:
    """Find existing debtor contact by KvK or email, or create a new one."""
    # Try to find by KvK number first (most reliable for companies)
    if intake.debtor_kvk:
        result = await db.execute(
            select(Contact).where(
                Contact.tenant_id == tenant_id,
                Contact.kvk_number == intake.debtor_kvk,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    # Try to find by email
    if intake.debtor_email:
        result = await db.execute(
            select(Contact).where(
                Contact.tenant_id == tenant_id,
                Contact.email == intake.debtor_email,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    # Create new contact
    contact_type = intake.debtor_type or "company"
    contact = Contact(
        tenant_id=tenant_id,
        contact_type=contact_type,
        name=intake.debtor_name or "Onbekend",
        email=intake.debtor_email,
        kvk_number=intake.debtor_kvk,
        visit_address=intake.debtor_address,
        visit_city=intake.debtor_city,
        visit_postcode=intake.debtor_postcode,
    )
    db.add(contact)
    await db.flush()
    await db.refresh(contact)

    logger.info(
        "Created debtor contact: %s (%s) for tenant %s",
        contact.name,
        contact.id,
        tenant_id,
    )
    return contact


def _parse_date(value: str | None) -> date | None:
    """Parse a date string in YYYY-MM-DD format. Returns None on failure."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None
