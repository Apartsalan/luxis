"""Tests for the notifications module — stub endpoints return expected shapes."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_notifications_returns_empty(client: AsyncClient, auth_headers: dict):
    """Stub: list notifications returns empty list."""
    resp = await client.get("/api/notifications", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_unread_count_returns_zero(client: AsyncClient, auth_headers: dict):
    """Stub: unread count returns zero."""
    resp = await client.get("/api/notifications/unread-count", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


@pytest.mark.asyncio
async def test_mark_read(client: AsyncClient, auth_headers: dict):
    """Stub: mark notification as read returns ok."""
    fake_id = str(uuid.uuid4())
    resp = await client.put(f"/api/notifications/{fake_id}/read", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient, auth_headers: dict):
    """Stub: mark all notifications as read returns ok."""
    resp = await client.put("/api/notifications/read-all", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(client: AsyncClient):
    """Requests without auth token return 401."""
    resp = await client.get("/api/notifications")
    assert resp.status_code in (401, 403)
