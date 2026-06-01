"""Tests for trust funds offset-to-invoice (verrekening) flow.

Covers DF117-21 verrekening: offset trust balance against own invoice with
required client consent (Voda art. 6.19 lid 5).
"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token, hash_password
from app.relations.models import Contact

# ── Helpers ──────────────────────────────────────────────────────────────────


@pytest.fixture
def case_payload(test_company: Contact) -> dict:
    return {
        "case_type": "advies",
        "description": "Verrekening test zaak",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-20",
    }


async def _create_case(client: AsyncClient, headers: dict, payload: dict) -> str:
    r = await client.post("/api/cases", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _create_sent_invoice(
    client: AsyncClient,
    headers: dict,
    contact_id: str,
    db: AsyncSession,
    case_id: str | None = None,
    lines: list[dict] | None = None,
) -> dict:
    """Create an invoice and force it to 'sent' status.

    Bypasses /api/invoices/{id}/send because that endpoint requires SMTP
    (DF117-13 actually emails the PDF). For tests we update the DB directly.
    """
    from sqlalchemy import select as _select

    from app.invoices.models import Invoice as InvoiceModel

    if lines is None:
        lines = [{"description": "Honorarium", "quantity": "10", "unit_price": "100.00"}]
    payload = {
        "contact_id": contact_id,
        "invoice_date": "2026-02-01",
        "due_date": "2026-03-01",
        "btw_percentage": "21.00",
        "lines": lines,
    }
    if case_id:
        payload["case_id"] = case_id
    r = await client.post("/api/invoices", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    inv = r.json()
    r = await client.post(f"/api/invoices/{inv['id']}/approve", headers=headers)
    assert r.status_code == 200, r.text

    # Bypass /send (requires real SMTP) — set status directly in DB
    res = await db.execute(_select(InvoiceModel).where(InvoiceModel.id == uuid.UUID(inv["id"])))
    invoice_obj = res.scalar_one()
    invoice_obj.status = "sent"
    await db.commit()

    r = await client.get(f"/api/invoices/{inv['id']}", headers=headers)
    assert r.status_code == 200
    return r.json()


async def _create_deposit(client: AsyncClient, headers: dict, case_id: str, amount: str) -> dict:
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json={
            "transaction_type": "deposit",
            "amount": amount,
            "description": f"Storting {amount}",
            "payment_method": "bank",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _create_second_user(db: AsyncSession, tenant: Tenant) -> tuple[User, dict]:
    u = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=f"approver-{uuid.uuid4()}@kestinglegal.nl",
        hashed_password=hash_password("testpassword123"),
        full_name="Tweede Directeur",
        role="admin",
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    token = create_access_token(str(u.id), str(tenant.id))
    return u, {"Authorization": f"Bearer {token}"}


def _consent_payload(invoice_id: str, amount: str, **overrides) -> dict:
    base = {
        "amount": amount,
        "description": "Verrekening met factuur",
        "target_invoice_id": invoice_id,
        "consent_received_at": "2026-04-08",
        "consent_method": "email",
        "consent_note": "Bevestigd per email op 8 april 2026 door Jan Jansen",
    }
    base.update(overrides)
    return base


# ── Eligible invoices listing ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_eligible_invoices_lists_open_invoices(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
    db: AsyncSession,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    invoice = await _create_sent_invoice(client, auth_headers, str(test_company.id), db)

    r = await client.get(
        f"/api/trust-funds/cases/{case_id}/eligible-invoices", headers=auth_headers
    )
    assert r.status_code == 200
    invoices = r.json()
    assert any(inv["id"] == invoice["id"] for inv in invoices)
    match = next(inv for inv in invoices if inv["id"] == invoice["id"])
    assert Decimal(match["outstanding"]) == Decimal(invoice["total"])


# ── Happy path ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_offset_happy_path_books_invoice_payment(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
    db: AsyncSession,
    test_tenant: Tenant,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    await _create_deposit(client, auth_headers, case_id, "1000.00")
    invoice = await _create_sent_invoice(client, auth_headers, str(test_company.id), db)
    invoice_total = Decimal(invoice["total"])

    payload = _consent_payload(invoice["id"], "500.00")
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/offsets", json=payload, headers=auth_headers
    )
    assert r.status_code == 201, r.text
    offset = r.json()
    assert offset["transaction_type"] == "offset_to_invoice"
    assert offset["status"] == "pending_approval"
    assert offset["target_invoice_id"] == invoice["id"]
    assert offset["consent_method"] == "email"

    # Balance excludes pending offset from available
    r = await client.get(f"/api/trust-funds/cases/{case_id}/balance", headers=auth_headers)
    assert r.status_code == 200
    bal = r.json()
    assert Decimal(bal["available"]) == Decimal("500.00")

    # Approve via second user (4-eyes)
    _user2, headers2 = await _create_second_user(db, test_tenant)
    r = await client.post(
        f"/api/trust-funds/transactions/{offset['id']}/approve", headers=auth_headers
    )
    assert r.status_code == 200
    r = await client.post(
        f"/api/trust-funds/transactions/{offset['id']}/approve", headers=headers2
    )
    assert r.status_code == 200, r.text
    final = r.json()
    assert final["status"] == "approved"

    # Trust balance fell by 500
    r = await client.get(f"/api/trust-funds/cases/{case_id}/balance", headers=auth_headers)
    bal = r.json()
    assert Decimal(bal["total_balance"]) == Decimal("500.00")
    assert Decimal(bal["available"]) == Decimal("500.00")

    # Invoice has a verrekening payment for 500
    r = await client.get(f"/api/invoices/{invoice['id']}/payments", headers=auth_headers)
    assert r.status_code == 200
    payments = r.json()
    assert len(payments) == 1
    assert payments[0]["payment_method"] == "verrekening"
    assert Decimal(payments[0]["amount"]) == Decimal("500.00")

    # Invoice status updated
    r = await client.get(f"/api/invoices/{invoice['id']}", headers=auth_headers)
    inv = r.json()
    if invoice_total == Decimal("500.00"):
        assert inv["status"] == "paid"
    else:
        assert inv["status"] == "partially_paid"


# ── Validation: missing consent ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_offset_rejected_without_consent_note(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
    db: AsyncSession,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    await _create_deposit(client, auth_headers, case_id, "1000.00")
    invoice = await _create_sent_invoice(client, auth_headers, str(test_company.id), db)

    payload = _consent_payload(invoice["id"], "100.00", consent_note="")
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/offsets", json=payload, headers=auth_headers
    )
    assert r.status_code == 422  # Pydantic validator rejects empty note


@pytest.mark.asyncio
async def test_offset_rejected_with_invalid_consent_method(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
    db: AsyncSession,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    await _create_deposit(client, auth_headers, case_id, "1000.00")
    invoice = await _create_sent_invoice(client, auth_headers, str(test_company.id), db)

    payload = _consent_payload(invoice["id"], "100.00", consent_method="telepathy")
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/offsets", json=payload, headers=auth_headers
    )
    assert r.status_code == 422


# ── Validation: amounts ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_offset_rejected_when_balance_too_low(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
    db: AsyncSession,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    await _create_deposit(client, auth_headers, case_id, "100.00")
    invoice = await _create_sent_invoice(client, auth_headers, str(test_company.id), db)

    payload = _consent_payload(invoice["id"], "500.00")
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/offsets", json=payload, headers=auth_headers
    )
    assert r.status_code == 400
    assert "saldo" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_offset_rejected_when_amount_exceeds_invoice_outstanding(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
    db: AsyncSession,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    await _create_deposit(client, auth_headers, case_id, "10000.00")
    # Small invoice: 10 * 100 = 1000 + 21% btw = 1210
    invoice = await _create_sent_invoice(client, auth_headers, str(test_company.id), db)

    payload = _consent_payload(invoice["id"], "5000.00")
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/offsets", json=payload, headers=auth_headers
    )
    assert r.status_code == 400
    assert "factuurbedrag" in r.json()["detail"].lower()


# ── Validation: cross-client ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_offset_rejected_when_invoice_belongs_to_other_client(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
    db: AsyncSession,
    test_tenant: Tenant,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    await _create_deposit(client, auth_headers, case_id, "1000.00")

    # Create another contact + invoice for that contact
    other = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Andere BV",
        email="ander@example.com",
    )
    db.add(other)
    await db.commit()
    await db.refresh(other)

    invoice = await _create_sent_invoice(client, auth_headers, str(other.id), db)

    payload = _consent_payload(invoice["id"], "100.00")
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/offsets", json=payload, headers=auth_headers
    )
    assert r.status_code == 400
    assert "cliënt" in r.json()["detail"] or "client" in r.json()["detail"].lower()


# ── Self-approval flag ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_offset_self_approval_when_flag_enabled(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
    db: AsyncSession,
    monkeypatch,
):
    """Default TRUST_FUNDS_ALLOW_SELF_APPROVAL=true allows solo practitioner."""
    monkeypatch.setenv("TRUST_FUNDS_ALLOW_SELF_APPROVAL", "true")
    case_id = await _create_case(client, auth_headers, case_payload)
    await _create_deposit(client, auth_headers, case_id, "1000.00")
    invoice = await _create_sent_invoice(client, auth_headers, str(test_company.id), db)

    payload = _consent_payload(invoice["id"], "300.00")
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/offsets", json=payload, headers=auth_headers
    )
    assert r.status_code == 201
    offset = r.json()

    # Same user can sign both slots
    r = await client.post(
        f"/api/trust-funds/transactions/{offset['id']}/approve", headers=auth_headers
    )
    assert r.status_code == 200
    r = await client.post(
        f"/api/trust-funds/transactions/{offset['id']}/approve", headers=auth_headers
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_offset_self_approval_blocked_when_flag_disabled(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    case_payload: dict,
    db: AsyncSession,
    monkeypatch,
):
    monkeypatch.setenv("TRUST_FUNDS_ALLOW_SELF_APPROVAL", "false")
    case_id = await _create_case(client, auth_headers, case_payload)
    await _create_deposit(client, auth_headers, case_id, "1000.00")
    invoice = await _create_sent_invoice(client, auth_headers, str(test_company.id), db)

    payload = _consent_payload(invoice["id"], "300.00")
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/offsets", json=payload, headers=auth_headers
    )
    assert r.status_code == 201
    offset = r.json()

    # Creator cannot self-approve in strict mode
    r = await client.post(
        f"/api/trust-funds/transactions/{offset['id']}/approve", headers=auth_headers
    )
    assert r.status_code == 403
