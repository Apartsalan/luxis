"""Incasso pipeline router — endpoints for pipeline steps and batch actions."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.cases.models import Case
from app.database import get_db
from app.dependencies import get_current_user
from app.incasso import service
from app.incasso.schemas import (
    BatchActionRequest,
    BatchActionResult,
    BatchPreviewRequest,
    BatchPreviewResponse,
    CaseStepHistoryResponse,
    MoveToStepRequest,
    PipelineOverview,
    PipelineStepCreate,
    PipelineStepResponse,
    PipelineStepUpdate,
    QueueCounts,
    SetVerweerRequest,
    TransitionCreate,
    TransitionResponse,
    TransitionUpdate,
)
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/incasso", tags=["incasso"])


# ── Pipeline Steps CRUD ───────────────────────────────────────────────────


@router.get("/pipeline-steps", response_model=list[PipelineStepResponse])
async def list_pipeline_steps(
    active_only: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all incasso pipeline steps for the current tenant."""
    steps = await service.list_pipeline_steps(db, current_user.tenant_id, active_only=active_only)
    return [service.step_to_response(s) for s in steps]


@router.post(
    "/pipeline-steps",
    response_model=PipelineStepResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pipeline_step(
    data: PipelineStepCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new incasso pipeline step."""
    step = await service.create_pipeline_step(db, current_user.tenant_id, data)
    return service.step_to_response(step)


@router.put("/pipeline-steps/{step_id}", response_model=PipelineStepResponse)
async def update_pipeline_step(
    step_id: uuid.UUID,
    data: PipelineStepUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing incasso pipeline step."""
    step = await service.update_pipeline_step(db, current_user.tenant_id, step_id, data)
    return service.step_to_response(step)


@router.delete(
    "/pipeline-steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_pipeline_step(
    step_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete an incasso pipeline step."""
    await service.delete_pipeline_step(db, current_user.tenant_id, step_id)


@router.post(
    "/pipeline-steps/seed",
    response_model=list[PipelineStepResponse],
    status_code=status.HTTP_201_CREATED,
)
async def seed_pipeline_steps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Seed default incasso pipeline steps (if none exist)."""
    steps = await service.seed_default_steps(db, current_user.tenant_id)
    return [service.step_to_response(s) for s in steps]


# ── Step Transitions CRUD ─────────────────────────────────────────────────


@router.get("/transitions", response_model=list[TransitionResponse])
async def list_transitions(
    from_step_id: uuid.UUID | None = Query(default=None),
    active_only: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List step transitions, optionally filtered by source step."""
    transitions = await service.list_transitions(
        db, current_user.tenant_id, from_step_id=from_step_id, active_only=active_only
    )
    return [service.transition_to_response(t) for t in transitions]


@router.post(
    "/transitions",
    response_model=TransitionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transition(
    data: TransitionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new step transition."""
    t = await service.create_transition(db, current_user.tenant_id, data)
    return service.transition_to_response(t)


@router.put("/transitions/{transition_id}", response_model=TransitionResponse)
async def update_transition(
    transition_id: uuid.UUID,
    data: TransitionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing step transition."""
    t = await service.update_transition(db, current_user.tenant_id, transition_id, data)
    return service.transition_to_response(t)


@router.delete(
    "/transitions/{transition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_transition(
    transition_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a step transition."""
    await service.delete_transition(db, current_user.tenant_id, transition_id)


@router.post(
    "/transitions/seed",
    response_model=list[TransitionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def seed_transitions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Seed default transitions for the incasso workflow."""
    transitions = await service.seed_default_transitions(db, current_user.tenant_id)
    return [service.transition_to_response(t) for t in transitions]


# ── Pipeline Overview ─────────────────────────────────────────────────────


@router.get("/pipeline", response_model=PipelineOverview)
async def get_pipeline_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all incasso cases grouped by pipeline step."""
    return await service.get_pipeline_overview(db, current_user.tenant_id)


# ── Smart Work Queues ────────────────────────────────────────────────────


@router.get("/queues/counts", response_model=QueueCounts)
async def get_queue_counts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get badge counts for Smart Work Queue tabs."""
    return await service.get_queue_counts(db, current_user.tenant_id)


# ── Case Step Operations ─────────────────────────────────────────────────


@router.get(
    "/cases/{case_id}/step-history",
    response_model=list[CaseStepHistoryResponse],
)
async def get_case_step_history(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get step history timeline for a case."""
    return await service.get_case_step_history(db, current_user.tenant_id, case_id)


@router.post("/cases/{case_id}/move-step")
async def move_case_to_step(
    case_id: uuid.UUID,
    data: MoveToStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Move a case to a specific pipeline step."""
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == current_user.tenant_id,
            Case.id == case_id,
            Case.is_active.is_(True),
        )
    )
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError("Dossier niet gevonden")

    target_step = await service.get_pipeline_step_by_id(
        db, current_user.tenant_id, data.target_step_id
    )

    await service.move_case_to_step(
        db, current_user.tenant_id, case, target_step,
        user_id=current_user.id,
        trigger_type="manual",
        notes=data.notes,
    )
    return {"status": "ok"}


@router.post("/cases/{case_id}/verweer")
async def set_case_verweer(
    case_id: uuid.UUID,
    data: SetVerweerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle verweer (objection/dispute) on a case."""
    await service.set_case_verweer(
        db, current_user.tenant_id, case_id,
        has_verweer=data.has_verweer,
        verweer_note=data.verweer_note,
        verweer_date=data.verweer_date,
        user_id=current_user.id,
    )
    return {"status": "ok"}


# ── Batch Actions ─────────────────────────────────────────────────────────


@router.post("/batch/preview", response_model=BatchPreviewResponse)
async def batch_preview(
    data: BatchPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pre-flight check for a batch action — shows blockers and status changes needed."""
    return await service.batch_preview(
        db,
        current_user.tenant_id,
        data.case_ids,
        data.action,
        data.target_step_id,
    )


@router.post("/batch", response_model=BatchActionResult)
async def batch_execute(
    data: BatchActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute a batch action on selected incasso cases."""
    return await service.batch_execute(
        db,
        current_user.tenant_id,
        current_user.id,
        data.case_ids,
        data.action,
        data.target_step_id,
        data.auto_assign_step,
        data.send_email,
    )


# ── Manual draft trigger (sessie 133) ─────────────────────────────────────


@router.post("/cases/{case_id}/generate-draft", status_code=status.HTTP_201_CREATED)
async def generate_draft_for_current_step(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Genereer handmatig een AI-draft voor de huidige stap van een dossier.

    Werkt altijd, ongeacht tenant.pipeline_auto_drafts_enabled flag. De draft
    wordt opgeslagen in `ai_drafts` en er komt een task in `/taken` queue.
    """
    from app.incasso.automation_service import generate_draft_for_step

    case = (await db.execute(
        select(Case).where(
            Case.tenant_id == current_user.tenant_id,
            Case.id == case_id,
        )
    )).scalar_one_or_none()
    if not case:
        raise NotFoundError("Dossier niet gevonden")
    if not case.incasso_step_id:
        raise NotFoundError("Dossier heeft geen actieve incasso-stap")

    # Voor manual trigger: target_step = huidige stap (genereer draft voor wat NU staat)
    draft = await generate_draft_for_step(
        db,
        tenant_id=current_user.tenant_id,
        case_id=case_id,
        target_step_id=case.incasso_step_id,
        rule_match=None,
        create_workflow_task=True,
    )
    await db.commit()

    return {
        "draft_id": str(draft.id),
        "case_id": str(case_id),
        "subject": draft.subject,
        "model_used": draft.model_used,
        "status": draft.status,
        "message": "Concept klaargezet in /taken voor review.",
    }
