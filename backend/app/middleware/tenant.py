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
    await db.execute(text(f"SET app.current_tenant = '{tenant_id}'"))
