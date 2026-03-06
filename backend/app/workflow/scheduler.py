"""Workflow scheduler — daily + periodic jobs.

Includes:
- Daily task status updates (pending → due → overdue)
- Daily verjaring checks
- Email auto-sync every 5 minutes (all connected accounts)

Uses APScheduler with AsyncIOScheduler, started on FastAPI startup event.
"""

import logging

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
    """Daily job: check all tenants for approaching verjaring and create warning tasks."""
    from app.auth.models import Tenant
    from app.workflow.service import check_verjaring

    logger.info("Scheduler: starting daily verjaring check")
    try:
        async with async_session() as session:
            # Get all active tenants
            result = await session.execute(
                select(Tenant).where(Tenant.is_active.is_(True))
            )
            tenants = list(result.scalars().all())

            total_warnings = 0
            for tenant in tenants:
                warnings = await check_verjaring(session, tenant.id)
                if warnings:
                    for w in warnings:
                        level = "CRITICAL" if w["is_expired"] else "WARNING"
                        days_info = (
                            "VERJAARD" if w["is_expired"]
                            else f"{w['days_remaining']} dagen resterend"
                        )
                        logger.warning(
                            f"Scheduler: [{level}] Verjaring zaak {w['case_number']} "
                            f"(tenant {tenant.name}) — {days_info}"
                        )
                    total_warnings += len(warnings)

            await session.commit()
            logger.info(
                "Scheduler: verjaring check complete"
                " — %d warnings across %d tenants",
                total_warnings,
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
                    logger.error(
                        f"Scheduler: email sync mislukt voor {account.email_address}: {e}"
                    )

            await session.commit()
            logger.info(
                f"Scheduler: email auto-sync klaar — "
                f"{len(accounts)} accounts, {total_new} nieuw, {total_linked} gekoppeld"
            )
    except Exception:
        logger.exception("Scheduler: email auto-sync failed")


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

    # Every 5 minutes: sync all connected email accounts
    scheduler.add_job(
        email_auto_sync,
        IntervalTrigger(minutes=5),
        id="email_auto_sync",
        name="Auto-sync email accounts",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started: daily jobs at 06:00/06:15 UTC, email sync every 5 min"
    )


def stop_scheduler() -> None:
    """Stop the APScheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Workflow scheduler stopped")
