"""Dashboard module router — KPIs and recent activity endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dashboard import service
from app.dashboard.schemas import DashboardSummary, RecentActivityResponse
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


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
    return await service.get_recent_activity(
        db, user.tenant_id, limit
    )
