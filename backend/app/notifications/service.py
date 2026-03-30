import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification
from app.notifications.schemas import NotificationCreate


async def create_notification(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: NotificationCreate,
) -> Notification:
    """Create a new notification for a user."""
    notification = Notification(
        tenant_id=tenant_id,
        user_id=user_id,
        type=data.type,
        title=data.title,
        message=data.message,
        case_id=data.case_id,
        case_number=data.case_number,
        task_id=data.task_id,
    )
    db.add(notification)
    await db.flush()
    await db.refresh(notification)
    return notification


async def create_notification_if_not_exists(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: NotificationCreate,
    dedup_hours: int = 24,
) -> Notification | None:
    """Create a notification only if a similar one doesn't already exist within dedup_hours.

    Deduplicates on (tenant_id, user_id, type, case_id) within the time window.
    Returns the notification if created, None if deduplicated.
    """
    cutoff = datetime.now(UTC) - timedelta(hours=dedup_hours)
    stmt = select(Notification).where(
        and_(
            Notification.tenant_id == tenant_id,
            Notification.user_id == user_id,
            Notification.type == data.type,
            (Notification.case_id == data.case_id) if data.case_id
            else Notification.case_id.is_(None),
            Notification.created_at >= cutoff,
        )
    ).limit(1)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return None
    return await create_notification(db, tenant_id, user_id, data)


async def list_notifications(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int = 15,
) -> list[Notification]:
    """List notifications for a user, newest first."""
    stmt = (
        select(Notification)
        .where(
            Notification.tenant_id == tenant_id,
            Notification.user_id == user_id,
        )
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_unread_count(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> int:
    """Count unread notifications for a user."""
    stmt = select(func.count()).select_from(Notification).where(
        Notification.tenant_id == tenant_id,
        Notification.user_id == user_id,
        Notification.is_read == False,  # noqa: E712
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def mark_read(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    notification_id: uuid.UUID,
) -> bool:
    """Mark a single notification as read. Returns True if found."""
    stmt = (
        update(Notification)
        .where(
            Notification.id == notification_id,
            Notification.tenant_id == tenant_id,
            Notification.user_id == user_id,
        )
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount > 0


async def mark_all_read(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> int:
    """Mark all unread notifications as read. Returns count updated."""
    stmt = (
        update(Notification)
        .where(
            Notification.tenant_id == tenant_id,
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount


async def cleanup_old_notifications(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    days: int = 30,
) -> int:
    """Delete read notifications older than `days`. Returns count deleted."""
    from sqlalchemy import delete

    cutoff = datetime.now(UTC) - timedelta(days=days)
    stmt = (
        delete(Notification)
        .where(
            Notification.tenant_id == tenant_id,
            Notification.is_read == True,  # noqa: E712
            Notification.created_at < cutoff,
        )
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount
