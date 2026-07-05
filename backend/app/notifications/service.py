import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification
from app.notifications.schemas import NotificationCreate

# Notification type constants — keep in sync with frontend CaseActionFeed
NOTIF_EMAIL_RECEIVED = "email_received"
NOTIF_AI_DRAFT_READY = "ai_draft_ready"
NOTIF_CLASSIFICATION_DONE = "classification_done"
NOTIF_DEADLINE_OVERDUE = "deadline_overdue"
NOTIF_INVOICE_OVERDUE = "invoice_overdue"  # CONN-1: eigen declaratie vervallen
NOTIF_TRUST_APPROVAL_PENDING = "trust_approval_pending"  # CONN-2: vier-ogen wacht
NOTIF_TRUST_STALE = "trust_stale"  # FIN-2: derdengelden staan te lang stil


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

    Deduplicates on (tenant_id, user_id, type, case_id) — and on task_id when set,
    so different tasks on the same case don't collapse into one notification.
    Returns the notification if created, None if deduplicated.
    """
    cutoff = datetime.now(UTC) - timedelta(hours=dedup_hours)
    where_clauses = [
        Notification.tenant_id == tenant_id,
        Notification.user_id == user_id,
        Notification.type == data.type,
        Notification.created_at >= cutoff,
    ]
    if data.case_id:
        where_clauses.append(Notification.case_id == data.case_id)
    else:
        where_clauses.append(Notification.case_id.is_(None))
    if data.task_id:
        where_clauses.append(Notification.task_id == data.task_id)
    stmt = select(Notification).where(and_(*where_clauses)).limit(1)
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


# FEAT-AI-05: allowed snooze durations (hours). 0 = unsnooze (clear). Whitelisted
# server-side so the client can only pick a fixed interval.
SNOOZE_HOURS = frozenset({0, 24, 72, 168})


async def snooze_notification(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    notification_id: uuid.UUID,
    hours: int,
) -> bool:
    """Snooze a notification for `hours` (server-computed), or unsnooze when hours==0.

    Snoozing keeps the item unread (is_read=False) so it stays actionable — it is
    only hidden from the "Wachtend" filter until snoozed_until passes. Returns True
    if the notification was found.
    """
    if hours not in SNOOZE_HOURS:
        raise ValueError(f"Ongeldige snooze-duur: {hours}")
    snoozed_until = (
        datetime.now(UTC) + timedelta(hours=hours) if hours > 0 else None
    )
    stmt = (
        update(Notification)
        .where(
            Notification.id == notification_id,
            Notification.tenant_id == tenant_id,
            Notification.user_id == user_id,
        )
        .values(snoozed_until=snoozed_until, is_read=False)
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


async def _notify_all_tenant_users(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: NotificationCreate,
    *,
    dedup_minutes: int = 60,
) -> int:
    """Create the same notification for every active user in the tenant, deduped per user.

    Returns the number of new notifications actually created.
    """
    from app.auth.models import User

    users_result = await db.execute(
        select(User.id).where(User.tenant_id == tenant_id, User.is_active.is_(True))
    )
    user_ids = [row[0] for row in users_result.all()]
    if not user_ids:
        return 0

    cutoff = datetime.now(UTC) - timedelta(minutes=dedup_minutes)
    created = 0
    for user_id in user_ids:
        stmt = select(Notification.id).where(
            and_(
                Notification.tenant_id == tenant_id,
                Notification.user_id == user_id,
                Notification.type == data.type,
                (Notification.case_id == data.case_id) if data.case_id
                else Notification.case_id.is_(None),
                Notification.created_at >= cutoff,
                # Dedup on title too so different drafts/emails don't collide
                Notification.title == data.title,
            )
        ).limit(1)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            continue
        await create_notification(db, tenant_id, user_id, data)
        created += 1
    return created


async def create_email_received_notification(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    case_number: str | None,
    from_label: str,
    subject: str,
) -> int:
    """Notify all tenant users that a new inbound email was linked to a case.

    Deduped per (user, case, subject) within 60 minutes — protects against
    duplicate sync runs creating duplicate notifications for the same message.
    """
    subject_clean = (subject or "(geen onderwerp)").strip()[:120]
    title = f"Nieuwe email: {subject_clean}"
    message = f"Van: {from_label}"
    return await _notify_all_tenant_users(
        db,
        tenant_id,
        NotificationCreate(
            type=NOTIF_EMAIL_RECEIVED,
            title=title,
            message=message,
            case_id=case_id,
            case_number=case_number,
        ),
        dedup_minutes=60,
    )


async def create_draft_ready_notification(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    case_number: str | None,
    intent: str,
    preview: str,
) -> int:
    """Notify all tenant users that an AI draft is ready for review.

    Deduped per (user, case, intent) within 5 minutes — protects against
    accidental double-generation.
    """
    intent_label = {
        "next_step": "volgende stap",
        "reply_to_email": "antwoord op email",
        "free_compose": "vrij bericht",
    }.get(intent, intent)
    title = f"AI-concept klaar — {intent_label}"
    preview_clean = (preview or "").strip().replace("\n", " ")[:200]
    return await _notify_all_tenant_users(
        db,
        tenant_id,
        NotificationCreate(
            type=NOTIF_AI_DRAFT_READY,
            title=title,
            message=preview_clean,
            case_id=case_id,
            case_number=case_number,
        ),
        dedup_minutes=5,
    )


async def create_classification_done_notification(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    case_number: str | None,
    category: str,
    sentiment: str | None,
    from_label: str,
) -> int:
    """Notify all tenant users that an inbound email was classified by AI.

    Deduped per (user, case, category) within 10 minutes.
    """
    tone_label = sentiment or "neutraal"
    title = f"Antwoord geclassificeerd — toon: {tone_label}"
    message = f"Van: {from_label} • Categorie: {category}"
    return await _notify_all_tenant_users(
        db,
        tenant_id,
        NotificationCreate(
            type=NOTIF_CLASSIFICATION_DONE,
            title=title,
            message=message,
            case_id=case_id,
            case_number=case_number,
        ),
        dedup_minutes=10,
    )


async def create_invoice_overdue_notification(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    invoice_number: str,
    amount,
    case_id: uuid.UUID | None = None,
    case_number: str | None = None,
) -> int:
    """CONN-1: notify all tenant users that an own invoice (declaratie) is overdue.

    Deduped per (user, case, title) within 24h. The overdue job only flips
    'sent' → 'overdue' once per invoice, so in practice this fires a single
    time; the dedup window only guards against a double job-run.
    """
    title = f"Factuur te laat: {invoice_number}"
    message = f"Vervaldatum verstreken — openstaand € {amount}"
    return await _notify_all_tenant_users(
        db,
        tenant_id,
        NotificationCreate(
            type=NOTIF_INVOICE_OVERDUE,
            title=title,
            message=message,
            case_id=case_id,
            case_number=case_number,
        ),
        dedup_minutes=24 * 60,
    )


async def create_trust_approval_pending_notification(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    creator_id: uuid.UUID,
    transaction_type: str,
    amount,
    case_id: uuid.UUID | None = None,
    case_number: str | None = None,
) -> int:
    """CONN-2: notify active tenant users — EXCEPT the creator — that a trust
    transaction (uitbetaling/verrekening) is waiting for four-eyes approval.

    Returns 0 in a single-user tenant (no second approver to alert), which is
    correct: self-approval is allowed there (H14) and there is no one to notify.
    """
    from app.auth.models import User

    label = {
        "disbursement": "Uitbetaling",
        "offset_to_invoice": "Verrekening",
    }.get(transaction_type, "Derdengelden-transactie")
    title = f"{label} wacht op goedkeuring"
    message = f"Bedrag € {amount} — controleer en keur goed (vier-ogen)"

    users_result = await db.execute(
        select(User.id).where(
            User.tenant_id == tenant_id,
            User.is_active.is_(True),
            User.id != creator_id,
        )
    )
    created = 0
    for (user_id,) in users_result.all():
        await create_notification(
            db,
            tenant_id,
            user_id,
            NotificationCreate(
                type=NOTIF_TRUST_APPROVAL_PENDING,
                title=title,
                message=message,
                case_id=case_id,
                case_number=case_number,
            ),
        )
        created += 1
    return created


async def create_trust_stale_notification(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    balance,
    days_stale: int,
    dedup_days: int,
    case_id: uuid.UUID | None = None,
    case_number: str | None = None,
) -> int:
    """FIN-2: notify all tenant users that a case's trust balance has sat idle.

    Voda art. 6.19: client money must be forwarded "zodra de gelegenheid zich
    voordoet". Deduped per (user, case, title) within `dedup_days` days so the
    daily job nags at most once per window, not every morning.
    """
    title = f"Derdengelden staan stil: dossier {case_number or ''}".strip()
    message = (
        f"€ {balance} staat al {days_stale} dagen op de stichtingsrekening — "
        f"wikkel het dossier af (verrekenen of uitbetalen)."
    )
    return await _notify_all_tenant_users(
        db,
        tenant_id,
        NotificationCreate(
            type=NOTIF_TRUST_STALE,
            title=title,
            message=message,
            case_id=case_id,
            case_number=case_number,
        ),
        dedup_minutes=dedup_days * 24 * 60,
    )


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
