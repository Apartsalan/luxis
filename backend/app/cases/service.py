"""Cases module service — Business logic for cases, parties, and activities."""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cases.models import Case, CaseActivity, CaseParty
from app.workflow.models import WorkflowTask
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


# ── Task Templates per Case Type (G10) ────────────────────────────────────────

INCASSO_TASKS = [
    {"title": "Dossier controleren en compleet maken", "task_type": "manual_review", "days": 1,
     "description": "Controleer of alle gegevens compleet zijn: facturen, contactgegevens wederpartij, renteberekening."},
    {"title": "Herinnering versturen", "task_type": "send_letter", "days": 3,
     "description": "Stuur een herinnering naar de debiteur."},
    {"title": "14-dagenbrief versturen (B2C)", "task_type": "send_letter", "days": 7,
     "description": "Wettelijk verplichte 14-dagenbrief voor consumenten (B2C)."},
    {"title": "Controleer betaling na herinnering", "task_type": "check_payment", "days": 14,
     "description": "Controleer of er een betaling is ontvangen na de herinnering."},
    {"title": "Sommatie versturen", "task_type": "send_letter", "days": 21,
     "description": "Stuur een aanmaning/sommatie naar de debiteur."},
    {"title": "Controleer betaling na sommatie", "task_type": "check_payment", "days": 35,
     "description": "Controleer of er een betaling is ontvangen na de sommatie."},
    {"title": "Beoordeel dagvaarding", "task_type": "manual_review", "days": 42,
     "description": "Beoordeel of dagvaarding nodig is. Neem contact op met de client."},
    {"title": "Verjaringstermijn controleren", "task_type": "set_deadline", "days": 180,
     "description": "Controleer de verjaringstermijn en onderneem actie indien nodig."},
]

ADVIES_TASKS = [
    {"title": "Dossier controleren en compleet maken", "task_type": "manual_review", "days": 1,
     "description": "Controleer of alle stukken en gegevens compleet zijn."},
    {"title": "Juridisch onderzoek", "task_type": "manual_review", "days": 7,
     "description": "Voer juridisch onderzoek uit en bereid advies voor."},
    {"title": "Concept advies opstellen", "task_type": "generate_document", "days": 14,
     "description": "Stel een concept adviesbrief op voor de client."},
    {"title": "Advies versturen aan client", "task_type": "send_letter", "days": 21,
     "description": "Verstuur het definitieve advies naar de client."},
]

INSOLVENTIE_TASKS = [
    {"title": "Dossier controleren en compleet maken", "task_type": "manual_review", "days": 1,
     "description": "Controleer of alle stukken compleet zijn: jaarrekeningen, crediteurenlijst, etc."},
    {"title": "Beoordeel faillissementsaanvraag of surseance", "task_type": "manual_review", "days": 3,
     "description": "Beoordeel welke procedure het meest geschikt is."},
    {"title": "Verzoekschrift opstellen", "task_type": "generate_document", "days": 14,
     "description": "Stel het verzoekschrift op voor de rechtbank."},
    {"title": "Indienen bij rechtbank", "task_type": "manual_review", "days": 21,
     "description": "Dien het verzoekschrift in bij de bevoegde rechtbank."},
]

OVERIG_TASKS = [
    {"title": "Dossier controleren en compleet maken", "task_type": "manual_review", "days": 1,
     "description": "Controleer of alle gegevens en stukken compleet zijn."},
    {"title": "Plan van aanpak bepalen", "task_type": "manual_review", "days": 3,
     "description": "Bepaal de strategie en het plan van aanpak voor deze zaak."},
]

TASK_TEMPLATES: dict[str, list[dict]] = {
    "incasso": INCASSO_TASKS,
    "advies": ADVIES_TASKS,
    "insolventie": INSOLVENTIE_TASKS,
    "overig": OVERIG_TASKS,
}


async def _create_initial_tasks(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    user_id: uuid.UUID,
) -> list[WorkflowTask]:
    """Create initial task templates for a newly created case based on case_type."""
    templates = TASK_TEMPLATES.get(case.case_type, OVERIG_TASKS)
    created: list[WorkflowTask] = []

    for tpl in templates:
        task = WorkflowTask(
            tenant_id=tenant_id,
            case_id=case.id,
            assigned_to_id=case.assigned_to_id or user_id,
            task_type=tpl["task_type"],
            title=tpl["title"],
            description=tpl["description"],
            due_date=case.date_opened + timedelta(days=tpl["days"]),
            status="pending",
            auto_execute=False,
        )
        db.add(task)
        created.append(task)

    if created:
        await db.flush()

    return created


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
    client_id: uuid.UUID | None = None,
    assigned_to_id: uuid.UUID | None = None,
    date_from: "date | None" = None,
    date_to: "date | None" = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    is_active: bool = True,
) -> tuple[list[Case], int]:
    """List cases with optional filtering and pagination."""
    from app.relations.models import Contact

    query = select(Case).where(
        Case.tenant_id == tenant_id,
        Case.is_active == is_active,  # noqa: E712
    )

    if case_type:
        query = query.where(Case.case_type == case_type)

    if status:
        query = query.where(Case.status == status)

    if client_id:
        # Filter cases where this contact is client, opposing party, OR a case party
        query = query.where(
            or_(
                Case.client_id == client_id,
                Case.opposing_party_id == client_id,
                Case.parties.any(CaseParty.contact_id == client_id),
            )
        )

    if assigned_to_id:
        query = query.where(Case.assigned_to_id == assigned_to_id)

    if date_from:
        query = query.where(Case.date_opened >= date_from)

    if date_to:
        query = query.where(Case.date_opened <= date_to)

    if min_amount is not None:
        query = query.where(Case.total_principal >= min_amount)

    if max_amount is not None:
        query = query.where(Case.total_principal <= max_amount)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Case.case_number.ilike(search_term),
                Case.description.ilike(search_term),
                Case.reference.ilike(search_term),
                Case.client.has(Contact.name.ilike(search_term)),
                Case.opposing_party.has(Contact.name.ilike(search_term)),
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
        select(Case)
        .where(
            Case.id == case_id,
            Case.tenant_id == tenant_id,
        )
        .options(
            selectinload(Case.parties).selectinload(CaseParty.contact),
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
        court_case_number=data.court_case_number,
        court_name=data.court_name,
        judge_name=data.judge_name,
        chamber=data.chamber,
        procedure_type=data.procedure_type,
        procedure_phase=data.procedure_phase,
        interest_type=data.interest_type,
        contractual_rate=data.contractual_rate,
        contractual_compound=data.contractual_compound,
        client_id=data.client_id,
        opposing_party_id=data.opposing_party_id,
        billing_contact_id=data.billing_contact_id,
        assigned_to_id=data.assigned_to_id or user_id,
        date_opened=data.date_opened,
        budget=data.budget,
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

    # G10: Create initial task templates based on case type
    await _create_initial_tasks(db, tenant_id, case, user_id)

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
    """Update the status of a case using the database-driven workflow engine.

    Validates transitions against WorkflowTransition table and enforces
    legal constraints (14-dagenbrief, verjaring).
    After transition, triggers automation hooks (task creation + audit trail).
    """
    from app.workflow.hooks import on_status_change
    from app.workflow.service import execute_transition

    case = await get_case(db, tenant_id, case_id)
    old_status = case.status

    # Use the workflow engine for validation + execution
    case, validation = await execute_transition(
        db, tenant_id, case, data.new_status, user_id, note=data.note
    )

    # Trigger automation hooks (task creation + audit trail)
    await on_status_change(
        db, tenant_id, case, old_status, data.new_status, user_id
    )

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


# ── Conflict Check ───────────────────────────────────────────────────────


async def conflict_check(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    role: str,
) -> list[dict]:
    """Check if a contact has conflicting roles in existing cases.

    When adding a contact as 'client', check if they appear as opposing_party
    in any active case (and vice versa). Returns a list of conflicting cases.

    Args:
        contact_id: The contact to check.
        role: The intended role — 'client' or 'opposing_party'.
    """
    if role == "client":
        # Contact is being added as client — check if they're opposing party somewhere
        query = select(Case).where(
            Case.tenant_id == tenant_id,
            Case.is_active == True,  # noqa: E712
            Case.opposing_party_id == contact_id,
        )
    elif role == "opposing_party":
        # Contact is being added as opposing party — check if they're client somewhere
        query = select(Case).where(
            Case.tenant_id == tenant_id,
            Case.is_active == True,  # noqa: E712
            Case.client_id == contact_id,
        )
    else:
        return []

    result = await db.execute(query)
    cases = list(result.scalars().all())

    return [
        {
            "case_id": str(c.id),
            "case_number": c.case_number,
            "case_type": c.case_type,
            "status": c.status,
            "role_in_case": "wederpartij" if role == "client" else "client",
            "client_name": c.client.name if c.client else None,
            "opposing_party_name": c.opposing_party.name if c.opposing_party else None,
        }
        for c in cases
    ]


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

    # Re-query with explicit eager loading so contact is available for serialisation
    result = await db.execute(
        select(CaseParty)
        .where(CaseParty.id == party.id)
        .options(selectinload(CaseParty.contact))
    )
    return result.scalar_one()


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
