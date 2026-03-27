"""Workflow module endpoints — statuses, transitions, tasks, rules."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.workflow import service
from app.workflow.schemas import (
    AllowedTransitionResponse,
    CalendarEvent,
    WorkflowRuleCreate,
    WorkflowRuleResponse,
    WorkflowRuleUpdate,
    WorkflowStatusCreate,
    WorkflowStatusResponse,
    WorkflowStatusUpdate,
    WorkflowTaskCreate,
    WorkflowTaskResponse,
    WorkflowTaskUpdate,
    WorkflowTransitionCreate,
    WorkflowTransitionResponse,
)

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


# ── Calendar ────────────────────────────────────────────────────────────────


@router.get("/calendar", response_model=list[CalendarEvent])
async def get_calendar_events(
    date_from: date = Query(..., description="Start of date range (inclusive)"),
    date_to: date = Query(..., description="End of date range (inclusive)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get calendar events (workflow tasks + KYC reviews) for a date range."""
    rows = await service.get_calendar_events(db, current_user.tenant_id, date_from, date_to)
    return [CalendarEvent(**row) for row in rows]


# ── Statuses ────────────────────────────────────────────────────────────────


@router.get("/statuses", response_model=list[WorkflowStatusResponse])
async def list_statuses(
    active_only: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all workflow statuses for the current tenant."""
    return await service.list_statuses(db, current_user.tenant_id, active_only=active_only)


@router.post(
    "/statuses",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_status(
    data: WorkflowStatusCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow status (admin only)."""
    return await service.create_status(db, current_user.tenant_id, data)


@router.put("/statuses/{status_id}", response_model=WorkflowStatusResponse)
async def update_status(
    status_id: uuid.UUID,
    data: WorkflowStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a workflow status."""
    return await service.update_status(db, current_user.tenant_id, status_id, data)


@router.delete("/statuses/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_status(
    status_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a workflow status (fails if in use)."""
    await service.delete_status(db, current_user.tenant_id, status_id)


# ── Transitions ─────────────────────────────────────────────────────────────


@router.get("/transitions", response_model=list[WorkflowTransitionResponse])
async def list_transitions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active transitions."""
    return await service.list_transitions(db, current_user.tenant_id)


@router.get(
    "/transitions/allowed",
    response_model=list[AllowedTransitionResponse],
)
async def get_allowed_transitions(
    from_status: str = Query(..., description="Current status slug"),
    debtor_type: str = Query(default="b2b", description="b2b or b2c"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get allowed transitions from a given status for a debtor type."""
    return await service.get_allowed_transitions(
        db, current_user.tenant_id, from_status, debtor_type
    )


@router.post(
    "/transitions",
    response_model=WorkflowTransitionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transition(
    data: WorkflowTransitionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new transition (admin only)."""
    return await service.create_transition(db, current_user.tenant_id, data)


@router.delete(
    "/transitions/{transition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_transition(
    transition_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a transition."""
    await service.delete_transition(db, current_user.tenant_id, transition_id)


# ── Tasks ───────────────────────────────────────────────────────────────────


@router.get("/tasks", response_model=list[WorkflowTaskResponse])
async def list_tasks(
    case_id: uuid.UUID | None = Query(default=None),
    task_status: str | None = Query(default=None, alias="status"),
    assigned_to_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List workflow tasks with optional filters."""
    return await service.list_tasks(
        db,
        current_user.tenant_id,
        case_id=case_id,
        status=task_status,
        assigned_to_id=assigned_to_id,
    )


@router.get("/tasks/{task_id}", response_model=WorkflowTaskResponse)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single task."""
    return await service.get_task(db, current_user.tenant_id, task_id)


@router.post(
    "/tasks",
    response_model=WorkflowTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    data: WorkflowTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a manual workflow task."""
    return await service.create_task(db, current_user.tenant_id, data)


@router.put("/tasks/{task_id}", response_model=WorkflowTaskResponse)
async def update_task(
    task_id: uuid.UUID,
    data: WorkflowTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a workflow task (status, assignee, etc.)."""
    return await service.update_task(db, current_user.tenant_id, task_id, data)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a workflow task."""
    await service.delete_task(db, current_user.tenant_id, task_id)


# ── Rules ───────────────────────────────────────────────────────────────────


@router.get("/rules", response_model=list[WorkflowRuleResponse])
async def list_rules(
    active_only: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all workflow rules."""
    return await service.list_rules(db, current_user.tenant_id, active_only=active_only)


@router.post(
    "/rules",
    response_model=WorkflowRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rule(
    data: WorkflowRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow rule (admin only)."""
    return await service.create_rule(db, current_user.tenant_id, data)


@router.put("/rules/{rule_id}", response_model=WorkflowRuleResponse)
async def update_rule(
    rule_id: uuid.UUID,
    data: WorkflowRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a workflow rule."""
    return await service.update_rule(db, current_user.tenant_id, rule_id, data)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a workflow rule."""
    await service.delete_rule(db, current_user.tenant_id, rule_id)


# ── Verjaring check ────────────────────────────────────────────────────────


@router.get("/verjaring")
async def check_verjaring(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check all active cases for approaching verjaring (5 years)."""
    return await service.check_verjaring(db, current_user.tenant_id)
