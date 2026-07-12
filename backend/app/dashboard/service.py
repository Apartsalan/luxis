"""Dashboard module service — aggregation queries for KPIs and activity."""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseActivity
from app.cases.schemas import TERMINAL_STATUSES
from app.relations.models import Contact

# Marker die de BaseNet-import op elke geschreven rij zet (contacts.notes,
# cases.debtor_notes). Zie scripts/basenet/import_basenet.py::_MARKER.
IMPORT_MARKER = "[BaseNet-import]"

# S203 #2: dagelijkse achtergrondtaken waarvan een uitblijvende run juridisch/
# operationeel gevaarlijk is. job_id → leesbare naam. Een run ouder dan 25 uur
# (24u interval + speling) telt als 'staat stil'.
_CRITICAL_DAILY_JOBS = {
    "daily_verjaring_check": "Verjaringscontrole",
    "daily_task_status_update": "Taakstatus-bijwerken",
    "daily_deadline_notifications": "Deadline-meldingen",
    "daily_installment_overdue_check": "Termijn-achterstandcontrole",
    "daily_invoice_overdue_check": "Factuur-achterstandcontrole",
}
_STALE_AFTER = timedelta(hours=25)


async def get_scheduler_alerts(db: AsyncSession) -> list[str]:
    """Signaleer kritieke dagelijkse jobs die zijn gestopt met draaien.

    Alleen alarm als een job ééns heeft gedraaid en zijn laatste run > 25u oud is
    (een job die na een verse deploy nog niet aan de beurt was, heeft geen rij en
    geeft dus geen vals alarm). Globaal, niet tenant-gebonden — de scheduler draait
    installatiebreed.
    """
    from app.settings.models import SchedulerHeartbeat

    rows = (await db.execute(select(SchedulerHeartbeat))).scalars().all()
    by_id = {r.job_id: r for r in rows}
    now = datetime.now(UTC)
    alerts: list[str] = []
    for job_id, label in _CRITICAL_DAILY_JOBS.items():
        row = by_id.get(job_id)
        if row is None or row.last_run_at is None:
            continue  # nog nooit gedraaid → geen vals alarm na verse deploy
        age = now - row.last_run_at
        if age > _STALE_AFTER:
            hours = int(age.total_seconds() // 3600)
            alerts.append(f"{label} draaide voor het laatst {hours} uur geleden.")
            continue
        # S205: 'draait maar faalt intern' — de job draaide recent, maar slikte een
        # exceptie. De dead-man-switch hierboven ziet dat niet (last_run_at is vers).
        # Alarmeer als er een recente fout op de heartbeat staat (< 25u).
        if row.last_error and row.last_error_at is not None:
            error_age = now - row.last_error_at
            if error_age <= _STALE_AFTER:
                alerts.append(f"{label} faalde bij de laatste run: {row.last_error}")
    return alerts


async def get_dashboard_summary(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> dict:
    """Build the main dashboard KPI summary.

    Returns counts, totals, and breakdowns for the tenant's cases.
    """
    # Total active cases. S175b: 'actief' = lopend werk, dus zonder terminale
    # dossiers — is_active betekent sinds de BaseNet-import alleen 'zichtbaar'
    # (het hele 607-zaken-archief staat op is_active=True als naslagwerk).
    result = await db.execute(
        select(func.count(Case.id)).where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.status.notin_(TERMINAL_STATUSES),
        )
    )
    total_active_cases = result.scalar() or 0

    # Total contacts
    result = await db.execute(
        select(func.count(Contact.id)).where(
            Contact.tenant_id == tenant_id,
            Contact.is_active.is_(True),
        )
    )
    total_contacts = result.scalar() or 0

    # Total principal and paid (from open cases — archief telt niet mee, S175b)
    result = await db.execute(
        select(
            func.coalesce(func.sum(Case.total_principal), 0),
            func.coalesce(func.sum(Case.total_paid), 0),
        ).where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.status.notin_(TERMINAL_STATUSES),
        )
    )
    row = result.one()
    total_principal = Decimal(str(row[0]))
    total_paid = Decimal(str(row[1]))
    # AUDIT-H4: 'openstaand' must include interest + BIK (same grand_total logic
    # as the case detail), not just principal − paid.
    from app.collections.service import get_portfolio_outstanding

    total_outstanding = await get_portfolio_outstanding(db, tenant_id)

    # Cases by status — werkvoorraad-verdeling, dus zonder terminale dossiers
    # (dat zou met 607 zaken elke andere balk in het niet laten vallen, S175b).
    result = await db.execute(
        select(Case.status, func.count(Case.id))
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.status.notin_(TERMINAL_STATUSES),
        )
        .group_by(Case.status)
    )
    cases_by_status = [{"status": row[0], "count": row[1]} for row in result.all()]

    # Cases by type (zelfde werkvoorraad-regel, S175b)
    result = await db.execute(
        select(Case.case_type, func.count(Case.id))
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.status.notin_(TERMINAL_STATUSES),
        )
        .group_by(Case.case_type)
    )
    cases_by_type = [{"case_type": row[0], "count": row[1]} for row in result.all()]

    # Cases opened this month
    today = date.today()
    first_of_month = today.replace(day=1)
    # "Deze maand" = werkelijk nieuw, niet de BaseNet-import (S203 #6). Import-rijen
    # dragen de marker in debtor_notes; zonder deze uitsluiting telt een her-import
    # van een deze-maand-geopende zaak onterecht mee.
    result = await db.execute(
        select(func.count(Case.id)).where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.date_opened >= first_of_month,
            func.coalesce(Case.debtor_notes, "").not_like(f"%{IMPORT_MARKER}%"),
        )
    )
    cases_this_month = result.scalar() or 0

    # Cases closed this month
    result = await db.execute(
        select(func.count(Case.id)).where(
            Case.tenant_id == tenant_id,
            Case.date_closed >= first_of_month,
            Case.date_closed.is_not(None),
        )
    )
    cases_closed_this_month = result.scalar() or 0

    # Contacts created this month — sluit de BaseNet-import uit (S203 #6): alle 1169
    # geïmporteerde relaties dragen een created_at-stempel van de importdag, wat het
    # dashboard "1169 nieuw deze maand" liet tonen. Import-rijen dragen de marker in notes.
    result = await db.execute(
        select(func.count(Contact.id)).where(
            Contact.tenant_id == tenant_id,
            Contact.created_at >= first_of_month,
            func.coalesce(Contact.notes, "").not_like(f"%{IMPORT_MARKER}%"),
        )
    )
    contacts_this_month = result.scalar() or 0

    scheduler_alerts = await get_scheduler_alerts(db)

    return {
        "total_active_cases": total_active_cases,
        "total_contacts": total_contacts,
        "total_outstanding": total_outstanding,
        "total_principal": total_principal,
        "total_paid": total_paid,
        "cases_by_status": cases_by_status,
        "cases_by_type": cases_by_type,
        "cases_this_month": cases_this_month,
        "cases_closed_this_month": cases_closed_this_month,
        "contacts_this_month": contacts_this_month,
        "scheduler_alerts": scheduler_alerts,
    }


async def get_recent_activity(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    limit: int = 20,
) -> dict:
    """Get the most recent activities across all cases.

    Returns a feed of the latest activities with case context.
    """
    # Query activities with case join
    result = await db.execute(
        select(CaseActivity)
        .join(Case, CaseActivity.case_id == Case.id)
        .where(
            CaseActivity.tenant_id == tenant_id,
            Case.is_active.is_(True),
        )
        .order_by(CaseActivity.created_at.desc())
        .limit(limit)
    )
    activities = result.scalars().all()

    # Get total count
    count_result = await db.execute(
        select(func.count(CaseActivity.id))
        .join(Case, CaseActivity.case_id == Case.id)
        .where(
            CaseActivity.tenant_id == tenant_id,
            Case.is_active.is_(True),
        )
    )
    total = count_result.scalar() or 0

    items = []
    for activity in activities:
        # Fetch the case for case_number
        case_result = await db.execute(select(Case).where(Case.id == activity.case_id))
        case = case_result.scalar_one_or_none()

        # Get user name if available
        user_name = None
        if activity.user:
            user_name = activity.user.full_name

        items.append(
            {
                "id": activity.id,
                "case_id": activity.case_id,
                "case_number": case.case_number if case else "?",
                "activity_type": activity.activity_type,
                "title": activity.title,
                "description": activity.description,
                "user_name": user_name,
                "created_at": activity.created_at,
            }
        )

    return {
        "items": items,
        "total": total,
    }
