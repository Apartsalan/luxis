"""Tenant middleware — extracts tenant_id from JWT and sets PostgreSQL session variable.

This enables Row-Level Security: every query is automatically scoped to the current tenant.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_tenant_context(db: AsyncSession, tenant_id: str) -> None:
    """Set the current tenant in the PostgreSQL session.

    This is used by RLS policies to automatically filter all queries
    to only return rows belonging to the current tenant.
    """
    # Validate tenant_id is a valid UUID to prevent SQL injection.
    # Note: SET does not support parameterized queries in PostgreSQL,
    # so we validate the UUID format strictly before interpolation.
    import uuid as _uuid
    try:
        validated = str(_uuid.UUID(str(tenant_id)))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid tenant_id: {tenant_id}")
    await db.execute(text(f"SET LOCAL app.current_tenant = '{validated}'"))
