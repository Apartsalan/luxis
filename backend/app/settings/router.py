"""Settings router — tenant profile, modules, and configuration."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.email import service as email_service
from app.settings import service
from app.settings.schemas import (
    MailLockResponse,
    MailLockUpdate,
    TenantSettingsResponse,
    TenantSettingsUpdate,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _mail_lock_state() -> MailLockResponse:
    return MailLockResponse(
        locked=email_service.is_mail_locked(),
        db_locked=email_service.db_mail_locked(),
        env_hard_lock=bool(settings.outbound_mail_lock),
    )


@router.get("/mail-lock", response_model=MailLockResponse)
async def get_mail_lock(current_user: User = Depends(get_current_user)):
    """Huidige stand van het bouwfase-mailslot."""
    return _mail_lock_state()


@router.put("/mail-lock", response_model=MailLockResponse)
async def update_mail_lock(
    data: MailLockUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Mailslot open/dicht zetten. Admin only. Het env-noodslot blijft een harde
    override: staat dat aan, dan blijft mail geblokkeerd ongeacht deze knop."""
    await email_service.set_mail_lock(db, data.locked)
    return _mail_lock_state()


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
