"""Reports service — aggregation queries for management KPIs and incasso stats."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import case as sql_case
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.collections.models import Payment
from app.incasso.models import IncassoPipelineStep
from app.relations.models import Contact


async def get_kpis(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> dict:
    """Get high-level KPIs for the reports page."""
    # Total + active cases
    result = await db.execute(
        select(
            func.count(Case.id),
            func.count(sql_case((Case.is_active.is_(True), Case.id))),
        ).where(Case.tenant_id == tenant_id)
    )
    row = result.one()
    total_cases = row[0]
    active_cases = row[1]

    # Outstanding + collected
    result = await db.execute(
        select(
            func.coalesce(func.sum(Case.total_principal), 0),
            func.coalesce(func.sum(Case.total_paid), 0),
        ).where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
        )
    )
    row = result.one()
    total_principal = Decimal(str(row[0]))
    total_paid = Decimal(str(row[1]))
    total_outstanding = total_principal - total_paid
    total_collected = total_paid

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
    avg_days_to_collect = avg_interval.days if avg_interval else 0

    # Cases by pipeline step
    result = await db.execute(
        select(
            IncassoPipelineStep.name,
            func.count(Case.id),
        )
        .join(IncassoPipelineStep, Case.incasso_step_id == IncassoPipelineStep.id, isouter=True)
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.case_type == "incasso",
        )
        .group_by(IncassoPipelineStep.name)
    )
    cases_by_phase = {row[0] or "Geen stap": row[1] for row in result.all()}

    # Cases by debtor type
    result = await db.execute(
        select(
            sql_case(
                (Contact.contact_type == "company", "Bedrijf"),
                else_="Particulier",
            ),
            func.count(Case.id),
        )
        .join(Contact, Case.client_id == Contact.id, isouter=True)
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
        )
        .group_by(Contact.contact_type)
    )
    cases_by_debtor_type = {row[0]: row[1] for row in result.all()}

    # Overdue tasks count
    from app.workflow.models import WorkflowTask

    result = await db.execute(
        select(func.count(WorkflowTask.id)).where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.status == "overdue",
        )
    )
    overdue_tasks = result.scalar() or 0

    # Upcoming deadlines (due tasks in next 7 days)
    result = await db.execute(
        select(func.count(WorkflowTask.id)).where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.status.in_(["pending", "due"]),
            WorkflowTask.due_date <= date.today() + timedelta(days=7),
            WorkflowTask.due_date >= date.today(),
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

    # New cases per month
    result = await db.execute(
        select(
            func.to_char(Case.date_opened, "YYYY-MM"),
            func.count(Case.id),
        )
        .where(
            Case.tenant_id == tenant_id,
            Case.date_opened >= start_date,
        )
        .group_by(func.to_char(Case.date_opened, "YYYY-MM"))
        .order_by(func.to_char(Case.date_opened, "YYYY-MM"))
    )
    new_cases_by_month = dict(result.all())

    # Closed cases per month
    result = await db.execute(
        select(
            func.to_char(Case.date_closed, "YYYY-MM"),
            func.count(Case.id),
        )
        .where(
            Case.tenant_id == tenant_id,
            Case.date_closed >= start_date,
            Case.date_closed.isnot(None),
        )
        .group_by(func.to_char(Case.date_closed, "YYYY-MM"))
        .order_by(func.to_char(Case.date_closed, "YYYY-MM"))
    )
    closed_cases_by_month = dict(result.all())

    # Payments per month
    result = await db.execute(
        select(
            func.to_char(Payment.payment_date, "YYYY-MM"),
            func.coalesce(func.sum(Payment.amount), 0),
        )
        .where(
            Payment.tenant_id == tenant_id,
            Payment.payment_date >= start_date,
        )
        .group_by(func.to_char(Payment.payment_date, "YYYY-MM"))
        .order_by(func.to_char(Payment.payment_date, "YYYY-MM"))
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
        .join(IncassoPipelineStep, Case.incasso_step_id == IncassoPipelineStep.id)
        .where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.case_type == "incasso",
        )
        .group_by(IncassoPipelineStep.name, IncassoPipelineStep.sort_order)
        .order_by(IncassoPipelineStep.sort_order)
    )
    return [
        {
            "phase": row[0],
            "count": row[1],
            "total_amount": str(row[2]),
        }
        for row in result.all()
    ]
