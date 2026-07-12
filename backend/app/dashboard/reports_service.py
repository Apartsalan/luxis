"""Reports service — aggregation queries for management KPIs and incasso stats."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, func, select
from sqlalchemy import case as sql_case
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.cases.schemas import TERMINAL_STATUSES
from app.collections.models import Payment
from app.incasso.models import IncassoPipelineStep


async def get_kpis(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    months: int = 12,
) -> dict:
    """Get high-level KPIs for the reports page."""
    # Total + active cases. S175b/S199: 'actief' = niet-terminaal lopend werk;
    # is_active betekent sinds de BaseNet-import alleen 'zichtbaar'.
    result = await db.execute(
        select(
            func.count(Case.id),
            func.count(
                sql_case(
                    (
                        (Case.is_active.is_(True))
                        & Case.status.notin_(TERMINAL_STATUSES),
                        Case.id,
                    )
                )
            ),
        ).where(Case.tenant_id == tenant_id)
    )
    row = result.one()
    total_cases = row[0]
    active_cases = row[1]

    # Outstanding basis (alleen niet-terminale lopende zaken, S175b/S199)
    result = await db.execute(
        select(func.coalesce(func.sum(Case.total_principal), 0)).where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.status.notin_(TERMINAL_STATUSES),
        )
    )
    total_principal = Decimal(str(result.scalar_one()))
    # AUDIT-H4: 'openstaand' must include interest + BIK (same grand_total logic
    # as the case detail), not just principal − paid. collected/collection_rate
    # stay principal-based (separate metrics).
    from app.collections.service import get_portfolio_outstanding

    total_outstanding = await get_portfolio_outstanding(db, tenant_id)
    period_start = date.today().replace(day=1) - relativedelta(months=months - 1)
    # Definitie "Geïnd": de som van werkelijk geboekte betalingen waarvan de
    # payment_date binnen de geselecteerde rapportageperiode valt.
    result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.tenant_id == tenant_id,
            Payment.payment_date >= period_start,
        )
    )
    total_collected = Decimal(str(result.scalar_one()))

    # Collection rate
    collection_rate = (
        float(total_collected / total_principal * 100) if total_principal > 0 else 0.0
    )

    # Average days to collect (closed cases with date_opened and date_closed)
    result = await db.execute(
        select(func.avg(Case.date_closed - Case.date_opened)).where(
            Case.tenant_id == tenant_id,
            Case.date_closed.isnot(None),
            Case.date_opened.isnot(None),
        )
    )
    avg_interval = result.scalar()
    # date_closed - date_opened is an integer day-count in PostgreSQL, so
    # func.avg() returns a NUMERIC -> Decimal (no .days attribute). Round to int.
    avg_days_to_collect = int(round(float(avg_interval))) if avg_interval else 0

    # Cases by pipeline step
    result = await db.execute(
        select(
            IncassoPipelineStep.name,
            func.count(Case.id),
        )
        .join(
            IncassoPipelineStep,
            and_(
                Case.incasso_step_id == IncassoPipelineStep.id,
                IncassoPipelineStep.tenant_id == tenant_id,
            ),
            isouter=True,
        )
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.status.notin_(TERMINAL_STATUSES),
            Case.case_type == "incasso",
        )
        .group_by(IncassoPipelineStep.name)
    )
    cases_by_phase = {row[0] or "Geen stap": row[1] for row in result.all()}

    # Cases by debtor type — classify on the case's own debtor_type (b2b = the
    # debtor is a business, b2c = a consumer), NOT the creditor/client contact
    # that Case.client_id points to (AUDIT-MEDIUM: this used to group on the
    # client's contact_type, mislabelling the creditor as the debtor).
    result = await db.execute(
        select(
            sql_case(
                (Case.debtor_type == "b2b", "Bedrijf"),
                else_="Particulier",
            ),
            func.count(Case.id),
        )
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.status.notin_(TERMINAL_STATUSES),
        )
        .group_by(Case.debtor_type)
    )
    cases_by_debtor_type = {row[0]: row[1] for row in result.all()}

    # Overdue tasks count. Derive 'overdue' from due_date, NOT from the
    # materialized WorkflowTask.status — that column is only refreshed by a
    # daily batch job, so between runs it drifts stale and the KPI reads 0
    # while tasks are in fact overdue (AUDIT-H23).
    from app.workflow.models import WorkflowTask

    _open_task = (
        WorkflowTask.is_active.is_(True),
        WorkflowTask.status.notin_(["completed", "skipped"]),
    )
    result = await db.execute(
        select(func.count(WorkflowTask.id)).where(
            WorkflowTask.tenant_id == tenant_id,
            *_open_task,
            WorkflowTask.due_date < date.today(),
        )
    )
    overdue_tasks = result.scalar() or 0

    # Upcoming deadlines (open tasks due in the next 7 days) — also derived from
    # due_date so it stays consistent with the overdue count above.
    result = await db.execute(
        select(func.count(WorkflowTask.id)).where(
            WorkflowTask.tenant_id == tenant_id,
            *_open_task,
            WorkflowTask.due_date >= date.today(),
            WorkflowTask.due_date <= date.today() + timedelta(days=7),
        )
    )
    upcoming_deadlines = result.scalar() or 0

    return {
        "total_cases": total_cases,
        "active_cases": active_cases,
        "total_outstanding": str(total_outstanding),
        "total_collected": str(total_collected),
        "collection_rate": round(collection_rate, 1),
        "avg_days_to_collect": avg_days_to_collect,
        "cases_by_phase": cases_by_phase,
        "cases_by_debtor_type": cases_by_debtor_type,
        "overdue_tasks": overdue_tasks,
        "upcoming_deadlines": upcoming_deadlines,
    }


async def get_monthly_stats(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    months: int = 12,
) -> list[dict]:
    """Get monthly case and financial stats for the last N months."""
    today = date.today()
    start_date = today.replace(day=1) - timedelta(days=30 * (months - 1))
    start_date = start_date.replace(day=1)

    # New cases per month. AUDIT-MEDIUM: filter is_active — without it the
    # soft-deleted seed cases (hundreds of is_active=false rows) inflated the
    # chart to "215 nieuwe zaken" while only 2 cases are actually active.
    opened_month = func.to_char(Case.date_opened, "YYYY-MM").label("month")
    result = await db.execute(
        select(opened_month, func.count(Case.id))
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.date_opened >= start_date,
        )
        .group_by(opened_month)
        .order_by(opened_month)
    )
    new_cases_by_month = dict(result.all())

    # Closed cases per month (same is_active filter — the active book only).
    closed_month = func.to_char(Case.date_closed, "YYYY-MM").label("month")
    result = await db.execute(
        select(closed_month, func.count(Case.id))
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.date_closed >= start_date,
            Case.date_closed.isnot(None),
        )
        .group_by(closed_month)
        .order_by(closed_month)
    )
    closed_cases_by_month = dict(result.all())

    # Payments per month
    pay_month = func.to_char(Payment.payment_date, "YYYY-MM").label("month")
    result = await db.execute(
        select(pay_month, func.coalesce(func.sum(Payment.amount), 0))
        .where(
            Payment.tenant_id == tenant_id,
            Payment.payment_date >= start_date,
        )
        .group_by(pay_month)
        .order_by(pay_month)
    )
    collected_by_month = {row[0]: str(row[1]) for row in result.all()}

    # Build monthly stats list
    stats = []
    current = start_date
    while current <= today:
        month_key = current.strftime("%Y-%m")
        stats.append({
            "month": month_key,
            "new_cases": new_cases_by_month.get(month_key, 0),
            "closed_cases": closed_cases_by_month.get(month_key, 0),
            "amount_collected": collected_by_month.get(month_key, "0.00"),
            "amount_outstanding": "0.00",  # Would need per-month snapshot
        })
        # Next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return stats


async def get_phase_distribution(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[dict]:
    """Get distribution of active incasso cases across pipeline steps."""
    result = await db.execute(
        select(
            IncassoPipelineStep.name,
            func.count(Case.id),
            func.coalesce(func.sum(Case.total_principal - Case.total_paid), 0),
        )
        .join(
            IncassoPipelineStep,
            and_(
                Case.incasso_step_id == IncassoPipelineStep.id,
                IncassoPipelineStep.tenant_id == tenant_id,
            ),
            isouter=True,
        )
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.status.notin_(TERMINAL_STATUSES),
            Case.case_type == "incasso",
        )
        .group_by(IncassoPipelineStep.name, IncassoPipelineStep.sort_order)
        .order_by(IncassoPipelineStep.sort_order.nulls_last())
    )
    return [
        {
            "phase": row[0] or "Geen stap",
            "count": row[1],
            "total_amount": str(row[2]),
        }
        for row in result.all()
    ]
