"""Tenant middleware — extracts tenant_id from JWT and sets PostgreSQL session variable.

This enables Row-Level Security: every query is automatically scoped to the current tenant.
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Cache whether the luxis_app role exists (checked once per process).
_rls_role_checked: bool = False
_rls_role_available: bool = False


async def set_tenant_context(db: AsyncSession, tenant_id: str) -> None:
    """Set the current tenant in the PostgreSQL session.

    This is used by RLS policies to automatically filter all queries
    to only return rows belonging to the current tenant.
    """
    global _rls_role_checked, _rls_role_available

    # Validate tenant_id is a valid UUID to prevent SQL injection.
    # Note: SET does not support parameterized queries in PostgreSQL,
    # so we validate the UUID format strictly before interpolation.
    import uuid as _uuid
    try:
        validated = str(_uuid.UUID(str(tenant_id)))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid tenant_id: {tenant_id}")
    await db.execute(text(f"SET LOCAL app.current_tenant = '{validated}'"))

    # Switch to non-superuser role so RLS policies are enforced.
    # Check once if the role exists (won't exist in test DBs).
    if not _rls_role_checked:
        result = await db.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = 'luxis_app'")
        )
        _rls_role_available = result.scalar() is not None
        _rls_role_checked = True
        if not _rls_role_available:
            logger.warning("luxis_app role not found — RLS role switching disabled")

    if _rls_role_available:
        await db.execute(text("SET LOCAL ROLE luxis_app"))
