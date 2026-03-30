"""Time entry tool handlers."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize
from app.time_entries import service as time_entries_service
from app.time_entries.schemas import TimeEntryCreate


async def handle_time_entry_create(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
    duration_minutes: int,
    entry_date: str | None = None,
    description: str | None = None,
    activity_type: str = "other",
    billable: bool = True,
    hourly_rate: str | None = None,
) -> dict:
    """Log a time entry for a case."""
    data = TimeEntryCreate(
        case_id=uuid.UUID(case_id),
        date=date.fromisoformat(entry_date) if entry_date else date.today(),
        duration_minutes=duration_minutes,
        description=description,
        activity_type=activity_type,
        billable=billable,
        hourly_rate=Decimal(hourly_rate) if hourly_rate else None,
    )
    entry = await time_entries_service.create_time_entry(db, tenant_id, user_id, data)
    return {
        "id": serialize(entry.id),
        "duration_minutes": entry.duration_minutes,
        "activity_type": entry.activity_type,
        "billable": entry.billable,
        "created": True,
    }


async def handle_unbilled_hours(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str | None = None,
) -> dict:
    """List unbilled (not yet invoiced) time entries."""
    entries = await time_entries_service.list_unbilled_time_entries(
        db, tenant_id, case_id=uuid.UUID(case_id) if case_id else None
    )
    return {
        "items": [
            {
                "id": serialize(e.id),
                "case_id": serialize(e.case_id) if hasattr(e, "case_id") else None,
                "case_number": e.case.case_number if hasattr(e, "case") and e.case else None,
                "date": serialize(e.date),
                "duration_minutes": e.duration_minutes,
                "description": e.description,
                "activity_type": e.activity_type,
                "hourly_rate": serialize(e.hourly_rate),
                "billable": e.billable,
            }
            for e in entries
        ],
        "count": len(entries),
    }
