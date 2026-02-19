"""Workflow service — database-driven status engine with legal constraints.

Replaces the hardcoded STATUS_TRANSITIONS dict in cases/schemas.py.
All transition validation now comes from the workflow_transitions table,
with additional hardcoded legal constraints (14-dagenbrief, verjaring).
"""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseActivity
from app.relations.kyc_models import KycVerification
from app.shared.exceptions import BadRequestError, ConflictError, NotFoundError
from app.workflow.models import (
    WorkflowRule,
    WorkflowStatus,
    WorkflowTask,
    WorkflowTransition,
)
from app.workflow.schemas import (
    LEGAL_CONSTRAINTS,
    TASK_STATUSES,
    TASK_TYPES,
    AllowedTransitionResponse,
    TransitionValidationResult,
    WorkflowRuleCreate,
    WorkflowRuleUpdate,
    WorkflowStatusCreate,
    WorkflowStatusUpdate,
    WorkflowTaskCreate,
    WorkflowTaskUpdate,
    WorkflowTransitionCreate,
)


# ── WorkflowStatus CRUD ────────────────────────────────────────────────────


async def list_statuses(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    active_only: bool = True,
) -> list[WorkflowStatus]:
    """List all workflow statuses for a tenant, ordered by sort_order."""
    query = select(WorkflowStatus).where(
        WorkflowStatus.tenant_id == tenant_id,
    )
    if active_only:
        query = query.where(WorkflowStatus.is_active.is_(True))
    query = query.order_by(WorkflowStatus.sort_order)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_status_by_slug(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    slug: str,
) -> WorkflowStatus:
    """Get a workflow status by slug. Raises NotFoundError if not found."""
    result = await db.execute(
        select(WorkflowStatus).where(
            WorkflowStatus.tenant_id == tenant_id,
            WorkflowStatus.slug == slug,
            WorkflowStatus.is_active.is_(True),
        )
    )
    status = result.scalar_one_or_none()
    if status is None:
        raise NotFoundError(f"Workflow status '{slug}' niet gevonden")
    return status


async def get_status_by_id(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    status_id: uuid.UUID,
) -> WorkflowStatus:
    """Get a workflow status by ID."""
    result = await db.execute(
        select(WorkflowStatus).where(
            WorkflowStatus.id == status_id,
            WorkflowStatus.tenant_id == tenant_id,
        )
    )
    status = result.scalar_one_or_none()
    if status is None:
        raise NotFoundError("Workflow status niet gevonden")
    return status


async def create_status(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: WorkflowStatusCreate,
) -> WorkflowStatus:
    """Create a new workflow status."""
    # Check slug uniqueness
    existing = await db.execute(
        select(WorkflowStatus).where(
            WorkflowStatus.tenant_id == tenant_id,
            WorkflowStatus.slug == data.slug,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Status met slug '{data.slug}' bestaat al")

    status = WorkflowStatus(tenant_id=tenant_id, **data.model_dump())
    db.add(status)
    await db.flush()
    await db.refresh(status)
    return status


async def update_status(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    status_id: uuid.UUID,
    data: WorkflowStatusUpdate,
) -> WorkflowStatus:
    """Update a workflow status."""
    status = await get_status_by_id(db, tenant_id, status_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(status, field, value)
    await db.flush()
    await db.refresh(status)
    return status


async def delete_status(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    status_id: uuid.UUID,
) -> None:
    """Soft-delete a workflow status. Fails if status is in use by cases."""
    status = await get_status_by_id(db, tenant_id, status_id)

    # Check if any active cases use this status
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.status == status.slug,
            Case.is_active.is_(True),
        ).limit(1)
    )
    if result.scalar_one_or_none():
        raise ConflictError(
            f"Status '{status.label}' is in gebruik door actieve zaken en kan niet worden verwijderd"
        )

    status.is_active = False
    await db.flush()


# ── WorkflowTransition CRUD ────────────────────────────────────────────────


async def list_transitions(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[WorkflowTransition]:
    """List all active transitions for a tenant."""
    result = await db.execute(
        select(WorkflowTransition).where(
            WorkflowTransition.tenant_id == tenant_id,
            WorkflowTransition.is_active.is_(True),
        )
    )
    return list(result.scalars().all())


async def create_transition(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: WorkflowTransitionCreate,
) -> WorkflowTransition:
    """Create a new transition."""
    transition = WorkflowTransition(tenant_id=tenant_id, **data.model_dump())
    db.add(transition)
    await db.flush()
    await db.refresh(transition)
    return transition


async def delete_transition(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    transition_id: uuid.UUID,
) -> None:
    """Soft-delete a transition."""
    result = await db.execute(
        select(WorkflowTransition).where(
            WorkflowTransition.id == transition_id,
            WorkflowTransition.tenant_id == tenant_id,
        )
    )
    transition = result.scalar_one_or_none()
    if transition is None:
        raise NotFoundError("Transitie niet gevonden")
    transition.is_active = False
    await db.flush()


# ── Status Engine — validate and execute transitions ────────────────────────


async def get_allowed_transitions(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    from_slug: str,
    debtor_type: str,
) -> list[AllowedTransitionResponse]:
    """Get allowed transitions from a given status for a debtor type."""
    from_status = await get_status_by_slug(db, tenant_id, from_slug)

    result = await db.execute(
        select(WorkflowTransition).where(
            WorkflowTransition.tenant_id == tenant_id,
            WorkflowTransition.from_status_id == from_status.id,
            WorkflowTransition.is_active.is_(True),
            WorkflowTransition.debtor_type.in_([debtor_type, "both"]),
        )
    )
    transitions = list(result.scalars().all())

    return [
        AllowedTransitionResponse(
            to_status_id=t.to_status.id,
            to_slug=t.to_status.slug,
            to_label=t.to_status.label,
            to_phase=t.to_status.phase,
            to_color=t.to_status.color,
            debtor_type=t.debtor_type,
            requires_note=t.requires_note,
        )
        for t in transitions
        if t.to_status.is_active
    ]


async def validate_transition(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    new_slug: str,
) -> TransitionValidationResult:
    """Validate a status transition with legal constraints.

    Returns validation result with errors (blockers) and warnings (advisories).
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Check target status exists
    try:
        to_status = await get_status_by_slug(db, tenant_id, new_slug)
    except NotFoundError:
        return TransitionValidationResult(
            allowed=False,
            errors=[f"Status '{new_slug}' bestaat niet"],
        )

    # 2. Check transition is allowed in database
    from_status = await get_status_by_slug(db, tenant_id, case.status)
    result = await db.execute(
        select(WorkflowTransition).where(
            WorkflowTransition.tenant_id == tenant_id,
            WorkflowTransition.from_status_id == from_status.id,
            WorkflowTransition.to_status_id == to_status.id,
            WorkflowTransition.is_active.is_(True),
            WorkflowTransition.debtor_type.in_([case.debtor_type, "both"]),
        )
    )
    transition = result.scalar_one_or_none()

    if transition is None:
        allowed_transitions = await get_allowed_transitions(
            db, tenant_id, case.status, case.debtor_type
        )
        allowed_labels = [t.to_label for t in allowed_transitions]
        errors.append(
            f"Status kan niet van '{case.status}' naar '{new_slug}'. "
            f"Toegestane overgangen: {', '.join(allowed_labels) if allowed_labels else 'geen (eindstatus)'}"
        )
        return TransitionValidationResult(allowed=False, errors=errors)

    # 3. Legal constraint: B2C must have 14_dagenbrief before sommatie
    if (
        LEGAL_CONSTRAINTS["14_dagenbrief_required_b2c"]
        and case.debtor_type == "b2c"
        and new_slug == "sommatie"
    ):
        # Check if case has ever been in 14_dagenbrief status
        result = await db.execute(
            select(CaseActivity).where(
                CaseActivity.case_id == case.id,
                CaseActivity.activity_type == "status_change",
                CaseActivity.new_status == "14_dagenbrief",
            ).limit(1)
        )
        if not result.scalar_one_or_none():
            errors.append(
                "B2C-zaak vereist 14-dagenbrief voordat sommatie verstuurd kan worden "
                "(Art. 6:96 lid 6 BW)"
            )

    # 4. Legal constraint: minimum 14 days after 14_dagenbrief
    if case.status == "14_dagenbrief" and new_slug not in ("betaald", "oninbaar", "schikking"):
        min_wait = LEGAL_CONSTRAINTS["14_dagenbrief_min_wait"]
        # Find when 14_dagenbrief was set
        result = await db.execute(
            select(CaseActivity).where(
                CaseActivity.case_id == case.id,
                CaseActivity.activity_type == "status_change",
                CaseActivity.new_status == "14_dagenbrief",
            ).order_by(CaseActivity.created_at.desc()).limit(1)
        )
        activity = result.scalar_one_or_none()
        if activity:
            days_elapsed = (datetime.now(UTC) - activity.created_at).days
            if days_elapsed < min_wait:
                remaining = min_wait - days_elapsed
                errors.append(
                    f"Na 14-dagenbrief moeten minimaal {min_wait} dagen gewacht worden. "
                    f"Nog {remaining} dag(en) te gaan (Art. 6:96 lid 6 BW)"
                )

    # 5. Verjaring warning (advisory, not blocking)
    if hasattr(case, "date_opened") and case.date_opened:
        verjaring_years = LEGAL_CONSTRAINTS["verjaring_years"]
        verjaring_date = case.date_opened.replace(
            year=case.date_opened.year + verjaring_years
        )
        days_until_verjaring = (verjaring_date - date.today()).days
        if days_until_verjaring <= 0:
            warnings.append(
                f"WAARSCHUWING: Verjaring bereikt op {verjaring_date.strftime('%d-%m-%Y')} "
                f"(Art. 3:307 BW). Zaak is mogelijk verjaard!"
            )
        elif days_until_verjaring <= 90:
            warnings.append(
                f"Let op: verjaring nadert op {verjaring_date.strftime('%d-%m-%Y')} "
                f"(nog {days_until_verjaring} dagen). Overweeg stuitingshandeling."
            )

    return TransitionValidationResult(
        allowed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


async def execute_transition(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    new_slug: str,
    user_id: uuid.UUID,
    note: str | None = None,
) -> tuple[Case, TransitionValidationResult]:
    """Validate and execute a status transition.

    Returns the updated case and validation result (with warnings even on success).
    """
    validation = await validate_transition(db, tenant_id, case, new_slug)
    if not validation.allowed:
        raise ConflictError("; ".join(validation.errors))

    to_status = await get_status_by_slug(db, tenant_id, new_slug)

    old_status = case.status
    case.status = new_slug

    # Set date_closed if moving to terminal state
    if to_status.is_terminal:
        case.date_closed = date.today()

    await db.flush()

    # Log activity
    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case.id,
        user_id=user_id,
        activity_type="status_change",
        title=f"Status gewijzigd: {old_status} \u2192 {new_slug}",
        description=note,
        old_status=old_status,
        new_status=new_slug,
    )
    db.add(activity)
    await db.flush()

    await db.refresh(case)
    return case, validation


# ── WorkflowRule CRUD ───────────────────────────────────────────────────────


async def list_rules(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    active_only: bool = True,
) -> list[WorkflowRule]:
    """List all workflow rules for a tenant."""
    query = select(WorkflowRule).where(
        WorkflowRule.tenant_id == tenant_id,
    )
    if active_only:
        query = query.where(WorkflowRule.is_active.is_(True))
    query = query.order_by(WorkflowRule.sort_order)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_rule(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rule_id: uuid.UUID,
) -> WorkflowRule:
    """Get a workflow rule by ID."""
    result = await db.execute(
        select(WorkflowRule).where(
            WorkflowRule.id == rule_id,
            WorkflowRule.tenant_id == tenant_id,
        )
    )
    rule = result.scalar_one_or_none()
    if rule is None:
        raise NotFoundError("Workflow regel niet gevonden")
    return rule


async def create_rule(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: WorkflowRuleCreate,
) -> WorkflowRule:
    """Create a new workflow rule."""
    if data.action_type not in TASK_TYPES:
        raise BadRequestError(
            f"Ongeldig actietype: {data.action_type}. "
            f"Kies uit: {', '.join(TASK_TYPES)}"
        )
    rule = WorkflowRule(tenant_id=tenant_id, **data.model_dump())
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


async def update_rule(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rule_id: uuid.UUID,
    data: WorkflowRuleUpdate,
) -> WorkflowRule:
    """Update a workflow rule."""
    rule = await get_rule(db, tenant_id, rule_id)
    update_data = data.model_dump(exclude_unset=True)
    if "action_type" in update_data and update_data["action_type"] not in TASK_TYPES:
        raise BadRequestError(
            f"Ongeldig actietype: {update_data['action_type']}. "
            f"Kies uit: {', '.join(TASK_TYPES)}"
        )
    for field, value in update_data.items():
        setattr(rule, field, value)
    await db.flush()
    await db.refresh(rule)
    return rule


async def delete_rule(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rule_id: uuid.UUID,
) -> None:
    """Soft-delete a workflow rule."""
    rule = await get_rule(db, tenant_id, rule_id)
    rule.is_active = False
    await db.flush()


# ── WorkflowTask CRUD ──────────────────────────────────────────────────────


async def list_tasks(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    case_id: uuid.UUID | None = None,
    status: str | None = None,
    assigned_to_id: uuid.UUID | None = None,
) -> list[WorkflowTask]:
    """List workflow tasks with optional filters."""
    query = select(WorkflowTask).where(
        WorkflowTask.tenant_id == tenant_id,
        WorkflowTask.is_active.is_(True),
    )
    if case_id:
        query = query.where(WorkflowTask.case_id == case_id)
    if status:
        query = query.where(WorkflowTask.status == status)
    if assigned_to_id:
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
            f"Ongeldig taaktype: {data.task_type}. "
            f"Kies uit: {', '.join(TASK_TYPES)}"
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
                f"Ongeldige taakstatus: {new_status}. "
                f"Kies uit: {', '.join(TASK_STATUSES)}"
            )
        if new_status == "completed":
            task.completed_at = datetime.now(UTC)
        elif new_status in ("pending", "due"):
            task.completed_at = None

    for field, value in update_data.items():
        setattr(task, field, value)

    await db.flush()
    await db.refresh(task)
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


# ── Task Engine — create tasks from rules on status change ──────────────────


async def evaluate_rules_for_transition(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    new_status_slug: str,
) -> list[WorkflowTask]:
    """Evaluate workflow rules after a status transition and create tasks.

    Called after a successful status change. Finds matching rules and creates tasks.
    """
    new_status = await get_status_by_slug(db, tenant_id, new_status_slug)

    # Find matching rules
    result = await db.execute(
        select(WorkflowRule).where(
            WorkflowRule.tenant_id == tenant_id,
            WorkflowRule.trigger_status_id == new_status.id,
            WorkflowRule.is_active.is_(True),
            WorkflowRule.debtor_type.in_([case.debtor_type, "both"]),
        ).order_by(WorkflowRule.sort_order)
    )
    matching_rules = list(result.scalars().all())

    created_tasks = []
    for rule in matching_rules:
        due_date = date.today() + timedelta(days=rule.days_delay)

        task = WorkflowTask(
            tenant_id=tenant_id,
            case_id=case.id,
            assigned_to_id=case.assigned_to_id if rule.assign_to_case_owner else None,
            task_type=rule.action_type,
            title=f"{rule.name} voor zaak {case.case_number}",
            description=rule.description,
            due_date=due_date,
            status="pending" if rule.days_delay > 0 else "due",
            auto_execute=rule.auto_execute,
            action_config=rule.action_config,
            created_by_rule_id=rule.id,
        )
        db.add(task)
        created_tasks.append(task)

    if created_tasks:
        await db.flush()
        for task in created_tasks:
            await db.refresh(task)

    return created_tasks


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
    warning_threshold = today - timedelta(days=verjaring_years * 365 - 90)

    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.date_closed.is_(None),
            Case.date_opened <= warning_threshold,
        )
    )

    warnings = []
    for case in result.scalars().all():
        verjaring_date = case.date_opened.replace(
            year=case.date_opened.year + verjaring_years
        )
        days_remaining = (verjaring_date - today).days
        warnings.append({
            "case_id": str(case.id),
            "case_number": case.case_number,
            "date_opened": case.date_opened.isoformat(),
            "verjaring_date": verjaring_date.isoformat(),
            "days_remaining": days_remaining,
            "is_expired": days_remaining <= 0,
        })

    return warnings


# ── Calendar aggregation ─────────────────────────────────────────────────


# Color mapping for calendar events
_TASK_COLORS = {
    "overdue": "#ef4444",   # red
    "due": "#f59e0b",       # amber
    "pending": "#3b82f6",   # blue
    "completed": "#10b981", # green
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
        events.append({
            "id": str(task.id),
            "title": task.title,
            "date": task.due_date,
            "event_type": "task",
            "status": task.status,
            "case_id": str(task.case_id),
            "case_number": case.case_number if case else None,
            "contact_id": None,
            "contact_name": None,
            "assigned_to_name": assigned_to.full_name if assigned_to else None,
            "task_type": task.task_type,
            "color": _TASK_COLORS.get(task.status, "#3b82f6"),
        })

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

    today = date.today()
    for kyc in kyc_records:
        contact = kyc.contact
        review_date = kyc.next_review_date
        kyc_status = "overdue" if review_date < today else "pending"
        events.append({
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
        })

    # ── 3. Sort combined list by date ────────────────────────────────────
    events.sort(key=lambda e: e["date"])

    return events
