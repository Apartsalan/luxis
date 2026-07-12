"""Workflow service — tasks, scheduling, verjaring, and calendar aggregation."""

import uuid
from datetime import UTC, date, datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.cases.schemas import TERMINAL_STATUSES
from app.relations.kyc_models import KycVerification
from app.shared.exceptions import BadRequestError, NotFoundError
from app.workflow.models import WorkflowTask
from app.workflow.schemas import (
    LEGAL_CONSTRAINTS,
    TASK_STATUSES,
    TASK_TYPES,
    WorkflowTaskCreate,
    WorkflowTaskUpdate,
    effective_task_status,
)

# ── WorkflowTask CRUD ──────────────────────────────────────────────────────


async def list_tasks(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    case_id: uuid.UUID | None = None,
    status: str | None = None,
    assigned_to_id: uuid.UUID | None = None,
    include_unassigned: bool = False,
) -> list[WorkflowTask]:
    """List workflow tasks with optional filters.

    `include_unassigned` (alleen zinvol samen met `assigned_to_id`): naast de
    taken van die gebruiker óók eigenaarloze tenant-taken meenemen. A1 — de
    verjaring-monitor maakt taken zonder eigenaar aan; zonder dit blijven ze
    onzichtbaar in Mijn Taken.
    """
    query = select(WorkflowTask).where(
        WorkflowTask.tenant_id == tenant_id,
        WorkflowTask.is_active.is_(True),
    )
    if case_id:
        query = query.where(WorkflowTask.case_id == case_id)
    if status:
        query = query.where(WorkflowTask.status == status)
    if assigned_to_id:
        if include_unassigned:
            query = query.where(
                or_(
                    WorkflowTask.assigned_to_id == assigned_to_id,
                    WorkflowTask.assigned_to_id.is_(None),
                )
            )
        else:
            query = query.where(WorkflowTask.assigned_to_id == assigned_to_id)
    query = query.order_by(WorkflowTask.due_date, WorkflowTask.created_at)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_task(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    task_id: uuid.UUID,
) -> WorkflowTask:
    """Get a workflow task by ID."""
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.id == task_id,
            WorkflowTask.tenant_id == tenant_id,
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise NotFoundError("Taak niet gevonden")
    return task


async def create_task(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: WorkflowTaskCreate,
) -> WorkflowTask:
    """Create a workflow task manually."""
    if data.task_type not in TASK_TYPES:
        raise BadRequestError(
            f"Ongeldig taaktype: {data.task_type}. Kies uit: {', '.join(TASK_TYPES)}"
        )
    task = WorkflowTask(tenant_id=tenant_id, **data.model_dump())
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def update_task(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    task_id: uuid.UUID,
    data: WorkflowTaskUpdate,
) -> WorkflowTask:
    """Update a workflow task (status, assignee, etc.)."""
    task = await get_task(db, tenant_id, task_id)
    update_data = data.model_dump(exclude_unset=True)

    if "status" in update_data:
        new_status = update_data["status"]
        if new_status not in TASK_STATUSES:
            raise BadRequestError(
                f"Ongeldige taakstatus: {new_status}. Kies uit: {', '.join(TASK_STATUSES)}"
            )
        if new_status == "completed":
            task.completed_at = datetime.now(UTC)
        elif new_status in ("pending", "due"):
            task.completed_at = None

    for field, value in update_data.items():
        setattr(task, field, value)

    await db.flush()
    await db.refresh(task)

    # G9: If task is recurring and just completed, create next occurrence
    if (
        task.status == "completed"
        and task.recurrence
        and task.recurrence in ("daily", "weekly", "monthly", "quarterly", "yearly")
    ):
        await _create_next_recurring_task(db, task)

    return task


async def delete_task(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    task_id: uuid.UUID,
) -> None:
    """Soft-delete a workflow task."""
    task = await get_task(db, tenant_id, task_id)
    task.is_active = False
    await db.flush()


async def skip_open_tasks_for_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> int:
    """Mark a case's still-open tasks as 'skipped'.

    Called when a case is archived (soft-deleted) so its open tasks stop
    surfacing as overdue/upcoming and on the agenda (AUDIT-H24). Returns the
    number of tasks that were skipped.
    """
    result = await db.execute(
        update(WorkflowTask)
        .where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.case_id == case_id,
            WorkflowTask.is_active.is_(True),
            WorkflowTask.status.notin_(["completed", "skipped"]),
        )
        .values(status="skipped")
    )
    await db.flush()
    return result.rowcount


# ── G9: Recurring task helper ────────────────────────────────────────────────


_RECURRENCE_DELTAS = {
    "daily": relativedelta(days=1),
    "weekly": relativedelta(weeks=1),
    "monthly": relativedelta(months=1),
    "quarterly": relativedelta(months=3),
    "yearly": relativedelta(years=1),
}


async def _create_next_recurring_task(
    db: AsyncSession,
    completed_task: WorkflowTask,
) -> WorkflowTask | None:
    """Create the next occurrence of a recurring task.

    Called after a recurring task is marked as completed.
    Returns the new task, or None if recurrence has ended.
    """
    delta = _RECURRENCE_DELTAS.get(completed_task.recurrence)  # type: ignore[arg-type]
    if delta is None:
        return None

    next_due = completed_task.due_date + delta

    # Check if past recurrence end date
    if completed_task.recurrence_end_date and next_due > completed_task.recurrence_end_date:
        return None

    next_task = WorkflowTask(
        tenant_id=completed_task.tenant_id,
        case_id=completed_task.case_id,
        assigned_to_id=completed_task.assigned_to_id,
        task_type=completed_task.task_type,
        title=completed_task.title,
        description=completed_task.description,
        due_date=next_due,
        status="pending" if next_due > date.today() else "due",
        auto_execute=completed_task.auto_execute,
        action_config=completed_task.action_config,
        recurrence=completed_task.recurrence,
        recurrence_end_date=completed_task.recurrence_end_date,
        parent_task_id=completed_task.id,
    )
    db.add(next_task)
    await db.flush()
    await db.refresh(next_task)
    return next_task


# ── Scheduler helpers ───────────────────────────────────────────────────────


async def update_task_statuses(db: AsyncSession) -> dict:
    """Daily job: mark pending tasks as 'due' or 'overdue' based on due_date.

    Returns counts of updated tasks.
    """
    today = date.today()
    counts = {"marked_due": 0, "marked_overdue": 0}

    # Mark pending tasks that are now due
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.status == "pending",
            WorkflowTask.due_date <= today,
            WorkflowTask.is_active.is_(True),
        )
    )
    for task in result.scalars().all():
        task.status = "due"
        counts["marked_due"] += 1

    # Mark due tasks that are overdue (due_date < today)
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.status == "due",
            WorkflowTask.due_date < today,
            WorkflowTask.is_active.is_(True),
        )
    )
    for task in result.scalars().all():
        task.status = "overdue"
        counts["marked_overdue"] += 1

    await db.flush()
    return counts


async def check_verjaring(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[dict]:
    """Check all active cases for approaching verjaring (5 years).

    Returns list of warnings for cases within 90 days of verjaring.
    """
    today = date.today()
    verjaring_years = LEGAL_CONSTRAINTS["verjaring_years"]

    # Audit #83: verjaring (art. 3:307 BW) loopt vanaf de opeisbaarheid van de
    # vordering — in Luxis benaderd door de oudste claims.default_date — en
    # niet vanaf het moment dat het dossier bij het kantoor werd geopend.
    # date_opened blijft de fallback voor dossiers zonder vorderingen.
    from app.collections.models import Claim

    oldest_claim = (
        select(Claim.case_id, func.min(Claim.default_date).label("oldest_default"))
        .where(Claim.tenant_id == tenant_id, Claim.is_active.is_(True))
        .group_by(Claim.case_id)
        .subquery()
    )

    # B2/S199 — date_closed is geen betrouwbaar "afgesloten"-signaal:
    # geïmporteerde, heropende zaken kunnen een oude sluitdatum dragen. De vaste
    # terminale zaakstatussen zijn daarom het enige uitsluitcriterium.

    result = await db.execute(
        select(Case, oldest_claim.c.oldest_default)
        .outerjoin(oldest_claim, oldest_claim.c.case_id == Case.id)
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.status.notin_(TERMINAL_STATUSES),
        )
    )

    warnings = []
    for case, oldest_default in result.all():
        basis_date = oldest_default or case.date_opened
        verjaring_date = basis_date + relativedelta(years=verjaring_years)
        days_remaining = (verjaring_date - today).days
        if days_remaining > 90:
            continue  # nog ruim buiten de waarschuwingstermijn
        warnings.append(
            {
                "case_id": str(case.id),
                "case_number": case.case_number,
                "date_opened": case.date_opened.isoformat(),
                "basis_date": basis_date.isoformat(),
                "verjaring_date": verjaring_date.isoformat(),
                "days_remaining": days_remaining,
                "is_expired": days_remaining <= 0,
            }
        )

    return warnings


# ── Calendar aggregation ─────────────────────────────────────────────────


# Color mapping for calendar events
_TASK_COLORS = {
    "overdue": "#ef4444",  # red
    "due": "#f59e0b",  # amber
    "pending": "#3b82f6",  # blue
    "completed": "#10b981",  # green
}
_KYC_COLOR = "#8b5cf6"  # purple


async def get_calendar_events(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    date_from: date,
    date_to: date,
) -> list[dict]:
    """Return calendar events (tasks + KYC reviews) for a date range.

    Combines workflow tasks and KYC review deadlines into a single sorted list.
    """
    events: list[dict] = []
    today = date.today()

    # ── 1. Workflow tasks ────────────────────────────────────────────────
    task_query = (
        select(WorkflowTask)
        .where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.is_active.is_(True),
            WorkflowTask.due_date >= date_from,
            WorkflowTask.due_date <= date_to,
            WorkflowTask.status.notin_(("completed", "skipped")),
        )
        .order_by(WorkflowTask.due_date)
    )
    result = await db.execute(task_query)
    tasks = list(result.scalars().all())

    for task in tasks:
        case = task.case
        assigned_to = task.assigned_to
        # Derive status from due_date so a past-due task shows red ('Te laat'),
        # not blue ('Gepland'), even if the daily batch hasn't run (AUDIT-H22).
        eff_status = effective_task_status(task.status, task.due_date, today)
        events.append(
            {
                "id": str(task.id),
                "title": task.title,
                "date": task.due_date,
                "event_type": "task",
                "status": eff_status,
                "case_id": str(task.case_id),
                "case_number": case.case_number if case else None,
                "contact_id": None,
                "contact_name": None,
                "assigned_to_name": assigned_to.full_name if assigned_to else None,
                "task_type": task.task_type,
                "color": _TASK_COLORS.get(eff_status, "#3b82f6"),
            }
        )

    # ── 2. KYC review deadlines ──────────────────────────────────────────
    kyc_query = (
        select(KycVerification)
        .where(
            KycVerification.tenant_id == tenant_id,
            KycVerification.next_review_date.isnot(None),
            KycVerification.next_review_date >= date_from,
            KycVerification.next_review_date <= date_to,
        )
        .order_by(KycVerification.next_review_date)
    )
    result = await db.execute(kyc_query)
    kyc_records = list(result.scalars().all())

    for kyc in kyc_records:
        contact = kyc.contact
        review_date = kyc.next_review_date
        kyc_status = "overdue" if review_date < today else "pending"
        events.append(
            {
                "id": str(kyc.id),
                "title": f"KYC review: {contact.name}" if contact else "KYC review",
                "date": review_date,
                "event_type": "kyc_review",
                "status": kyc_status,
                "case_id": None,
                "case_number": None,
                "contact_id": str(kyc.contact_id),
                "contact_name": contact.name if contact else None,
                "assigned_to_name": None,
                "task_type": None,
                "color": _KYC_COLOR,
            }
        )

    # ── 3. Sort combined list by date ────────────────────────────────────
    events.sort(key=lambda e: e["date"])

    return events
