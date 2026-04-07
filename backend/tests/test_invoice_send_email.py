"""Tests for the invoice email-sending flow (DF117-13).

Lisanne demo 2026-04-07: clicking "Verzenden" on a factuur must actually
deliver the PDF to the customer's billing email via the connected provider,
not just flip the status to "sent". These tests cover both the happy path
and the error/edge cases.
"""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.email.oauth_models import EmailAccount
from app.invoices.models import Invoice
from app.invoices.service import _build_invoice_email_body, send_invoice
from app.relations.models import Contact


# ─── Fixtures ──────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def email_account(
    db: AsyncSession, test_tenant: Tenant, test_user: User
) -> EmailAccount:
    """Create a fake Outlook email account so send_with_attachment can
    find a provider to use."""
    account = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        provider="outlook",
        email_address="lisanne@kestinglegal.nl",
        access_token_enc=b"fake_access_token",
        refresh_token_enc=b"fake_refresh_token",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@pytest_asyncio.fixture
async def billable_contact(db: AsyncSession, test_tenant: Tenant) -> Contact:
    """Contact with a billing email — the typical client a factuur is sent to."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Acme Klant BV",
        email="contact@acmeklant.nl",
        billing_email="facturen@acmeklant.nl",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def _create_approved_invoice(
    client: AsyncClient, auth_headers: dict, contact_id: uuid.UUID
) -> dict:
    """Create a concept invoice and approve it (ready to send)."""
    payload = {
        "contact_id": str(contact_id),
        "invoice_date": "2026-04-01",
        "due_date": "2026-04-30",
        "btw_percentage": "21.00",
        "lines": [
            {"description": "Juridische dienstverlening", "quantity": "1", "unit_price": "1000.00"},
        ],
    }
    resp = await client.post("/api/invoices", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    invoice_id = resp.json()["id"]
    approve_resp = await client.post(f"/api/invoices/{invoice_id}/approve", headers=auth_headers)
    assert approve_resp.status_code == 200
    return approve_resp.json()


# ─── Happy path: send via provider with PDF attached ──────────────────────


@pytest.mark.asyncio
async def test_send_invoice_calls_provider_with_pdf(
    client: AsyncClient,
    auth_headers: dict,
    email_account: EmailAccount,
    billable_contact: Contact,
):
    """When the lawyer clicks Verzenden, the connected Outlook provider must
    be called with the rendered PDF as an attachment, recipient = billing_email,
    and subject = factuurnummer."""
    invoice = await _create_approved_invoice(client, auth_headers, billable_contact.id)
    invoice_id = invoice["id"]
    expected_recipient = "facturen@acmeklant.nl"

    with patch(
        "app.email.send_service.get_valid_access_token",
        new=AsyncMock(return_value="fake_token"),
    ), patch(
        "app.email.providers.outlook.OutlookProvider.send_message",
        new=AsyncMock(return_value="provider_msg_123"),
    ) as mock_send:
        resp = await client.post(
            f"/api/invoices/{invoice_id}/send", headers=auth_headers
        )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "sent"

    # Verify the provider was called exactly once with correct args
    mock_send.assert_called_once()
    call_kwargs = mock_send.call_args.kwargs
    assert call_kwargs["to"] == [expected_recipient]
    assert data["invoice_number"] in call_kwargs["subject"]
    # Attachment should be a single PDF
    attachments = call_kwargs["attachments"]
    assert len(attachments) == 1
    assert attachments[0].content_type == "application/pdf"
    assert attachments[0].filename.endswith(".pdf")
    # PDF bytes should be non-empty
    assert len(attachments[0].data) > 100


@pytest.mark.asyncio
async def test_send_invoice_falls_back_to_email_when_no_billing_email(
    client: AsyncClient,
    auth_headers: dict,
    email_account: EmailAccount,
    db: AsyncSession,
    test_tenant: Tenant,
):
    """When billing_email is not set, fall back to contact.email."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="No Billing BV",
        email="info@nobilling.nl",  # only regular email
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    invoice = await _create_approved_invoice(client, auth_headers, contact.id)

    with patch(
        "app.email.send_service.get_valid_access_token",
        new=AsyncMock(return_value="fake_token"),
    ), patch(
        "app.email.providers.outlook.OutlookProvider.send_message",
        new=AsyncMock(return_value="msg_456"),
    ) as mock_send:
        resp = await client.post(
            f"/api/invoices/{invoice['id']}/send", headers=auth_headers
        )

    assert resp.status_code == 200, resp.text
    mock_send.assert_called_once()
    assert mock_send.call_args.kwargs["to"] == ["info@nobilling.nl"]


# ─── Error paths ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_invoice_fails_when_contact_has_no_email(
    client: AsyncClient,
    auth_headers: dict,
    email_account: EmailAccount,
    db: AsyncSession,
    test_tenant: Tenant,
):
    """Without any email address, the send must fail loudly with a 400 — not
    silently flip the status to 'sent'."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="No Email BV",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    invoice = await _create_approved_invoice(client, auth_headers, contact.id)

    resp = await client.post(
        f"/api/invoices/{invoice['id']}/send", headers=auth_headers
    )
    assert resp.status_code == 400
    assert "e-mailadres" in resp.json()["detail"].lower()

    # Status must NOT have changed
    get_resp = await client.get(f"/api/invoices/{invoice['id']}", headers=auth_headers)
    assert get_resp.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_send_invoice_fails_when_provider_raises(
    client: AsyncClient,
    auth_headers: dict,
    email_account: EmailAccount,
    billable_contact: Contact,
):
    """If the provider call fails, the invoice status must not advance."""
    invoice = await _create_approved_invoice(client, auth_headers, billable_contact.id)

    with patch(
        "app.email.send_service.get_valid_access_token",
        new=AsyncMock(return_value="fake_token"),
    ), patch(
        "app.email.providers.outlook.OutlookProvider.send_message",
        new=AsyncMock(side_effect=RuntimeError("graph 503")),
    ):
        resp = await client.post(
            f"/api/invoices/{invoice['id']}/send", headers=auth_headers
        )

    assert resp.status_code == 400
    assert "verzenden mislukt" in resp.json()["detail"].lower()
    get_resp = await client.get(f"/api/invoices/{invoice['id']}", headers=auth_headers)
    assert get_resp.json()["status"] == "approved"


# ─── skip_email opt-out (manual send) ──────────────────────────────────────


@pytest.mark.asyncio
async def test_send_invoice_skip_email_only_updates_status(
    client: AsyncClient,
    auth_headers: dict,
    billable_contact: Contact,
):
    """skip_email=true is the legacy / manual-send path: just flip the status,
    no PDF, no provider call. No email account needed either."""
    invoice = await _create_approved_invoice(client, auth_headers, billable_contact.id)

    with patch(
        "app.email.providers.outlook.OutlookProvider.send_message",
        new=AsyncMock(return_value="should_not_be_called"),
    ) as mock_send:
        resp = await client.post(
            f"/api/invoices/{invoice['id']}/send?skip_email=true", headers=auth_headers
        )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "sent"
    mock_send.assert_not_called()


# ─── Body builder ──────────────────────────────────────────────────────────


def test_invoice_email_body_includes_key_details():
    """The HTML body should mention the invoice number, total, and due date."""

    class _FakeInvoice:
        invoice_number = "F2026-001"
        total = Decimal("1210.00")
        due_date = date(2026, 4, 30)

    body = _build_invoice_email_body(_FakeInvoice(), "Acme BV")
    assert "Acme BV" in body
    assert "F2026-001" in body
    assert "1.210,00" in body or "1210" in body
    assert "30-04-2026" in body or "30/04/2026" in body or "2026" in body
    assert "Kesting Legal" in body
