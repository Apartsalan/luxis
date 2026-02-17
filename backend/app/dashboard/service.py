"""Dashboard module service — aggregation queries for KPIs and activity."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseActivity
from app.relations.models import Contact


async def get_dashboard_summary(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> dict:
    """Build the main dashboard KPI summary.

    Returns counts, totals, and breakdowns for the tenant's cases.
    """
    # Total active cases
    result = await db.execute(
        select(func.count(Case.id)).where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
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

    # Total principal and paid (from active cases)
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
    total_principal = float(row[0])
    total_paid = float(row[1])
    total_outstanding = total_principal - total_paid

    # Cases by status
    result = await db.execute(
        select(Case.status, func.count(Case.id)).where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
        ).group_by(Case.status)
    )
    cases_by_status = [
        {"status": row[0], "count": row[1]}
        for row in result.all()
    ]

    # Cases by type
    result = await db.execute(
        select(Case.case_type, func.count(Case.id)).where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
        ).group_by(Case.case_type)
    )
    cases_by_type = [
        {"case_type": row[0], "count": row[1]}
        for row in result.all()
    ]

    # Cases opened this month
    today = date.today()
    first_of_month = today.replace(day=1)
    result = await db.execute(
        select(func.count(Case.id)).where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.date_opened >= first_of_month,
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
        case_result = await db.execute(
            select(Case).where(Case.id == activity.case_id)
        )
        case = case_result.scalar_one_or_none()

        # Get user name if available
        user_name = None
        if activity.user:
            user_name = activity.user.full_name

        items.append({
            "id": activity.id,
            "case_id": activity.case_id,
            "case_number": case.case_number if case else "?",
            "activity_type": activity.activity_type,
            "title": activity.title,
            "description": activity.description,
            "user_name": user_name,
            "created_at": activity.created_at,
        })

    return {
        "items": items,
        "total": total,
    }
