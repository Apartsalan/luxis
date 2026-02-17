"""Tests for the authentication system."""

import pytest
from httpx import AsyncClient

from app.auth.models import Tenant, User
from app.auth.service import create_access_token


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
        "/auth/login",
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
        "/auth/login",
        json={"email": "lisanne@kestinglegal.nl", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient, test_user: User):
    """Unknown email should return 401."""
    response = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client: AsyncClient, test_user: User, test_tenant: Tenant):
    """Authenticated request to /auth/me should return user info."""
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "lisanne@kestinglegal.nl"
    assert data["full_name"] == "Lisanne Kesting"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient):
    """Request without token should return 403."""
    response = await client.get("/auth/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_me_with_invalid_token(client: AsyncClient):
    """Request with invalid token should return 401."""
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_user: User):
    """Login, then use refresh token to get new tokens."""
    # First login
    login_response = await client.post(
        "/auth/login",
        json={"email": "lisanne@kestinglegal.nl", "password": "testpassword123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    # Use refresh token
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
