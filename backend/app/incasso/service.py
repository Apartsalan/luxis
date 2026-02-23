"""Incasso pipeline service — business logic for pipeline steps and batch actions."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.incasso.models import IncassoPipelineStep
from app.incasso.schemas import (
    BatchActionResult,
    BatchBlocker,
    BatchPreviewResponse,
    CaseInPipeline,
    PipelineColumn,
    PipelineOverview,
    PipelineStepCreate,
    PipelineStepResponse,
    PipelineStepUpdate,
)
from app.shared.exceptions import BadRequestError, NotFoundError

# ── Pipeline Step CRUD ────────────────────────────────────────────────────


async def list_pipeline_steps(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    active_only: bool = True,
) -> list[IncassoPipelineStep]:
    """List all pipeline steps for a tenant, ordered by sort_order."""
    query = select(IncassoPipelineStep).where(
        IncassoPipelineStep.tenant_id == tenant_id,
    )
    if active_only:
        query = query.where(IncassoPipelineStep.is_active.is_(True))
    query = query.order_by(IncassoPipelineStep.sort_order)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_pipeline_step_by_id(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    step_id: uuid.UUID,
) -> IncassoPipelineStep:
    """Get a single pipeline step by ID."""
    result = await db.execute(
        select(IncassoPipelineStep).where(
            IncassoPipelineStep.tenant_id == tenant_id,
            IncassoPipelineStep.id == step_id,
        )
    )
    step = result.scalar_one_or_none()
    if not step:
        raise NotFoundError("Pipeline stap niet gevonden")
    return step


async def create_pipeline_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: PipelineStepCreate,
) -> IncassoPipelineStep:
    """Create a new pipeline step."""
    step = IncassoPipelineStep(
        tenant_id=tenant_id,
        **data.model_dump(),
    )
    db.add(step)
    await db.flush()
    await db.refresh(step)
    return step


async def update_pipeline_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    step_id: uuid.UUID,
    data: PipelineStepUpdate,
) -> IncassoPipelineStep:
    """Update an existing pipeline step."""
    step = await get_pipeline_step_by_id(db, tenant_id, step_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(step, field, value)
    await db.flush()
    await db.refresh(step)
    return step


async def delete_pipeline_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    step_id: uuid.UUID,
) -> None:
    """Soft-delete a pipeline step. Unassign cases first."""
    step = await get_pipeline_step_by_id(db, tenant_id, step_id)

    # Unassign any cases from this step
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.incasso_step_id == step_id,
        )
    )
    for case in result.scalars().all():
        case.incasso_step_id = None

    step.is_active = False
    await db.flush()


async def seed_default_steps(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[IncassoPipelineStep]:
    """Seed default incasso pipeline steps for a tenant (if none exist)."""
    existing = await list_pipeline_steps(db, tenant_id, active_only=False)
    if existing:
        return existing

    defaults = [
        {"name": "Aanmaning", "sort_order": 1, "min_wait_days": 0},
        {"name": "Sommatie", "sort_order": 2, "min_wait_days": 14},
        {"name": "2e Sommatie", "sort_order": 3, "min_wait_days": 14},
        {"name": "Ingebrekestelling", "sort_order": 4, "min_wait_days": 14},
        {"name": "Dagvaarding", "sort_order": 5, "min_wait_days": 14},
        {"name": "Executie", "sort_order": 6, "min_wait_days": 0},
    ]

    steps = []
    for d in defaults:
        step = IncassoPipelineStep(tenant_id=tenant_id, **d)
        db.add(step)
        steps.append(step)

    await db.flush()
    for step in steps:
        await db.refresh(step)
    return steps


# ── Pipeline Step Response Helper ─────────────────────────────────────────


def step_to_response(step: IncassoPipelineStep) -> PipelineStepResponse:
    """Convert a pipeline step model to response schema."""
    return PipelineStepResponse(
        id=step.id,
        name=step.name,
        sort_order=step.sort_order,
        min_wait_days=step.min_wait_days,
        template_id=step.template_id,
        template_name=step.template.name if step.template else None,
        is_active=step.is_active,
        created_at=step.created_at,
        updated_at=step.updated_at,
    )


# ── Pipeline Overview ─────────────────────────────────────────────────────


def _case_to_pipeline_item(case: Case, step_entered_date: date | None = None) -> CaseInPipeline:
    """Convert a Case model to CaseInPipeline schema."""
    outstanding = float(case.total_principal) - float(case.total_paid)
    if step_entered_date:
        days_in_step = (date.today() - step_entered_date).days
    else:
        days_in_step = (date.today() - case.date_opened).days

    return CaseInPipeline(
        id=case.id,
        case_number=case.case_number,
        client_name=case.client.name if case.client else "Onbekend",
        opposing_party_name=case.opposing_party.name if case.opposing_party else None,
        total_principal=float(case.total_principal),
        total_paid=float(case.total_paid),
        outstanding=round(outstanding, 2),
        days_in_step=days_in_step,
        incasso_step_id=case.incasso_step_id,
        status=case.status,
        date_opened=case.date_opened.isoformat(),
    )


async def get_pipeline_overview(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> PipelineOverview:
    """Get all incasso cases grouped by pipeline step."""
    # Get active steps
    steps = await list_pipeline_steps(db, tenant_id, active_only=True)

    # Get all active incasso cases
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.case_type == "incasso",
            Case.is_active.is_(True),
            Case.status != "afgesloten",
        )
    )
    all_cases = list(result.scalars().all())

    # Group cases by step
    step_map: dict[uuid.UUID, list[CaseInPipeline]] = {s.id: [] for s in steps}
    unassigned: list[CaseInPipeline] = []

    for case in all_cases:
        item = _case_to_pipeline_item(case)
        if case.incasso_step_id and case.incasso_step_id in step_map:
            step_map[case.incasso_step_id].append(item)
        else:
            unassigned.append(item)

    # Build columns
    columns = []
    for step in steps:
        cases_in_step = step_map.get(step.id, [])
        columns.append(
            PipelineColumn(
                step=step_to_response(step),
                cases=cases_in_step,
                count=len(cases_in_step),
            )
        )

    return PipelineOverview(
        columns=columns,
        unassigned=unassigned,
        total_cases=len(all_cases),
    )


# ── Batch Preview ─────────────────────────────────────────────────────────


async def batch_preview(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_ids: list[uuid.UUID],
    action: str,
    target_step_id: uuid.UUID | None = None,
) -> BatchPreviewResponse:
    """Pre-flight check for a batch action."""
    if not case_ids:
        raise BadRequestError("Geen dossiers geselecteerd")

    # Fetch the selected cases
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.id.in_(case_ids),
            Case.case_type == "incasso",
            Case.is_active.is_(True),
        )
    )
    cases = list(result.scalars().all())

    blocked: list[BatchBlocker] = []
    needs_step: list[CaseInPipeline] = []
    ready = 0

    if action == "advance_step":
        if not target_step_id:
            raise BadRequestError("Geen doelstap opgegeven voor statuswijziging")

        # Verify target step exists (raises NotFoundError if not)
        await get_pipeline_step_by_id(db, tenant_id, target_step_id)

        for case in cases:
            # Check blockers
            if case.status in ("betaald", "afgesloten"):
                blocked.append(BatchBlocker(
                    case_id=case.id,
                    case_number=case.case_number,
                    reason=f"Dossier heeft status '{case.status}'",
                ))
                continue

            if not case.incasso_step_id:
                needs_step.append(_case_to_pipeline_item(case))
                continue

            ready += 1

    elif action == "generate_document":
        for case in cases:
            if not case.incasso_step_id:
                needs_step.append(_case_to_pipeline_item(case))
                continue
            ready += 1

    elif action == "recalculate_interest":
        for case in cases:
            ready += 1

    else:
        raise BadRequestError(f"Onbekende actie: {action}")

    return BatchPreviewResponse(
        action=action,
        total_selected=len(cases),
        ready=ready,
        blocked=blocked,
        needs_step_assignment=needs_step,
    )


# ── Batch Execute ─────────────────────────────────────────────────────────


async def batch_execute(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_ids: list[uuid.UUID],
    action: str,
    target_step_id: uuid.UUID | None = None,
    auto_assign_step: bool = False,
) -> BatchActionResult:
    """Execute a batch action on selected cases."""
    if not case_ids:
        raise BadRequestError("Geen dossiers geselecteerd")

    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.id.in_(case_ids),
            Case.case_type == "incasso",
            Case.is_active.is_(True),
        )
    )
    cases = list(result.scalars().all())

    processed = 0
    skipped = 0
    errors: list[str] = []

    if action == "advance_step":
        if not target_step_id:
            raise BadRequestError("Geen doelstap opgegeven")

        target_step = await get_pipeline_step_by_id(db, tenant_id, target_step_id)

        # If auto_assign, get the first step for unassigned cases
        first_step = None
        if auto_assign_step:
            steps = await list_pipeline_steps(db, tenant_id, active_only=True)
            if steps:
                first_step = steps[0]

        for case in cases:
            if case.status in ("betaald", "afgesloten"):
                skipped += 1
                errors.append(f"{case.case_number}: status '{case.status}' — overgeslagen")
                continue

            if not case.incasso_step_id and auto_assign_step and first_step:
                case.incasso_step_id = first_step.id

            case.incasso_step_id = target_step.id
            processed += 1

    elif action == "generate_document":
        # Document generation is a placeholder — will integrate with document module
        for case in cases:
            if not case.incasso_step_id:
                skipped += 1
                errors.append(f"{case.case_number}: geen pipeline stap — overgeslagen")
                continue
            # TODO: integrate with document generation service
            processed += 1

    elif action == "recalculate_interest":
        # Interest recalculation placeholder — will integrate with collections module
        for case in cases:
            # TODO: integrate with interest calculation service
            processed += 1

    else:
        raise BadRequestError(f"Onbekende actie: {action}")

    await db.flush()

    return BatchActionResult(
        action=action,
        processed=processed,
        skipped=skipped,
        errors=errors,
    )
