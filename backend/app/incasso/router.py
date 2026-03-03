"""Incasso pipeline router — endpoints for pipeline steps and batch actions."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.incasso import service
from app.incasso.schemas import (
    BatchActionRequest,
    BatchActionResult,
    BatchPreviewRequest,
    BatchPreviewResponse,
    PipelineOverview,
    PipelineStepCreate,
    PipelineStepResponse,
    PipelineStepUpdate,
    QueueCounts,
)

router = APIRouter(prefix="/api/incasso", tags=["incasso"])


# ── Pipeline Steps CRUD ───────────────────────────────────────────────────


@router.get("/pipeline-steps", response_model=list[PipelineStepResponse])
async def list_pipeline_steps(
    active_only: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all incasso pipeline steps for the current tenant."""
    steps = await service.list_pipeline_steps(
        db, current_user.tenant_id, active_only=active_only
    )
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
    step = await service.update_pipeline_step(
        db, current_user.tenant_id, step_id, data
    )
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
