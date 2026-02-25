"""Notifications stub router — returns empty responses to prevent 404 errors.

This is a placeholder until a full notification system is implemented.
The frontend already calls these endpoints on every page load.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.auth.models import User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    limit: int = 15,
    current_user: User = Depends(get_current_user),
):
    """Return empty notification list (stub)."""
    return []


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
):
    """Return zero unread count (stub)."""
    return {"count": 0}


@router.put("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
):
    """Mark notification as read (stub)."""
    return {"ok": True}


@router.put("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read (stub)."""
    return {"ok": True}
