"""Dashboard module router — KPIs, recent activity, task, and reports endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dashboard import service
from app.dashboard.reports_service import get_kpis, get_monthly_stats, get_phase_distribution
from app.dashboard.schemas import DashboardSummary, RecentActivityResponse
from app.database import get_db
from app.dependencies import get_current_user
from app.workflow.schemas import WorkflowTaskResponse
from app.workflow.service import list_tasks as wf_list_tasks

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
reports_router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get the main dashboard KPI summary."""
    return await service.get_dashboard_summary(db, user.tenant_id)


@router.get("/recent-activity", response_model=RecentActivityResponse)
async def get_recent_activity(
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get the most recent activities across all cases."""
    return await service.get_recent_activity(db, user.tenant_id, limit)


@router.get("/my-tasks", response_model=list[WorkflowTaskResponse])
async def get_my_tasks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get open tasks assigned to the current user (due + overdue first)."""
    tasks = await wf_list_tasks(db, user.tenant_id, assigned_to_id=user.id)
    # Filter to non-completed tasks and sort: overdue first, then due, then pending
    status_order = {"overdue": 0, "due": 1, "pending": 2}
    open_tasks = [t for t in tasks if t.status in ("pending", "due", "overdue")]
    open_tasks.sort(key=lambda t: (status_order.get(t.status, 3), t.due_date))
    return open_tasks


# ── Reports endpoints ────────────────────────────────────────────────────


@reports_router.get("/kpis")
async def reports_kpis(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get high-level KPIs for the reports page."""
    return await get_kpis(db, user.tenant_id)


@reports_router.get("/monthly")
async def reports_monthly(
    months: int = Query(default=12, ge=1, le=36),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get monthly case and financial stats."""
    return await get_monthly_stats(db, user.tenant_id, months)


@reports_router.get("/phase-distribution")
async def reports_phase_distribution(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get distribution of active incasso cases across pipeline steps."""
    return await get_phase_distribution(db, user.tenant_id)
