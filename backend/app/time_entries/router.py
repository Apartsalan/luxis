"""Time entries router — endpoints for time tracking (tijdschrijven)."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from starlette import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.time_entries import service
from app.time_entries.schemas import (
    TimeEntryCreate,
    TimeEntryResponse,
    TimeEntrySummary,
    TimeEntryUpdate,
)

router = APIRouter(prefix="/api/time-entries", tags=["time-entries"])


@router.get("", response_model=list[TimeEntryResponse])
async def list_time_entries(
    case_id: uuid.UUID | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    billable: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List time entries with optional filters."""
    return await service.list_time_entries(
        db,
        current_user.tenant_id,
        case_id=case_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        billable=billable,
    )


@router.post(
    "",
    response_model=TimeEntryResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_time_entry(
    data: TimeEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new time entry for the current user."""
    return await service.create_time_entry(
        db, current_user.tenant_id, current_user.id, data
    )


@router.put("/{entry_id}", response_model=TimeEntryResponse)
async def update_time_entry(
    entry_id: uuid.UUID,
    data: TimeEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a time entry."""
    return await service.update_time_entry(
        db, current_user.tenant_id, entry_id, data
    )


@router.delete(
    "/{entry_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_time_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a time entry."""
    await service.delete_time_entry(
        db, current_user.tenant_id, entry_id
    )


@router.get("/summary", response_model=TimeEntrySummary)
async def get_summary(
    case_id: uuid.UUID | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get time entry summary with totals and per-case breakdown."""
    return await service.get_summary(
        db,
        current_user.tenant_id,
        case_id=case_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/my/today", response_model=list[TimeEntryResponse])
async def get_my_today(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get today's time entries for the current user (timer widget)."""
    return await service.get_my_today(
        db, current_user.tenant_id, current_user.id
    )
