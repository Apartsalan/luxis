"""Workflow scheduler — daily jobs for task status updates and verjaring checks.

Uses APScheduler with AsyncIOScheduler, started on FastAPI startup event.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, text

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
                        days_info = "VERJAARD" if w["is_expired"] else f"{w['days_remaining']} dagen resterend"
                        logger.warning(
                            f"Scheduler: [{level}] Verjaring zaak {w['case_number']} "
                            f"(tenant {tenant.name}) — {days_info}"
                        )
                    total_warnings += len(warnings)

            await session.commit()
            logger.info(
                f"Scheduler: verjaring check complete — {total_warnings} warnings across {len(tenants)} tenants"
            )
    except Exception:
        logger.exception("Scheduler: verjaring check failed")


def start_scheduler() -> None:
    """Start the APScheduler with daily jobs."""
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

    scheduler.start()
    logger.info("Workflow scheduler started with daily jobs at 06:00 and 06:15 UTC")


def stop_scheduler() -> None:
    """Stop the APScheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Workflow scheduler stopped")
