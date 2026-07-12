"""Workflow endpoints for tasks, calendar, and verjaring monitoring."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.workflow import service
from app.workflow.schemas import (
    CalendarEvent,
    WorkflowTaskCreate,
    WorkflowTaskResponse,
    WorkflowTaskUpdate,
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


# ── Verjaring check ────────────────────────────────────────────────────────


@router.get("/verjaring")
async def check_verjaring(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check all active cases for approaching verjaring (5 years)."""
    return await service.check_verjaring(db, current_user.tenant_id)
