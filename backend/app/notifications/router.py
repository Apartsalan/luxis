"""Notifications router — in-app notifications for deadlines, tasks, and warnings."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.notifications import service
from app.notifications.schemas import NotificationResponse

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    limit: int = 15,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List notifications for the current user, newest first."""
    return await service.list_notifications(
        db, current_user.tenant_id, current_user.id, limit
    )


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get unread notification count."""
    count = await service.get_unread_count(
        db, current_user.tenant_id, current_user.id
    )
    return {"count": count}


@router.put("/{notification_id}/read")
async def mark_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    found = await service.mark_read(
        db, current_user.tenant_id, current_user.id, notification_id
    )
    await db.commit()
    return {"ok": found}


@router.put("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    count = await service.mark_all_read(
        db, current_user.tenant_id, current_user.id
    )
    await db.commit()
    return {"ok": True, "count": count}
