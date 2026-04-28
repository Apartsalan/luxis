"""Workflow scheduler — daily + periodic jobs.

Includes:
- Daily task status updates (pending → due → overdue)
- Daily verjaring checks
- Email auto-sync every 5 minutes (all connected accounts)

Uses APScheduler with AsyncIOScheduler, started on FastAPI startup event.
"""

import logging
import uuid
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.database import async_session

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def daily_task_status_update() -> None:
    """Daily job: mark pending tasks as 'due' or 'overdue' based on due_date."""
    from app.workflow.service import update_task_statuses

    logger.info("Scheduler: starting daily task status update")
    try:
        async with async_session() as session:
            counts = await update_task_statuses(session)
            await session.commit()
            logger.info(
                "Scheduler: task status update complete — "
                f"marked_due={counts['marked_due']}, marked_overdue={counts['marked_overdue']}"
            )
    except Exception:
        logger.exception("Scheduler: task status update failed")


async def daily_verjaring_check() -> None:
    """Daily job: check all tenants for approaching verjaring and create warning tasks.

    Creates workflow tasks at 90, 60, and 30 day thresholds to ensure timely action.
    Deduplicates: won't create a task if one already exists for that case+threshold.
    """
    from app.auth.models import Tenant, User
    from app.notifications.schemas import NotificationCreate
    from app.notifications.service import create_notification_if_not_exists
    from app.workflow.models import WorkflowTask
    from app.workflow.service import check_verjaring

    logger.info("Scheduler: starting daily verjaring check")
    try:
        async with async_session() as session:
            result = await session.execute(select(Tenant).where(Tenant.is_active.is_(True)))
            tenants = list(result.scalars().all())

            total_warnings = 0
            tasks_created = 0
            for tenant in tenants:
                warnings = await check_verjaring(session, tenant.id)
                if warnings:
                    for w in warnings:
                        level = "CRITICAL" if w["is_expired"] else "WARNING"
                        days_info = (
                            "VERJAARD"
                            if w["is_expired"]
                            else f"{w['days_remaining']} dagen resterend"
                        )
                        logger.warning(
                            f"Scheduler: [{level}] Verjaring zaak {w['case_number']} "
                            f"(tenant {tenant.name}) — {days_info}"
                        )

                        # Create warning tasks at 90/60/30 day thresholds
                        days = w["days_remaining"]
                        if days <= 0:
                            threshold = "verjaard"
                        elif days <= 30:
                            threshold = "30_dagen"
                        elif days <= 60:
                            threshold = "60_dagen"
                        elif days <= 90:
                            threshold = "90_dagen"
                        else:
                            continue

                        task_title = (
                            f"VERJARING: {w['case_number']} — "
                            + ("VERJAARD! Direct actie vereist" if days <= 0
                               else f"nog {days} dagen (stuitingshandeling nodig)")
                        )

                        # Dedup: check if task already exists for this case+threshold
                        existing = await session.execute(
                            select(WorkflowTask).where(
                                WorkflowTask.tenant_id == tenant.id,
                                WorkflowTask.case_id == uuid.UUID(w["case_id"]),
                                WorkflowTask.task_type == "verjaring_warning",
                                WorkflowTask.title.contains(
                            threshold if threshold != "verjaard" else "VERJAARD"
                        ),
                                WorkflowTask.status.in_(["pending", "due", "overdue"]),
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        task = WorkflowTask(
                            tenant_id=tenant.id,
                            case_id=uuid.UUID(w["case_id"]),
                            task_type="verjaring_warning",
                            title=task_title,
                            description=(
                                f"Verjaringsdatum: {w['verjaring_date']} (Art. 3:307 BW). "
                                f"Overweeg een stuitingshandeling (aanmaning, dagvaarding)."
                            ),
                            due_date=date.today(),
                            status="overdue" if days <= 0 else "due",
                        )
                        session.add(task)
                        tasks_created += 1

                        # Also create in-app notification for all users
                        users_result = await session.execute(
                            select(User).where(
                                User.tenant_id == tenant.id,
                                User.is_active.is_(True),
                            )
                        )
                        for u in users_result.scalars().all():
                            await create_notification_if_not_exists(
                                session, tenant.id, u.id,
                                NotificationCreate(
                                    type="verjaring_warning",
                                    title=task_title,
                                    message=(
                                        f"Verjaringsdatum: {w['verjaring_date']}. "
                                        f"Overweeg een stuitingshandeling."
                                    ),
                                    case_id=uuid.UUID(w["case_id"]),
                                    case_number=w["case_number"],
                                ),
                            )

                    total_warnings += len(warnings)

            await session.commit()
            logger.info(
                "Scheduler: verjaring check — %d warnings, "
                "%d tasks created across %d tenants",
                total_warnings,
                tasks_created,
                len(tenants),
            )
    except Exception:
        logger.exception("Scheduler: verjaring check failed")


async def email_auto_sync() -> None:
    """Periodic job: sync all connected email accounts every 5 minutes.

    For each connected account:
    1. Fetches new emails from Gmail/Outlook
    2. Matches to dossiers via case number, reference, or contact email
    3. Downloads attachments for new emails
    """
    from app.email.oauth_models import EmailAccount
    from app.email.sync_service import sync_emails_for_account

    logger.info("Scheduler: starting email auto-sync")
    try:
        async with async_session() as session:
            # Get all connected email accounts across all tenants
            result = await session.execute(
                select(EmailAccount).where(
                    EmailAccount.refresh_token_enc.isnot(None),
                )
            )
            accounts = list(result.scalars().all())

            if not accounts:
                logger.debug("Scheduler: geen email accounts verbonden, skip sync")
                return

            total_new = 0
            total_linked = 0
            for account in accounts:
                try:
                    stats = await sync_emails_for_account(
                        session,
                        account,
                        max_results=50,  # Limit per sync cycle
                    )
                    total_new += stats["new"]
                    total_linked += stats["linked"]

                    if stats["new"] > 0:
                        logger.info(
                            f"Scheduler: email sync {account.email_address} — "
                            f"{stats['new']} nieuw, {stats['linked']} gekoppeld"
                        )
                except Exception as e:
                    logger.error(f"Scheduler: email sync mislukt voor {account.email_address}: {e}")

            await session.commit()
            logger.info(
                f"Scheduler: email auto-sync klaar — "
                f"{len(accounts)} accounts, {total_new} nieuw, {total_linked} gekoppeld"
            )
    except Exception:
        logger.exception("Scheduler: email auto-sync failed")


async def ai_intake_detection() -> None:
    """Periodic job: detect + process potential dossier intake emails.

    Runs every 7 minutes (offset from email sync and classification).
    Only active if ANTHROPIC_API_KEY or KIMI_API_KEY is configured.
    """
    from app.ai_agent.intake_service import detect_intake_emails, process_detected_intakes
    from app.auth.models import Tenant

    logger.info("Scheduler: starting AI intake detection")
    try:
        async with async_session() as session:
            result = await session.execute(select(Tenant).where(Tenant.is_active.is_(True)))
            tenants = list(result.scalars().all())

            total_detected = 0
            total_processed = 0
            for tenant in tenants:
                try:
                    detected = await detect_intake_emails(session, tenant.id)
                    total_detected += detected
                    processed = await process_detected_intakes(session, tenant.id)
                    total_processed += processed
                except Exception as e:
                    logger.error(
                        "Scheduler: AI intake failed for tenant %s: %s",
                        tenant.name,
                        e,
                    )

            await session.commit()
            if total_detected > 0 or total_processed > 0:
                logger.info(
                    "Scheduler: AI intake complete — %d detected, %d processed",
                    total_detected,
                    total_processed,
                )
    except Exception:
        logger.exception("Scheduler: AI intake detection failed")


async def ai_email_classification() -> None:
    """Periodic job: classify unclassified inbound emails on incasso cases.

    Runs every 6 minutes (offset from email sync).
    Only active if ANTHROPIC_API_KEY is configured.
    """
    from app.ai_agent.service import classify_new_emails
    from app.auth.models import Tenant

    logger.info("Scheduler: starting AI email classification")
    try:
        async with async_session() as session:
            result = await session.execute(select(Tenant).where(Tenant.is_active.is_(True)))
            tenants = list(result.scalars().all())

            total_classified = 0
            for tenant in tenants:
                try:
                    count = await classify_new_emails(session, tenant.id)
                    total_classified += count
                except Exception as e:
                    logger.error(
                        "Scheduler: AI classification failed for tenant %s: %s",
                        tenant.name,
                        e,
                    )

            await session.commit()
            if total_classified > 0:
                logger.info(
                    "Scheduler: AI classification complete — %d emails classified",
                    total_classified,
                )
    except Exception:
        logger.exception("Scheduler: AI email classification failed")


async def calendar_auto_sync() -> None:
    """Periodic job: sync Outlook calendars every 15 minutes.

    For each connected Outlook account, syncs events from Outlook to Luxis
    within a 90-day window (45 days back + 45 days forward).
    """
    from app.calendar.sync_service import sync_outlook_events
    from app.email.oauth_models import EmailAccount

    logger.info("Scheduler: starting calendar auto-sync")
    try:
        async with async_session() as session:
            result = await session.execute(
                select(EmailAccount).where(
                    EmailAccount.provider == "outlook",
                    EmailAccount.refresh_token_enc.isnot(None),
                )
            )
            accounts = list(result.scalars().all())

            if not accounts:
                logger.debug("Scheduler: geen Outlook accounts voor calendar sync")
                return

            total_created = 0
            total_updated = 0
            for account in accounts:
                try:
                    stats = await sync_outlook_events(
                        session,
                        account,
                        account.tenant_id,
                        account.user_id,
                    )
                    total_created += stats["created"]
                    total_updated += stats["updated"]
                except Exception as e:
                    logger.error(
                        "Scheduler: calendar sync failed for %s: %s",
                        account.email_address,
                        e,
                    )

            await session.commit()
            if total_created > 0 or total_updated > 0:
                logger.info(
                    "Scheduler: calendar sync done — %d created, %d updated",
                    total_created,
                    total_updated,
                )
    except Exception:
        logger.exception("Scheduler: calendar auto-sync failed")


async def followup_scan() -> None:
    """Periodic job: scan incasso cases for follow-up recommendations.

    Runs every 30 minutes. Creates recommendations for cases that have been
    in a pipeline step long enough (deadline_status = orange or red).
    No AI/LLM needed — purely rules-based on pipeline step min_wait_days.
    """
    from app.ai_agent.followup_service import scan_for_followups
    from app.auth.models import Tenant

    logger.info("Scheduler: starting follow-up scan")
    try:
        async with async_session() as session:
            result = await session.execute(select(Tenant).where(Tenant.is_active.is_(True)))
            tenants = list(result.scalars().all())

            total_created = 0
            for tenant in tenants:
                try:
                    count = await scan_for_followups(session, tenant.id)
                    total_created += count
                except Exception as e:
                    logger.error(
                        "Scheduler: follow-up scan failed for tenant %s: %s",
                        tenant.name,
                        e,
                    )

            await session.commit()
            if total_created > 0:
                logger.info(
                    "Scheduler: follow-up scan complete — %d nieuwe aanbevelingen",
                    total_created,
                )
    except Exception:
        logger.exception("Scheduler: follow-up scan failed")


async def daily_deadline_notifications() -> None:
    """Daily job: create in-app notifications for approaching/overdue deadlines.

    Checks calendar events of type 'deadline' or 'hearing' within 3 days,
    and creates notifications. Also creates notifications for overdue tasks.
    Deduplicates within 24 hours.
    """
    from app.auth.models import Tenant, User
    from app.calendar.models import CalendarEvent
    from app.notifications.schemas import NotificationCreate
    from app.notifications.service import create_notification_if_not_exists
    from app.workflow.models import WorkflowTask

    logger.info("Scheduler: starting deadline notification check")
    try:
        async with async_session() as session:
            result = await session.execute(select(Tenant).where(Tenant.is_active.is_(True)))
            tenants = list(result.scalars().all())

            total_created = 0
            for tenant in tenants:
                # Get all active users for this tenant
                users_result = await session.execute(
                    select(User).where(User.tenant_id == tenant.id, User.is_active.is_(True))
                )
                users = list(users_result.scalars().all())
                if not users:
                    continue

                today = date.today()
                from datetime import timedelta
                three_days = today + timedelta(days=3)

                # 1. Calendar events approaching (within 3 days)
                from datetime import timedelta as td

                from sqlalchemy import Date, cast

                events_result = await session.execute(
                    select(CalendarEvent).where(
                        CalendarEvent.tenant_id == tenant.id,
                        CalendarEvent.is_active.is_(True),
                        CalendarEvent.event_type.in_(
                            ["deadline", "hearing"]
                        ),
                        cast(CalendarEvent.start_time, Date) >= today,
                        cast(CalendarEvent.start_time, Date) <= three_days,
                    )
                )
                events = list(events_result.scalars().all())

                for event in events:
                    event_date = event.start_time.date()
                    days_until = (event_date - today).days
                    if days_until == 0:
                        label = "vandaag"
                    elif days_until == 1:
                        label = "over 1 dag"
                    else:
                        label = f"over {days_until} dagen"
                    notif_type = (
                        "deadline_overdue"
                        if days_until == 0
                        else "deadline_approaching"
                    )
                    kind = (
                        "Zitting"
                        if event.event_type == "hearing"
                        else "Deadline"
                    )

                    for user in users:
                        created = await create_notification_if_not_exists(
                            session, tenant.id, user.id,
                            NotificationCreate(
                                type=notif_type,
                                title=f"{event.title} — {label}",
                                message=(
                                    f"{kind} op "
                                    f"{event_date.strftime('%d-%m-%Y')}"
                                ),
                                case_id=event.case_id,
                            ),
                        )
                        if created:
                            total_created += 1

                # 2. Overdue calendar events (past, within 3 days)
                three_ago = today - td(days=3)
                overdue_result = await session.execute(
                    select(CalendarEvent).where(
                        CalendarEvent.tenant_id == tenant.id,
                        CalendarEvent.is_active.is_(True),
                        CalendarEvent.event_type.in_(
                            ["deadline", "hearing"]
                        ),
                        cast(CalendarEvent.start_time, Date) < today,
                        cast(CalendarEvent.start_time, Date) >= three_ago,
                    )
                )
                overdue_events = list(overdue_result.scalars().all())

                for event in overdue_events:
                    evt_date = event.start_time.date()
                    for user in users:
                        created = await create_notification_if_not_exists(
                            session, tenant.id, user.id,
                            NotificationCreate(
                                type="deadline_overdue",
                                title=f"VERLOPEN: {event.title}",
                                message=(
                                    f"Deadline was op "
                                    f"{evt_date.strftime('%d-%m-%Y')}"
                                ),
                                case_id=event.case_id,
                            ),
                        )
                        if created:
                            total_created += 1

                # 3. Overdue workflow tasks → notification
                overdue_tasks = await session.execute(
                    select(WorkflowTask).where(
                        WorkflowTask.tenant_id == tenant.id,
                        WorkflowTask.status == "overdue",
                        WorkflowTask.is_active.is_(True),
                    )
                )
                for task in overdue_tasks.scalars().all():
                    target_user = task.assigned_to_id or (users[0].id if users else None)
                    if not target_user:
                        continue
                    created = await create_notification_if_not_exists(
                        session, tenant.id, target_user,
                        NotificationCreate(
                            type="deadline_overdue",
                            title=f"Taak te laat: {task.title}",
                            message=f"Deadline was {task.due_date.strftime('%d-%m-%Y')}",
                            case_id=task.case_id,
                        ),
                    )
                    if created:
                        total_created += 1

            await session.commit()
            if total_created > 0:
                logger.info(
                    "Scheduler: deadline notifications — %d notificaties aangemaakt",
                    total_created,
                )
    except Exception:
        logger.exception("Scheduler: deadline notification check failed")


async def daily_installment_overdue_check() -> None:
    """Daily job: mark overdue payment arrangement installments.

    Finds pending installments with due_date < today and marks them as overdue.
    """
    from app.collections.service import mark_overdue_installments

    logger.info("Scheduler: starting installment overdue check")
    try:
        async with async_session() as session:
            count = await mark_overdue_installments(session)
            await session.commit()
            if count > 0:
                logger.info(
                    "Scheduler: installment overdue — %d termijnen achterstallig",
                    count,
                )
    except Exception:
        logger.exception("Scheduler: installment overdue check failed")


def start_scheduler() -> None:
    """Start the APScheduler with daily + periodic jobs."""
    if scheduler.running:
        return

    # Daily at 06:00 UTC: update task statuses (pending → due → overdue)
    scheduler.add_job(
        daily_task_status_update,
        CronTrigger(hour=6, minute=0),
        id="daily_task_status_update",
        name="Update workflow task statuses",
        replace_existing=True,
    )

    # Daily at 06:15 UTC: check verjaring across all tenants
    scheduler.add_job(
        daily_verjaring_check,
        CronTrigger(hour=6, minute=15),
        id="daily_verjaring_check",
        name="Check verjaring for all tenants",
        replace_existing=True,
    )

    # Daily at 06:20 UTC: deadline notifications (calendar events + overdue tasks)
    scheduler.add_job(
        daily_deadline_notifications,
        CronTrigger(hour=6, minute=20),
        id="daily_deadline_notifications",
        name="Create deadline notifications",
        replace_existing=True,
    )

    # Daily at 06:30 UTC: mark overdue installments
    scheduler.add_job(
        daily_installment_overdue_check,
        CronTrigger(hour=6, minute=30),
        id="daily_installment_overdue_check",
        name="Mark overdue payment arrangement installments",
        replace_existing=True,
    )

    # Every 5 minutes: sync all connected email accounts
    scheduler.add_job(
        email_auto_sync,
        IntervalTrigger(minutes=5),
        id="email_auto_sync",
        name="Auto-sync email accounts",
        replace_existing=True,
    )

    # Every 6 minutes: AI email classification (only if API key configured)
    from app.config import settings as app_settings

    ai_enabled = bool(app_settings.anthropic_api_key)
    if ai_enabled:
        scheduler.add_job(
            ai_email_classification,
            IntervalTrigger(minutes=6),
            id="ai_email_classification",
            name="AI email classification",
            replace_existing=True,
        )

    # Every 7 minutes: AI intake detection + processing
    intake_enabled = ai_enabled or bool(app_settings.kimi_api_key)
    if intake_enabled:
        scheduler.add_job(
            ai_intake_detection,
            IntervalTrigger(minutes=7),
            id="ai_intake_detection",
            name="AI intake detection",
            replace_existing=True,
        )

    # Every 15 minutes: sync Outlook calendars
    scheduler.add_job(
        calendar_auto_sync,
        IntervalTrigger(minutes=15),
        id="calendar_auto_sync",
        name="Auto-sync Outlook calendars",
        replace_existing=True,
    )

    # Every 30 minutes: follow-up recommendation scan (rules-based, no AI needed)
    scheduler.add_job(
        followup_scan,
        IntervalTrigger(minutes=30),
        id="followup_scan",
        name="Follow-up recommendation scan",
        replace_existing=True,
    )

    # Register orchestrator event handlers
    from app.ai_agent.orchestrator import register_handlers

    register_handlers()

    scheduler.start()
    ai_status = (
        "AI classification every 6 min" if ai_enabled else "AI classification OFF (no API key)"
    )
    intake_status = "intake detection every 7 min" if intake_enabled else "intake OFF (no AI key)"
    logger.info(
        "Scheduler started: daily jobs at 06:00/06:15 UTC, email sync every 5 min, %s, %s",
        ai_status,
        intake_status,
    )


def stop_scheduler() -> None:
    """Stop the APScheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Workflow scheduler stopped")
