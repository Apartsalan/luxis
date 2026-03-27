"""Email tool handlers — compose/send email, list unlinked emails."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize


async def handle_email_compose(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
) -> dict:
    """Send an email via the configured email provider for a case."""
    from app.email.send_service import send_with_attachment

    result = await send_with_attachment(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        case_id=uuid.UUID(case_id),
        to=to,
        subject=subject,
        body_html=body,
        cc=cc.split(",") if cc else None,
    )
    return serialize(result) if result else {"sent": True}


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
