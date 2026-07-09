"""Security tests for the tenant-context SQL-injection guard (S161/S162).

`set_tenant_context` interpolates the tenant id into a ``SET LOCAL
app.current_tenant = '...'`` statement, because PostgreSQL's SET cannot be
parameterized. The only thing standing between a malformed/hostile tenant id and
raw SQL is the strict UUID validation. These tests prove that guard holds — the
``except`` branch was previously uncovered.
"""

import pytest
from sqlalchemy import text

from app.middleware.tenant import set_tenant_context


@pytest.mark.parametrize(
    "bad_tenant_id",
    [
        "not-a-uuid",
        "'; DROP TABLE users; --",
        "11111111-1111-1111-1111-111111111111'; DROP TABLE contacts; --",
        "",
        "123",
        "00000000-0000-0000-0000-00000000000g",  # invalid hex digit
    ],
)
async def test_set_tenant_context_rejects_non_uuid(db, bad_tenant_id):
    """A non-UUID tenant id — including SQL-injection attempts — is rejected with
    ValueError BEFORE any SQL runs, so nothing reaches the SET statement."""
    with pytest.raises(ValueError):
        await set_tenant_context(db, bad_tenant_id)


async def test_set_tenant_context_accepts_valid_uuid(db, test_tenant):
    """A valid tenant UUID sets the session GUC that RLS reads."""
    await set_tenant_context(db, str(test_tenant.id))
    current = (
        await db.execute(text("SELECT current_setting('app.current_tenant', true)"))
    ).scalar()
    assert current == str(test_tenant.id)


# ── S183-2: context must survive a mid-request commit ─────────────────────────


async def test_tenant_context_survives_commit(db):
    """app.current_tenant is still set after a commit, without re-calling set_tenant_context.

    Before the after_begin re-application, SET LOCAL was reset at commit and the
    rest of the request ran as the bypass-RLS superuser with no tenant set.
    """
    import uuid

    tenant_id = str(uuid.uuid4())
    await set_tenant_context(db, tenant_id)

    before = (
        await db.execute(text("SELECT current_setting('app.current_tenant', true)"))
    ).scalar()
    assert before == tenant_id

    await db.commit()

    # New transaction after the commit — no second set_tenant_context call.
    after = (
        await db.execute(text("SELECT current_setting('app.current_tenant', true)"))
    ).scalar()
    assert after == tenant_id, "tenant context lost after commit (S183-2 regression)"


async def test_role_survives_commit_if_role_exists(db):
    """If luxis_app exists in this cluster, the role switch also survives a commit.

    Skipped where the role is absent (CI runs as the plain superuser) — there the
    role switch is a no-op by design and there is nothing to re-apply.
    """
    import uuid

    role_exists = (
        await db.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'luxis_app'"))
    ).scalar()
    if not role_exists:
        pytest.skip("luxis_app role not present in this test cluster")

    # set_tenant_context caches role-availability once per process. In a full-suite
    # run an earlier authenticated request caches it as False (test_rls_isolation
    # only CREATEs luxis_app partway through the suite), which would make the role
    # switch a silent no-op here and fail this guard for the wrong reason. Force a
    # fresh check for this test, then restore so no later test's behaviour shifts.
    from app.middleware import tenant as tenant_mod

    saved = (tenant_mod._rls_role_checked, tenant_mod._rls_role_available)
    tenant_mod._rls_role_checked = False
    try:
        tenant_id = str(uuid.uuid4())
        await set_tenant_context(db, tenant_id)
        assert (await db.execute(text("SELECT current_user"))).scalar() == "luxis_app"

        await db.commit()

        assert (
            await db.execute(text("SELECT current_user"))
        ).scalar() == "luxis_app", "role reverted to superuser after commit (S183-2 regression)"
    finally:
        tenant_mod._rls_role_checked, tenant_mod._rls_role_available = saved


async def test_plain_session_without_context_is_untouched(db):
    """A session that never sets a tenant keeps running as-is (migrations/jobs).

    Proves the after_begin listener is a strict no-op when no tenant is stored —
    it must not force a role or tenant onto background/migration sessions.
    """
    await db.commit()  # trigger a fresh transaction via the listener
    tenant = (
        await db.execute(text("SELECT current_setting('app.current_tenant', true)"))
    ).scalar()
    assert tenant in (None, ""), "listener set a tenant on a context-free session"
