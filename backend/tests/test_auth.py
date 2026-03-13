"""Tests for the authentication system."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token, hash_password
from app.config import settings


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health endpoint should always return OK."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    """Valid credentials should return access + refresh tokens."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "lisanne@kestinglegal.nl", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: User):
    """Wrong password should return 401."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "lisanne@kestinglegal.nl", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient, test_user: User):
    """Unknown email should return 401."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client: AsyncClient, test_user: User, test_tenant: Tenant):
    """Authenticated request to /auth/me should return user info."""
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "lisanne@kestinglegal.nl"
    assert data["full_name"] == "Lisanne Kesting"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient):
    """Request without token should return 401."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token(client: AsyncClient):
    """Request with invalid token should return 401."""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_user: User):
    """Login, then use refresh token to get new tokens."""
    # First login
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "lisanne@kestinglegal.nl", "password": "testpassword123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    # Use refresh token
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


# ── Tenant Isolation & Edge Cases ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_expired_token_returns_401(client: AsyncClient, test_user: User, test_tenant: Tenant):
    """An expired access token should return 401."""
    expire = datetime.now(UTC) - timedelta(minutes=5)
    payload = {
        "sub": str(test_user.id),
        "tenant_id": str(test_tenant.id),
        "type": "access",
        "exp": expire,
    }
    expired_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_with_nonexistent_user_returns_401(
    client: AsyncClient, test_tenant: Tenant
):
    """A token referencing a deleted/non-existent user should return 401."""
    fake_user_id = str(uuid.uuid4())
    token = create_access_token(fake_user_id, str(test_tenant.id))
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_empty_credentials(client: AsyncClient, test_user: User):
    """Empty email and/or password should return 401 or 422."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "", "password": ""},
    )
    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_inactive_user_cannot_login(
    client: AsyncClient, db: AsyncSession, test_tenant: Tenant
):
    """A user with is_active=False should not be able to login."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="inactive@kestinglegal.nl",
        hashed_password=hash_password("testpassword123"),
        full_name="Inactive User",
        role="admin",
        is_active=False,
    )
    db.add(user)
    await db.commit()

    response = await client.post(
        "/api/auth/login",
        json={"email": "inactive@kestinglegal.nl", "password": "testpassword123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_correct_tenant(
    client: AsyncClient, test_user: User, test_tenant: Tenant,
    second_user: User, second_tenant: Tenant,
):
    """Each user's /me endpoint should return their own tenant info."""
    # Tenant A
    token_a = create_access_token(str(test_user.id), str(test_tenant.id))
    resp_a = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert resp_a.status_code == 200
    assert resp_a.json()["email"] == "lisanne@kestinglegal.nl"

    # Tenant B
    token_b = create_access_token(str(second_user.id), str(second_tenant.id))
    resp_b = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert resp_b.status_code == 200
    assert resp_b.json()["email"] == "pieter@vandenberg.nl"


@pytest.mark.asyncio
async def test_update_profile_with_default_hourly_rate(
    client: AsyncClient, test_user: User, test_tenant: Tenant
):
    """Updating profile should set default_hourly_rate on user."""
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Set default hourly rate
    resp = await client.put(
        "/api/auth/me",
        json={"default_hourly_rate": "250.00"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["default_hourly_rate"] == "250.00"

    # Verify it persists via GET
    resp2 = await client.get("/api/auth/me", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["default_hourly_rate"] == "250.00"

    # Clear it by setting null
    resp3 = await client.put(
        "/api/auth/me",
        json={"default_hourly_rate": None},
        headers=headers,
    )
    assert resp3.status_code == 200
    assert resp3.json()["default_hourly_rate"] is None


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(client: AsyncClient):
    """Refreshing with garbage token should fail."""
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": "not-a-real-token"},
    )
    assert response.status_code == 401
