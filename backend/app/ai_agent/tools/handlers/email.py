"""Email tool handlers — list unlinked emails."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize


async def handle_email_unlinked(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """Get unlinked (not matched to a case) emails."""
    from app.email.sync_service import get_unlinked_emails

    emails, total = await get_unlinked_emails(db, tenant_id, page=page, per_page=per_page)
    return {
        "items": [
            {
                "id": serialize(e.id),
                "subject": e.subject,
                "from_email": e.from_email,
                "from_name": e.from_name,
                "date": serialize(e.date),
                "snippet": (e.body_text or "")[:200] if e.body_text else None,
            }
            for e in emails
        ],
        "total": total,
    }
