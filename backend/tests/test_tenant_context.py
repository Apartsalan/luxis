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
