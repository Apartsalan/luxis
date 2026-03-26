"""Tests for the settings module — get/update tenant settings, role checks."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token, hash_password

import uuid

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_non_admin_user(
    db: AsyncSession, tenant: Tenant
) -> tuple[User, dict[str, str]]:
    """Create a non-admin user and return (user, auth_headers)."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="medewerker@kestinglegal.nl",
        hashed_password=hash_password("testpassword"),
        full_name="Medewerker Test",
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(str(user.id), str(tenant.id))
    return user, {"Authorization": f"Bearer {token}"}


# ── GET tenant settings ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_tenant_settings(
    client: AsyncClient, auth_headers: dict, test_tenant: Tenant
):
    """Any authenticated user can read tenant settings."""
    resp = await client.get("/api/settings/tenant", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Kesting Legal"
    assert data["slug"] == "kesting-legal"
    assert data["kvk_number"] == "88601536"


@pytest.mark.asyncio
async def test_get_tenant_settings_non_admin(
    client: AsyncClient, db: AsyncSession, test_tenant: Tenant
):
    """Non-admin users can also read tenant settings."""
    _, headers = await _create_non_admin_user(db, test_tenant)
    resp = await client.get("/api/settings/tenant", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Kesting Legal"


# ── PUT tenant settings ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_tenant_settings(
    client: AsyncClient, auth_headers: dict, test_tenant: Tenant
):
    """Admin can update tenant settings."""
    resp = await client.put(
        "/api/settings/tenant",
        json={
            "name": "Kesting Legal B.V.",
            "city": "Amsterdam",
            "iban": "NL91ABNA0417164300",
            "phone": "+31207891234",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Kesting Legal B.V."
    assert data["city"] == "Amsterdam"
    assert data["iban"] == "NL91ABNA0417164300"


@pytest.mark.asyncio
async def test_update_tenant_settings_non_admin_forbidden(
    client: AsyncClient, db: AsyncSession, test_tenant: Tenant
):
    """Non-admin users cannot update tenant settings."""
    _, headers = await _create_non_admin_user(db, test_tenant)
    resp = await client.put(
        "/api/settings/tenant",
        json={"name": "Hacked Name"},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_preserves_unset_fields(
    client: AsyncClient, auth_headers: dict, test_tenant: Tenant
):
    """Updating some fields should not clear others."""
    await client.put(
        "/api/settings/tenant",
        json={"city": "Amsterdam", "phone": "+31207891234"},
        headers=auth_headers,
    )
    resp = await client.put(
        "/api/settings/tenant",
        json={"email": "info@kestinglegal.nl"},
        headers=auth_headers,
    )
    data = resp.json()
    assert data["email"] == "info@kestinglegal.nl"
    assert data["kvk_number"] == "88601536"  # should still be there


# ── Tenant isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tenant_isolation(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
):
    """Tenant A settings are not visible to tenant B."""
    resp_a = await client.get("/api/settings/tenant", headers=auth_headers)
    resp_b = await client.get("/api/settings/tenant", headers=second_auth_headers)
    assert resp_a.json()["name"] != resp_b.json()["name"]


# ── Auth ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(client: AsyncClient):
    """Requests without auth token return 401."""
    resp = await client.get("/api/settings/tenant")
    assert resp.status_code in (401, 403)
