"""Calendar module service — CRUD operations for calendar events."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar.models import EVENT_TYPE_COLORS, CalendarEvent
from app.calendar.schemas import CalendarEventCreate, CalendarEventUpdate
from app.shared.exceptions import BadRequestError, NotFoundError


async def list_events(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    event_type: str | None = None,
    case_id: uuid.UUID | None = None,
) -> list[CalendarEvent]:
    """List calendar events with optional filters."""
    stmt = (
        select(CalendarEvent)
        .where(
            CalendarEvent.tenant_id == tenant_id,
            CalendarEvent.is_active.is_(True),
        )
        .order_by(CalendarEvent.start_time.asc())
    )

    if date_from:
        stmt = stmt.where(CalendarEvent.start_time >= date_from)
    if date_to:
        stmt = stmt.where(CalendarEvent.start_time <= date_to)
    if event_type:
        stmt = stmt.where(CalendarEvent.event_type == event_type)
    if case_id:
        stmt = stmt.where(CalendarEvent.case_id == case_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
) -> CalendarEvent:
    """Get a single calendar event."""
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.tenant_id == tenant_id,
            CalendarEvent.is_active.is_(True),
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise NotFoundError("Event niet gevonden")
    return event


async def create_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: CalendarEventCreate,
) -> CalendarEvent:
    """Create a new calendar event."""
    if data.end_time <= data.start_time and not data.all_day:
        raise BadRequestError("Eindtijd moet na starttijd liggen")

    color = data.color or EVENT_TYPE_COLORS.get(data.event_type, "#6b7280")

    event = CalendarEvent(
        tenant_id=tenant_id,
        title=data.title,
        description=data.description,
        event_type=data.event_type,
        start_time=data.start_time,
        end_time=data.end_time,
        all_day=data.all_day,
        location=data.location,
        case_id=data.case_id,
        contact_id=data.contact_id,
        color=color,
        reminder_minutes=data.reminder_minutes,
        created_by=user_id,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


async def update_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    data: CalendarEventUpdate,
) -> CalendarEvent:
    """Update a calendar event."""
    event = await get_event(db, tenant_id, event_id)

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(event, field, value)

    # Recalculate color if event_type changed and no custom color
    if "event_type" in update_data and "color" not in update_data:
        event.color = EVENT_TYPE_COLORS.get(event.event_type, "#6b7280")

    # Validate times
    if event.end_time <= event.start_time and not event.all_day:
        raise BadRequestError("Eindtijd moet na starttijd liggen")

    await db.flush()
    await db.refresh(event)
    return event


async def delete_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
) -> None:
    """Soft-delete a calendar event."""
    event = await get_event(db, tenant_id, event_id)
    event.is_active = False
    await db.flush()
