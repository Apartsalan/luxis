"""Tenant middleware — extracts tenant_id from JWT and sets PostgreSQL session variable.

This enables Row-Level Security: every query is automatically scoped to the current tenant.

S183-2: ``SET LOCAL`` (both ``app.current_tenant`` and ``SET ROLE luxis_app``) is
transaction-scoped — it is reset the moment a transaction commits. A request that
commits mid-way (a handler that commits then does more DB work for its response)
would therefore drop back to the bypass-RLS superuser with no tenant set for the
rest of the request. To fix that once, structurally, we store the tenant on the
session and re-apply it via an ``after_begin`` event so EVERY transaction in a
request-scoped session (including the one after a mid-request commit) is correctly
scoped. Sessions without a stored tenant (migrations, background jobs) are untouched.
"""

import logging
import os
import uuid as _uuid

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Cache whether the luxis_app role exists (checked once per process).
_rls_role_checked: bool = False
_rls_role_available: bool = False

# Keys under which the per-request tenant context lives on Session.info.
_TENANT_INFO_KEY = "app_current_tenant"
_ROLE_INFO_KEY = "app_rls_role"


@event.listens_for(Session, "after_begin")
def _reapply_tenant_context(session: Session, transaction, connection) -> None:
    """Re-apply tenant + role at the start of every transaction (S183-2).

    Fires on the transaction that follows a mid-request ``commit()`` too, so the
    ``SET LOCAL`` context that the commit reset is restored before the next query
    runs. No-op for any session that never stored a tenant (migrations, jobs,
    plain test sessions) — those intentionally keep running as the superuser.
    """
    tenant_id = session.info.get(_TENANT_INFO_KEY)
    if not tenant_id:
        return
    # tenant_id is a validated UUID string (see set_tenant_context); safe to inline.
    connection.exec_driver_sql(f"SET LOCAL app.current_tenant = '{tenant_id}'")
    if session.info.get(_ROLE_INFO_KEY):
        connection.exec_driver_sql("SET LOCAL ROLE luxis_app")


async def set_tenant_context(db: AsyncSession, tenant_id: str) -> None:
    """Set the current tenant in the PostgreSQL session.

    This is used by RLS policies to automatically filter all queries
    to only return rows belonging to the current tenant. The context is stored on
    the session so it survives a mid-request commit (see ``_reapply_tenant_context``).
    """
    global _rls_role_checked, _rls_role_available

    # Validate tenant_id is a valid UUID to prevent SQL injection.
    # Note: SET does not support parameterized queries in PostgreSQL,
    # so we validate the UUID format strictly before interpolation.
    try:
        validated = str(_uuid.UUID(str(tenant_id)))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid tenant_id: {tenant_id}")

    # Store on the session BEFORE issuing SET, so the after_begin listener
    # re-applies it on every subsequent transaction in this request.
    db.sync_session.info[_TENANT_INFO_KEY] = validated
    await db.execute(text(f"SET LOCAL app.current_tenant = '{validated}'"))

    # Switch to non-superuser role so RLS policies are enforced.
    # Check once if the role exists (won't exist in test DBs).
    if not _rls_role_checked:
        result = await db.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'luxis_app'"))
        _rls_role_available = result.scalar() is not None
        _rls_role_checked = True
        if not _rls_role_available:
            app_env = os.environ.get("APP_ENV", "development")
            if app_env == "production":
                raise RuntimeError(
                    "CRITICAL: luxis_app role not found in production — "
                    "RLS cannot be enforced. Run migrations first."
                )
            logger.warning(
                "luxis_app role not found — RLS role switching disabled (non-production)"
            )

    if _rls_role_available:
        db.sync_session.info[_ROLE_INFO_KEY] = True
        await db.execute(text("SET LOCAL ROLE luxis_app"))
