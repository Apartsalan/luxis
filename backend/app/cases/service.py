"""Cases module service — Business logic for cases, parties, and activities."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseActivity, CaseParty
from app.cases.schemas import (
    CASE_STATUSES,
    CASE_TYPES,
    DEBTOR_TYPES,
    INTEREST_TYPES,
    STATUS_TRANSITIONS,
    CaseActivityCreate,
    CaseCreate,
    CasePartyCreate,
    CaseStatusUpdate,
    CaseUpdate,
)
from app.shared.exceptions import BadRequestError, ConflictError, NotFoundError

# ── Case Number Generation ───────────────────────────────────────────────────


async def generate_case_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate the next case number for a tenant.

    Format: YYYY-NNNNN (e.g. 2026-00001)
    """
    current_year = datetime.now(UTC).year
    prefix = f"{current_year}-"

    # Find the highest case number for this tenant and year
    result = await db.execute(
        select(func.max(Case.case_number)).where(
            Case.tenant_id == tenant_id,
            Case.case_number.like(f"{prefix}%"),
        )
    )
    last_number = result.scalar_one_or_none()

    if last_number:
        # Extract the sequence part and increment
        seq = int(last_number.split("-")[1]) + 1
    else:
        seq = 1

    return f"{prefix}{seq:05d}"


# ── Case CRUD ────────────────────────────────────────────────────────────────


async def list_cases(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    page: int = 1,
    per_page: int = 20,
    case_type: str | None = None,
    status: str | None = None,
    search: str | None = None,
    is_active: bool = True,
) -> tuple[list[Case], int]:
    """List cases with optional filtering and pagination."""
    query = select(Case).where(
        Case.tenant_id == tenant_id,
        Case.is_active == is_active,  # noqa: E712
    )

    if case_type:
        query = query.where(Case.case_type == case_type)

    if status:
        query = query.where(Case.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Case.case_number.ilike(search_term),
                Case.description.ilike(search_term),
                Case.reference.ilike(search_term),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Apply pagination and ordering
    query = (
        query.order_by(Case.date_opened.desc(), Case.case_number.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    result = await db.execute(query)
    cases = list(result.scalars().all())

    return cases, total


async def get_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> Case:
    """Get a single case by ID. Raises NotFoundError if not found."""
    result = await db.execute(
        select(Case).where(
            Case.id == case_id,
            Case.tenant_id == tenant_id,
        )
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise NotFoundError("Zaak niet gevonden")
    return case


async def create_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: CaseCreate,
) -> Case:
    """Create a new case with auto-generated case number."""
    # Validate case_type
    if data.case_type not in CASE_TYPES:
        raise BadRequestError(
            f"Ongeldig zaaktype: {data.case_type}. "
            f"Kies uit: {', '.join(CASE_TYPES)}"
        )

    # Validate debtor_type
    if data.debtor_type not in DEBTOR_TYPES:
        raise BadRequestError(
            f"Ongeldig debiteurtype: {data.debtor_type}. "
            f"Kies uit: {', '.join(DEBTOR_TYPES)}"
        )

    # Validate interest_type
    if data.interest_type not in INTEREST_TYPES:
        raise BadRequestError(
            f"Ongeldig rentetype: {data.interest_type}. "
            f"Kies uit: {', '.join(INTEREST_TYPES)}"
        )

    # Contractual rate required for contractual interest
    if data.interest_type == "contractual" and data.contractual_rate is None:
        raise BadRequestError(
            "Contractuele rente vereist een tarief (contractual_rate)"
        )

    # Generate case number
    case_number = await generate_case_number(db, tenant_id)

    case = Case(
        tenant_id=tenant_id,
        case_number=case_number,
        case_type=data.case_type,
        debtor_type=data.debtor_type,
        status="nieuw",
        description=data.description,
        reference=data.reference,
        interest_type=data.interest_type,
        contractual_rate=data.contractual_rate,
        contractual_compound=data.contractual_compound,
        client_id=data.client_id,
        opposing_party_id=data.opposing_party_id,
        assigned_to_id=data.assigned_to_id or user_id,
        date_opened=data.date_opened,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)

    # Log activity
    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case.id,
        user_id=user_id,
        activity_type="status_change",
        title="Zaak aangemaakt",
        description=f"Zaak {case_number} aangemaakt als {data.case_type}",
        new_status="nieuw",
    )
    db.add(activity)
    await db.flush()

    return case


async def update_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    data: CaseUpdate,
) -> Case:
    """Update case details (not status — use update_case_status for that)."""
    case = await get_case(db, tenant_id, case_id)

    update_data = data.model_dump(exclude_unset=True)

    # Validate interest_type if being changed
    if "interest_type" in update_data and update_data["interest_type"] not in INTEREST_TYPES:
        raise BadRequestError(
            f"Ongeldig rentetype: {update_data['interest_type']}. "
            f"Kies uit: {', '.join(INTEREST_TYPES)}"
        )

    for field, value in update_data.items():
        setattr(case, field, value)

    await db.flush()
    await db.refresh(case)
    return case


async def update_case_status(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    user_id: uuid.UUID,
    data: CaseStatusUpdate,
) -> Case:
    """Update the status of a case, following the allowed status workflow."""
    case = await get_case(db, tenant_id, case_id)

    # Validate new status
    if data.new_status not in CASE_STATUSES:
        raise BadRequestError(
            f"Ongeldige status: {data.new_status}. "
            f"Kies uit: {', '.join(CASE_STATUSES)}"
        )

    # Validate transition
    allowed = STATUS_TRANSITIONS.get(case.status, [])
    if data.new_status not in allowed:
        raise ConflictError(
            f"Status kan niet van '{case.status}' naar '{data.new_status}'. "
            f"Toegestane overgangen: {', '.join(allowed) if allowed else 'geen (eindstatus)'}"
        )

    old_status = case.status
    case.status = data.new_status

    # Set date_closed if moving to terminal state
    if data.new_status in ("betaald", "afgesloten"):
        case.date_closed = date.today()

    await db.flush()

    # Log activity
    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case.id,
        user_id=user_id,
        activity_type="status_change",
        title=f"Status gewijzigd: {old_status} → {data.new_status}",
        description=data.note,
        old_status=old_status,
        new_status=data.new_status,
    )
    db.add(activity)
    await db.flush()

    await db.refresh(case)
    return case


async def delete_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> None:
    """Soft-delete a case by setting is_active=False."""
    case = await get_case(db, tenant_id, case_id)
    case.is_active = False
    await db.flush()


# ── Case Parties ─────────────────────────────────────────────────────────────


async def add_case_party(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    data: CasePartyCreate,
) -> CaseParty:
    """Add a party (deurwaarder, rechtbank, etc.) to a case."""
    # Verify the case exists
    await get_case(db, tenant_id, case_id)

    party = CaseParty(
        tenant_id=tenant_id,
        case_id=case_id,
        contact_id=data.contact_id,
        role=data.role,
    )
    db.add(party)
    await db.flush()
    await db.refresh(party)
    return party


async def remove_case_party(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    party_id: uuid.UUID,
) -> None:
    """Remove a party from a case."""
    result = await db.execute(
        select(CaseParty).where(
            CaseParty.id == party_id,
            CaseParty.tenant_id == tenant_id,
        )
    )
    party = result.scalar_one_or_none()
    if party is None:
        raise NotFoundError("Partij niet gevonden")
    await db.delete(party)
    await db.flush()


# ── Case Activities ──────────────────────────────────────────────────────────


async def add_activity(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    user_id: uuid.UUID,
    data: CaseActivityCreate,
) -> CaseActivity:
    """Add an activity entry to a case."""
    # Verify the case exists
    await get_case(db, tenant_id, case_id)

    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case_id,
        user_id=user_id,
        activity_type=data.activity_type,
        title=data.title,
        description=data.description,
    )
    db.add(activity)
    await db.flush()
    await db.refresh(activity)
    return activity


async def list_activities(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[CaseActivity], int]:
    """List activities for a case, newest first."""
    # Verify the case exists
    await get_case(db, tenant_id, case_id)

    query = select(CaseActivity).where(
        CaseActivity.case_id == case_id,
        CaseActivity.tenant_id == tenant_id,
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = (
        query.order_by(CaseActivity.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    result = await db.execute(query)
    activities = list(result.scalars().all())

    return activities, total
