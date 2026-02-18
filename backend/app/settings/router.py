"""Settings router — tenant profile, modules, and configuration."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.settings import service
from app.settings.schemas import TenantSettingsResponse, TenantSettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/tenant", response_model=TenantSettingsResponse)
async def get_tenant_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current tenant's profile and settings."""
    return await service.get_tenant_settings(db, current_user.tenant_id)


@router.put("/tenant", response_model=TenantSettingsResponse)
async def update_tenant_settings(
    data: TenantSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Update the current tenant's profile and settings. Admin only."""
    return await service.update_tenant_settings(db, admin.tenant_id, data)
