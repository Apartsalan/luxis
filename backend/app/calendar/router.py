"""Calendar module endpoints — CRUD for user-created calendar events."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.calendar import service
from app.calendar.schemas import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.shared.exceptions import BadRequestError

router = APIRouter(prefix="/api/calendar/events", tags=["calendar"])


@router.post("/sync")
async def sync_calendar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger Outlook calendar sync."""
    from app.calendar.sync_service import sync_outlook_events
    from app.email.oauth_service import get_email_account

    account = await get_email_account(
        db, current_user.id, current_user.tenant_id, provider="outlook"
    )
    if not account:
        raise BadRequestError("Geen Outlook-account verbonden")

    stats = await sync_outlook_events(
        db, account, current_user.tenant_id, current_user.id
    )
    return stats


@router.get("", response_model=list[CalendarEventResponse])
async def list_events(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    event_type: str | None = Query(default=None),
    case_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List calendar events with optional date range and type filters."""
    return await service.list_events(
        db,
        current_user.tenant_id,
        date_from=date_from,
        date_to=date_to,
        event_type=event_type,
        case_id=case_id,
    )


@router.post(
    "",
    response_model=CalendarEventResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_event(
    data: CalendarEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new calendar event."""
    return await service.create_event(db, current_user.tenant_id, current_user.id, data)


@router.get("/{event_id}", response_model=CalendarEventResponse)
async def get_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single calendar event."""
    return await service.get_event(db, current_user.tenant_id, event_id)


@router.patch("/{event_id}", response_model=CalendarEventResponse)
async def update_event(
    event_id: uuid.UUID,
    data: CalendarEventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a calendar event."""
    return await service.update_event(db, current_user.tenant_id, event_id, data)


@router.delete(
    "/{event_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a calendar event."""
    await service.delete_event(db, current_user.tenant_id, event_id)
