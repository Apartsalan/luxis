"""Unified timeline service — merges all case activity sources into one chronological feed."""

import uuid
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cases.models import Case, CaseActivity, CaseFile
from app.collections.models import Claim, Payment
from app.documents.models import GeneratedDocument
from app.email.synced_email_models import SyncedEmail
from app.time_entries.models import TimeEntry


async def get_case_timeline(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    *,
    event_type: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[dict], int]:
    """Get unified timeline for a case.

    Returns a list of timeline items sorted by date (newest first) and total count.
    Each item has: id, type, title, description, date, metadata.
    """
    items: list[dict] = []

    # 1. Case activities (notes, status changes, etc.)
    if not event_type or event_type == "activity":
        result = await db.execute(
            select(CaseActivity)
            .where(CaseActivity.case_id == case_id, CaseActivity.tenant_id == tenant_id)
            .options(selectinload(CaseActivity.user))
        )
        for a in result.scalars().all():
            items.append({
                "id": str(a.id),
                "type": "activity",
                "subtype": a.activity_type,
                "title": a.title or a.activity_type.replace("_", " ").title(),
                "description": a.description,
                "date": a.created_at.isoformat(),
                "metadata": {
                    "user": a.user.full_name if a.user else None,
                },
            })

    # 2. Synced emails
    if not event_type or event_type == "email":
        result = await db.execute(
            select(SyncedEmail)
            .where(SyncedEmail.case_id == case_id, SyncedEmail.tenant_id == tenant_id)
        )
        for e in result.scalars().all():
            direction = "Ontvangen" if e.direction == "inbound" else "Verzonden"
            items.append({
                "id": str(e.id),
                "type": "email",
                "subtype": e.direction,
                "title": f"{direction}: {e.subject}",
                "description": e.snippet[:200] if e.snippet else None,
                "date": e.email_date.isoformat() if e.email_date else e.created_at.isoformat(),
                "metadata": {
                    "from": e.from_name or e.from_email,
                    "direction": e.direction,
                    "has_attachments": e.has_attachments,
                },
            })

    # 3. Payments
    if not event_type or event_type == "payment":
        result = await db.execute(
            select(Payment)
            .where(Payment.case_id == case_id, Payment.tenant_id == tenant_id)
        )
        for p in result.scalars().all():
            items.append({
                "id": str(p.id),
                "type": "payment",
                "subtype": "payment",
                "title": f"Betaling: €{p.amount:.2f}",
                "description": p.description,
                "date": datetime.combine(p.payment_date, datetime.min.time()).isoformat() if p.payment_date else p.created_at.isoformat(),
                "metadata": {
                    "amount": str(p.amount),
                },
            })

    # 4. Generated documents
    if not event_type or event_type == "document":
        result = await db.execute(
            select(GeneratedDocument)
            .where(GeneratedDocument.case_id == case_id, GeneratedDocument.tenant_id == tenant_id)
        )
        for d in result.scalars().all():
            items.append({
                "id": str(d.id),
                "type": "document",
                "subtype": d.template_type if hasattr(d, "template_type") else "document",
                "title": d.title or "Document",
                "description": None,
                "date": d.created_at.isoformat(),
                "metadata": {},
            })

    # 5. Time entries
    if not event_type or event_type == "time_entry":
        result = await db.execute(
            select(TimeEntry)
            .where(TimeEntry.case_id == case_id, TimeEntry.tenant_id == tenant_id)
            .options(selectinload(TimeEntry.user))
        )
        for t in result.scalars().all():
            minutes = t.duration_seconds // 60 if t.duration_seconds else 0
            hours = minutes // 60
            mins = minutes % 60
            items.append({
                "id": str(t.id),
                "type": "time_entry",
                "subtype": "time",
                "title": f"Tijdregistratie: {hours}:{mins:02d}",
                "description": t.description,
                "date": datetime.combine(t.entry_date, datetime.min.time()).isoformat() if t.entry_date else t.created_at.isoformat(),
                "metadata": {
                    "user": t.user.full_name if t.user else None,
                    "duration_minutes": minutes,
                },
            })

    # 6. Uploaded case files
    if not event_type or event_type == "file":
        result = await db.execute(
            select(CaseFile)
            .where(CaseFile.case_id == case_id, CaseFile.tenant_id == tenant_id, CaseFile.is_active == True)  # noqa: E712
            .options(selectinload(CaseFile.uploader))
        )
        for f in result.scalars().all():
            items.append({
                "id": str(f.id),
                "type": "file",
                "subtype": f.content_type or "file",
                "title": f"Bestand: {f.original_filename}",
                "description": f.description,
                "date": f.created_at.isoformat(),
                "metadata": {
                    "filename": f.original_filename,
                    "file_size": f.file_size,
                    "uploaded_by": f.uploader.full_name if f.uploader else None,
                },
            })

    # Sort all items by date (newest first)
    items.sort(key=lambda x: x["date"], reverse=True)

    # Pagination
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    return page_items, total
