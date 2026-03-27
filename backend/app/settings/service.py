"""Settings service — tenant profile and module management."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.settings.schemas import VALID_MODULES, TenantSettingsUpdate
from app.shared.exceptions import BadRequestError, NotFoundError


async def get_tenant_settings(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> Tenant:
    """Get tenant profile and settings."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise NotFoundError("Kantoor niet gevonden")
    return tenant


async def update_tenant_settings(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: TenantSettingsUpdate,
) -> Tenant:
    """Update tenant profile and settings."""
    tenant = await get_tenant_settings(db, tenant_id)

    updates = data.model_dump(exclude_unset=True)

    # Validate modules_enabled if provided
    if "modules_enabled" in updates and updates["modules_enabled"] is not None:
        invalid = [m for m in updates["modules_enabled"] if m not in VALID_MODULES]
        if invalid:
            raise BadRequestError(
                f"Onbekende modules: {', '.join(invalid)}. "
                f"Geldige opties: {', '.join(VALID_MODULES)}"
            )

    for field, value in updates.items():
        setattr(tenant, field, value)

    await db.flush()
    await db.refresh(tenant)
    return tenant
