"""Time entries service — CRUD and aggregations for time tracking."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.exceptions import NotFoundError
from app.time_entries.models import TimeEntry
from app.time_entries.schemas import (
    CaseTimeSummary,
    TimeEntryCreate,
    TimeEntrySummary,
    TimeEntryUpdate,
)

# ── CRUD ──────────────────────────────────────────────────────────────────


async def list_time_entries(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    case_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    billable: bool | None = None,
    invoiced: bool | None = None,
) -> list[TimeEntry]:
    """List time entries with optional filters."""
    query = select(TimeEntry).where(
        TimeEntry.tenant_id == tenant_id,
    )
    if case_id:
        query = query.where(TimeEntry.case_id == case_id)
    if user_id:
        query = query.where(TimeEntry.user_id == user_id)
    if date_from:
        query = query.where(TimeEntry.date >= date_from)
    if date_to:
        query = query.where(TimeEntry.date <= date_to)
    if billable is not None:
        query = query.where(TimeEntry.billable.is_(billable))
    if invoiced is not None:
        query = query.where(TimeEntry.invoiced.is_(invoiced))

    query = query.order_by(TimeEntry.date.desc(), TimeEntry.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def list_unbilled_time_entries(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    case_id: uuid.UUID | None = None,
) -> list[TimeEntry]:
    """Get all billable, uninvoiced time entries (ready to be billed)."""
    return await list_time_entries(
        db, tenant_id,
        case_id=case_id,
        billable=True,
        invoiced=False,
    )


async def get_time_entry(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entry_id: uuid.UUID,
) -> TimeEntry:
    """Get a single time entry by ID."""
    result = await db.execute(
        select(TimeEntry).where(
            TimeEntry.id == entry_id,
            TimeEntry.tenant_id == tenant_id,
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise NotFoundError("Tijdregistratie niet gevonden")
    return entry


async def create_time_entry(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TimeEntryCreate,
) -> TimeEntry:
    """Create a new time entry."""
    entry = TimeEntry(
        tenant_id=tenant_id,
        user_id=user_id,
        **data.model_dump(),
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def update_time_entry(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entry_id: uuid.UUID,
    data: TimeEntryUpdate,
) -> TimeEntry:
    """Update an existing time entry."""
    entry = await get_time_entry(db, tenant_id, entry_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    await db.flush()
    await db.refresh(entry)
    return entry


async def delete_time_entry(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entry_id: uuid.UUID,
) -> None:
    """Hard-delete a time entry (no soft-delete needed for time tracking)."""
    entry = await get_time_entry(db, tenant_id, entry_id)
    await db.delete(entry)
    await db.flush()


# ── Aggregations ──────────────────────────────────────────────────────────


async def get_summary(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    case_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> TimeEntrySummary:
    """Calculate time entry summary with totals and per-case breakdown."""
    entries = await list_time_entries(
        db, tenant_id,
        case_id=case_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )

    total_minutes = 0
    billable_minutes = 0
    total_amount = Decimal("0")

    # Group by case
    case_map: dict[uuid.UUID, dict] = {}

    for e in entries:
        total_minutes += e.duration_minutes
        if e.billable:
            billable_minutes += e.duration_minutes
            if e.hourly_rate:
                hours = Decimal(str(e.duration_minutes)) / Decimal("60")
                total_amount += hours * e.hourly_rate

        cid = e.case_id
        if cid not in case_map:
            case_map[cid] = {
                "case_id": cid,
                "case_number": e.case.case_number if e.case else "",
                "total_minutes": 0,
                "billable_minutes": 0,
                "total_amount": Decimal("0"),
            }
        case_map[cid]["total_minutes"] += e.duration_minutes
        if e.billable:
            case_map[cid]["billable_minutes"] += e.duration_minutes
            if e.hourly_rate:
                hours = Decimal(str(e.duration_minutes)) / Decimal("60")
                case_map[cid]["total_amount"] += hours * e.hourly_rate

    per_case = [
        CaseTimeSummary(**data)
        for data in sorted(case_map.values(), key=lambda d: d["total_minutes"], reverse=True)
    ]

    return TimeEntrySummary(
        total_minutes=total_minutes,
        billable_minutes=billable_minutes,
        non_billable_minutes=total_minutes - billable_minutes,
        total_amount=total_amount,
        per_case=per_case,
    )


async def get_my_today(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[TimeEntry]:
    """Get today's time entries for the current user (for timer widget)."""
    return await list_time_entries(
        db, tenant_id,
        user_id=user_id,
        date_from=date.today(),
        date_to=date.today(),
    )
