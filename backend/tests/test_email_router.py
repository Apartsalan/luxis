"""Tests for the email base router — status check + test email."""

import pytest
from httpx import AsyncClient

from app.config import settings


def _force_smtp_unconfigured(monkeypatch) -> None:
    """Force is_configured() to return False regardless of environment.

    The dev stack wires SMTP to Mailpit (smtp_host set), so these
    'not configured' tests were always red locally and only green in CI.
    Patching the settings is_configured() reads makes them deterministic.
    """
    monkeypatch.setattr(settings, "smtp_host", "")
    monkeypatch.setattr(settings, "smtp_from", "")


# ── Email Status ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_email_status(client: AsyncClient, auth_headers: dict):
    """Email status endpoint returns configured boolean."""
    resp = await client.get("/api/email/status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "configured" in data
    assert isinstance(data["configured"], bool)


# ── Test Email ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_test_email_not_configured(client: AsyncClient, auth_headers: dict, monkeypatch):
    """Test email fails gracefully when SMTP not configured."""
    _force_smtp_unconfigured(monkeypatch)
    resp = await client.post(
        "/api/email/test",
        json={"recipient_email": "test@example.nl"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "SMTP" in data["message"]


# ── Auth ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.get("/api/email/status")
    assert resp.status_code in (401, 403)
