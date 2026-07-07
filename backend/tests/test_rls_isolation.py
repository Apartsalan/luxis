"""Adversarial Row-Level Security (RLS) isolation tests — AUDIT-H2.

Proves that PostgreSQL RLS, not just the application's WHERE clauses, blocks
cross-tenant access. The setup mirrors production exactly by reusing the shared
``app.security.rls`` helpers (the same code the migration runs).

Why self-contained: CI runs ``pytest`` directly (no Alembic migrations) and
connects as the superuser ``luxis``. So each test creates the ``luxis_app`` role
and applies the policies itself, then drops to ``luxis_app`` via ``SET ROLE`` to
exercise enforcement — superusers always bypass RLS.

The control assertion (superuser sees BOTH tenants) is the red→green proof: it
demonstrates the data is physically present and that the role switch is what
hides the other tenant's rows.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.auth.models import Tenant
from app.config import settings
from app.relations.models import Contact
from app.security.rls import (
    apply_rls,
    disable_rls,
    discover_tenant_tables,
    find_unprotected_tenant_tables,
    rls_statements,
)

# Separate engine to the same test DB so we control role/connection precisely,
# independent of the ORM session fixture. NullPool → every connect() is a fresh
# backend, so SET ROLE never leaks between assertions or tests.
_TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/luxis_test"
_engine = create_async_engine(_TEST_DATABASE_URL, echo=False, poolclass=NullPool)


@pytest_asyncio.fixture
async def two_tenants_with_contacts(db, setup_database):
    """Seed two tenants, each with one contact, then apply the production RLS
    setup. Seeding runs as superuser (RLS bypassed), so both rows land.

    Returns (tenant_a_id, contact_a_id, tenant_b_id, contact_b_id).
    """
    tenant_a = Tenant(id=uuid.uuid4(), name="Kesting Legal", slug=f"a-{uuid.uuid4().hex[:8]}")
    tenant_b = Tenant(id=uuid.uuid4(), name="Van den Berg", slug=f"b-{uuid.uuid4().hex[:8]}")
    db.add_all([tenant_a, tenant_b])
    await db.flush()

    contact_a = Contact(
        id=uuid.uuid4(), tenant_id=tenant_a.id, contact_type="company", name="Acme A BV"
    )
    contact_b = Contact(
        id=uuid.uuid4(), tenant_id=tenant_b.id, contact_type="company", name="Acme B BV"
    )
    db.add_all([contact_a, contact_b])
    await db.commit()

    # Apply role + grants + per-table ENABLE/FORCE/policy — identical to the migration.
    async with _engine.begin() as conn:
        await conn.run_sync(apply_rls)

    yield tenant_a.id, contact_a.id, tenant_b.id, contact_b.id

    # Teardown: remove policies + disable RLS so later tests in the same process
    # (which run as luxis_app once the role exists) are not tenant-filtered. The
    # role + grants are left in place — conftest grants them on schema rebuild.
    async with _engine.begin() as conn:
        await conn.run_sync(disable_rls)


async def test_select_is_scoped_to_current_tenant(two_tenants_with_contacts):
    """As luxis_app with tenant A set, only A's contacts are visible."""
    tenant_a, contact_a, tenant_b, contact_b = two_tenants_with_contacts

    async with _engine.connect() as conn:
        await conn.execute(text("SET ROLE luxis_app"))
        await conn.execute(text(f"SET app.current_tenant = '{tenant_a}'"))
        ids = (await conn.execute(text("SELECT id FROM contacts"))).scalars().all()

    assert contact_a in ids
    assert contact_b not in ids, "LEAK: tenant B's contact visible under tenant A context"
    assert len(ids) == 1


async def test_current_tenant_flip_changes_visibility(two_tenants_with_contacts):
    """Switching app.current_tenant to B flips visibility to B's rows only."""
    tenant_a, contact_a, tenant_b, contact_b = two_tenants_with_contacts

    async with _engine.connect() as conn:
        await conn.execute(text("SET ROLE luxis_app"))
        await conn.execute(text(f"SET app.current_tenant = '{tenant_b}'"))
        ids = (await conn.execute(text("SELECT id FROM contacts"))).scalars().all()

    assert ids == [contact_b]
    assert contact_a not in ids


async def test_forged_cross_tenant_select_returns_zero_rows(two_tenants_with_contacts):
    """Directly forging a query for tenant B's known id while in tenant A's
    context returns 0 rows — RLS blocks the targeted read."""
    tenant_a, contact_a, tenant_b, contact_b = two_tenants_with_contacts

    async with _engine.connect() as conn:
        await conn.execute(text("SET ROLE luxis_app"))
        await conn.execute(text(f"SET app.current_tenant = '{tenant_a}'"))
        count = (
            await conn.execute(
                text("SELECT count(*) FROM contacts WHERE id = :cid"), {"cid": contact_b}
            )
        ).scalar()

    assert count == 0


async def test_cross_tenant_insert_is_blocked(two_tenants_with_contacts):
    """As luxis_app in tenant A's context, inserting a row tagged tenant B is
    rejected by the policy's WITH CHECK — you cannot write into another tenant."""
    tenant_a, contact_a, tenant_b, contact_b = two_tenants_with_contacts

    with pytest.raises((ProgrammingError, DBAPIError)) as exc_info:
        async with _engine.connect() as conn:
            await conn.execute(text("SET ROLE luxis_app"))
            await conn.execute(text(f"SET app.current_tenant = '{tenant_a}'"))
            await conn.execute(
                text(
                    "INSERT INTO contacts (id, tenant_id, contact_type, name) "
                    "VALUES (:id, :tid, 'company', 'Hacker BV')"
                ),
                {"id": uuid.uuid4(), "tid": tenant_b},
            )
            await conn.commit()

    assert "row-level security" in str(exc_info.value).lower()


async def test_superuser_control_sees_both_tenants(two_tenants_with_contacts):
    """CONTROL (red→green proof): without the role switch, the superuser sees
    BOTH tenants' rows. This proves the data is present and that RLS — not an
    empty table — is what isolates the tenants in the tests above."""
    tenant_a, contact_a, tenant_b, contact_b = two_tenants_with_contacts

    async with _engine.connect() as conn:
        # No SET ROLE: still the superuser luxis → RLS bypassed.
        ids = (await conn.execute(text("SELECT id FROM contacts"))).scalars().all()

    assert contact_a in ids
    assert contact_b in ids


async def test_all_tenant_tables_are_force_protected(two_tenants_with_contacts):
    """Coverage: every tenant-scoped table has FORCE RLS and a tenant_isolation
    policy. Guards against future tables silently shipping without isolation."""
    async with _engine.connect() as conn:
        tables = await conn.run_sync(discover_tenant_tables)
        assert tables, "no tenant tables discovered — schema not built?"

        unprotected = []
        for table in tables:
            forced = (
                await conn.execute(
                    text(
                        "SELECT relforcerowsecurity FROM pg_class "
                        "WHERE relname = :t AND relnamespace = 'public'::regnamespace"
                    ),
                    {"t": table},
                )
            ).scalar()
            has_policy = (
                await conn.execute(
                    text(
                        "SELECT 1 FROM pg_policies WHERE schemaname = 'public' "
                        "AND tablename = :t AND policyname = 'tenant_isolation'"
                    ),
                    {"t": table},
                )
            ).scalar()
            if not forced or not has_policy:
                unprotected.append((table, forced, has_policy))

    assert not unprotected, f"tables missing FORCE RLS or policy: {unprotected}"


async def test_users_table_excluded_from_rls(two_tenants_with_contacts):
    """`users` carries tenant_id but is deliberately excluded (cross-tenant login
    lookup). Confirm it is NOT in the protected set."""
    async with _engine.connect() as conn:
        tables = await conn.run_sync(discover_tenant_tables)
    assert "users" not in tables


async def test_drift_guard_flags_tenant_table_without_rls(setup_database):
    """S183-1 drift-guard: a tenant table lacking RLS is detected.

    This is the mechanism the production startup check (app.main.lifespan) runs.
    Create a throwaway table with a tenant_id column and NO RLS, assert the guard
    flags it, then secure it and assert the guard clears — proving a
    learned_answers-style gap (table shipped by a migration without RLS) would be
    caught at boot instead of silently leaking. Only asserts on the probe table,
    so it is independent of whatever RLS state the other tables are in."""
    async with _engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS _drift_probe"))
        await conn.execute(
            text("CREATE TABLE _drift_probe (id uuid PRIMARY KEY, tenant_id uuid NOT NULL)")
        )
    try:
        async with _engine.connect() as conn:
            flagged = await conn.run_sync(find_unprotected_tenant_tables)
        assert "_drift_probe" in flagged, "guard failed to flag an unprotected tenant table"

        async with _engine.begin() as conn:
            for stmt in rls_statements("_drift_probe"):
                await conn.execute(text(stmt))
        async with _engine.connect() as conn:
            flagged = await conn.run_sync(find_unprotected_tenant_tables)
        assert "_drift_probe" not in flagged, "guard flagged a table that IS protected"
    finally:
        async with _engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS _drift_probe"))
