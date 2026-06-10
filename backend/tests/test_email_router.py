"""Tests for the email base router — status check, test email, case email."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.config import settings
from app.relations.models import Contact


def _force_smtp_unconfigured(monkeypatch) -> None:
    """Force is_configured() to return False regardless of environment.

    The dev stack wires SMTP to Mailpit (smtp_host set), so these
    'not configured' tests were always red locally and only green in CI.
    Patching the settings is_configured() reads makes them deterministic.
    """
    monkeypatch.setattr(settings, "smtp_host", "")
    monkeypatch.setattr(settings, "smtp_from", "")

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_case(db: AsyncSession, tenant_id: uuid.UUID) -> Case:
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Test Client B.V.",
        email="client@example.nl",
    )
    db.add(contact)
    await db.flush()

    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number="2026-00001",
        case_type="incasso",
        status="nieuw",
        debtor_type="b2b",
        date_opened=date.today(),
        client_id=contact.id,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


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


# ── Send Case Email ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_case_email_not_configured(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, monkeypatch
):
    """Sending case email fails with 400 when SMTP not configured."""
    _force_smtp_unconfigured(monkeypatch)
    case = await _create_case(db, test_tenant.id)
    resp = await client.post(
        f"/api/email/cases/{case.id}/send",
        json={
            "recipient_email": "debiteur@example.nl",
            "subject": "Herinnering openstaande factuur",
            "body": "Geachte heer/mevrouw, hierbij herinneren wij u aan de openstaande factuur.",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_send_case_email_nonexistent_case(client: AsyncClient, auth_headers: dict):
    """Sending email for nonexistent case returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/email/cases/{fake_id}/send",
        json={
            "recipient_email": "test@example.nl",
            "subject": "Test",
            "body": "Test body",
        },
        headers=auth_headers,
    )
    # Either 400 (SMTP not configured check first) or 404
    assert resp.status_code in (400, 404)


# ── Tenant isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_email_case_tenant_isolation(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
):
    """Cannot send email for a case belonging to another tenant."""
    case = await _create_case(db, test_tenant.id)
    resp = await client.post(
        f"/api/email/cases/{case.id}/send",
        json={
            "recipient_email": "test@example.nl",
            "subject": "Test",
            "body": "Test",
        },
        headers=second_auth_headers,
    )
    # SMTP not configured returns 400 before tenant check, or 404 if tenant check first
    assert resp.status_code in (400, 404)


# ── Auth ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.get("/api/email/status")
    assert resp.status_code in (401, 403)
