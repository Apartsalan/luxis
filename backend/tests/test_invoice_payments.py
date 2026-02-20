"""Tests for invoice payments — C2 betalingstracking op facturen.

Covers: create payment, overpayment guard, auto-status transitions,
list payments, delete payment, payment summary, decimal precision.
"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.auth.models import Tenant
from app.relations.models import Contact


# ── Helpers ──────────────────────────────────────────────────────────────────


async def create_sent_invoice(
    client: AsyncClient,
    auth_headers: dict,
    contact_id: str,
    lines: list[dict] | None = None,
) -> dict:
    """Create an invoice and advance it to 'sent' status.

    Returns the full invoice response dict.
    """
    if lines is None:
        lines = [
            {"description": "Juridisch advies", "quantity": "10", "unit_price": "200.00"},
        ]

    # Create
    invoice_data = {
        "contact_id": contact_id,
        "invoice_date": "2026-02-01",
        "due_date": "2026-03-01",
        "btw_percentage": "21.00",
        "lines": lines,
    }
    response = await client.post("/api/invoices", json=invoice_data, headers=auth_headers)
    assert response.status_code == 201
    invoice = response.json()

    # Approve
    response = await client.post(
        f"/api/invoices/{invoice['id']}/approve", headers=auth_headers
    )
    assert response.status_code == 200

    # Send
    response = await client.post(
        f"/api/invoices/{invoice['id']}/send", headers=auth_headers
    )
    assert response.status_code == 200
    return response.json()


# ── Create Payment ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_payment(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Creating a payment on a sent invoice should return 201."""
    invoice = await create_sent_invoice(client, auth_headers, str(test_company.id))
    invoice_total = Decimal(invoice["total"])

    payment = {
        "amount": "500.00",
        "payment_date": "2026-02-15",
        "payment_method": "bank",
        "reference": "INGB-2026-001",
        "description": "Eerste deelbetaling",
    }
    response = await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json=payment,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["amount"]) == Decimal("500.00")
    assert data["payment_method"] == "bank"
    assert data["reference"] == "INGB-2026-001"
    assert data["description"] == "Eerste deelbetaling"
    assert data["payment_date"] == "2026-02-15"
    assert "creator" in data
    assert data["creator"]["email"] == "lisanne@kestinglegal.nl"


@pytest.mark.asyncio
async def test_create_payment_invalid_method(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """An invalid payment method should return 400."""
    invoice = await create_sent_invoice(client, auth_headers, str(test_company.id))

    payment = {
        "amount": "100.00",
        "payment_date": "2026-02-15",
        "payment_method": "bitcoin",
    }
    response = await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json=payment,
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "betaalmethode" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_payment_on_concept_invoice_fails(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Payments on concept invoices should be rejected."""
    invoice_data = {
        "contact_id": str(test_company.id),
        "invoice_date": "2026-02-01",
        "due_date": "2026-03-01",
        "lines": [{"description": "Test", "quantity": "1", "unit_price": "100.00"}],
    }
    response = await client.post("/api/invoices", json=invoice_data, headers=auth_headers)
    invoice_id = response.json()["id"]

    payment = {
        "amount": "50.00",
        "payment_date": "2026-02-15",
        "payment_method": "bank",
    }
    response = await client.post(
        f"/api/invoices/{invoice_id}/payments",
        json=payment,
        headers=auth_headers,
    )
    assert response.status_code == 400


# ── Overpayment Guard ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_overpayment_rejected(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Payment exceeding the outstanding amount should be rejected."""
    invoice = await create_sent_invoice(
        client, auth_headers, str(test_company.id),
        lines=[{"description": "Advies", "quantity": "1", "unit_price": "100.00"}],
    )
    invoice_total = Decimal(invoice["total"])  # 121.00 (100 + 21% BTW)

    # Try to pay more than the total
    payment = {
        "amount": "200.00",
        "payment_date": "2026-02-15",
        "payment_method": "bank",
    }
    response = await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json=payment,
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "overschrijdt" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cumulative_overpayment_rejected(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Second payment that would exceed total should be rejected."""
    invoice = await create_sent_invoice(
        client, auth_headers, str(test_company.id),
        lines=[{"description": "Advies", "quantity": "1", "unit_price": "100.00"}],
    )
    # Total = 121.00

    # First payment: 100.00
    payment1 = {
        "amount": "100.00",
        "payment_date": "2026-02-15",
        "payment_method": "bank",
    }
    response = await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json=payment1,
        headers=auth_headers,
    )
    assert response.status_code == 201

    # Second payment: 25.00 would exceed 121.00 total
    payment2 = {
        "amount": "25.00",
        "payment_date": "2026-02-16",
        "payment_method": "ideal",
    }
    response = await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json=payment2,
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "overschrijdt" in response.json()["detail"].lower()


# ── Auto-Status Transitions ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_partial_payment_sets_partially_paid(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """A partial payment should set invoice status to partially_paid."""
    invoice = await create_sent_invoice(client, auth_headers, str(test_company.id))
    # Total = 2420.00 (10 * 200 + 21% BTW)

    payment = {
        "amount": "1000.00",
        "payment_date": "2026-02-15",
        "payment_method": "bank",
    }
    await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json=payment,
        headers=auth_headers,
    )

    # Check invoice status
    response = await client.get(
        f"/api/invoices/{invoice['id']}", headers=auth_headers
    )
    assert response.json()["status"] == "partially_paid"
    assert response.json()["paid_date"] is None


@pytest.mark.asyncio
async def test_full_payment_sets_paid(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Paying the full amount should set invoice status to paid."""
    invoice = await create_sent_invoice(
        client, auth_headers, str(test_company.id),
        lines=[{"description": "Advies", "quantity": "1", "unit_price": "100.00"}],
    )
    invoice_total = invoice["total"]  # "121.00"

    payment = {
        "amount": invoice_total,
        "payment_date": "2026-02-20",
        "payment_method": "ideal",
    }
    await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json=payment,
        headers=auth_headers,
    )

    response = await client.get(
        f"/api/invoices/{invoice['id']}", headers=auth_headers
    )
    assert response.json()["status"] == "paid"
    assert response.json()["paid_date"] is not None


@pytest.mark.asyncio
async def test_multiple_payments_to_fully_paid(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Multiple partial payments summing to total should set status to paid."""
    invoice = await create_sent_invoice(
        client, auth_headers, str(test_company.id),
        lines=[{"description": "Advies", "quantity": "1", "unit_price": "100.00"}],
    )
    # Total = 121.00

    # Payment 1: 60.00
    await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json={"amount": "60.00", "payment_date": "2026-02-15", "payment_method": "bank"},
        headers=auth_headers,
    )

    # Check: partially_paid
    response = await client.get(f"/api/invoices/{invoice['id']}", headers=auth_headers)
    assert response.json()["status"] == "partially_paid"

    # Payment 2: 61.00 (total now 121.00)
    await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json={"amount": "61.00", "payment_date": "2026-02-20", "payment_method": "bank"},
        headers=auth_headers,
    )

    # Check: paid
    response = await client.get(f"/api/invoices/{invoice['id']}", headers=auth_headers)
    assert response.json()["status"] == "paid"


# ── List Payments ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_payments(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Listing payments returns all payments for the invoice."""
    invoice = await create_sent_invoice(client, auth_headers, str(test_company.id))

    # Create 3 payments
    for i in range(3):
        await client.post(
            f"/api/invoices/{invoice['id']}/payments",
            json={
                "amount": "100.00",
                "payment_date": f"2026-02-{15 + i:02d}",
                "payment_method": "bank",
                "description": f"Betaling {i + 1}",
            },
            headers=auth_headers,
        )

    response = await client.get(
        f"/api/invoices/{invoice['id']}/payments",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_list_payments_empty(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Listing payments on an invoice with no payments returns empty list."""
    invoice = await create_sent_invoice(client, auth_headers, str(test_company.id))

    response = await client.get(
        f"/api/invoices/{invoice['id']}/payments",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == []


# ── Delete Payment ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_payment(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Deleting a payment should remove it and update the invoice status."""
    invoice = await create_sent_invoice(
        client, auth_headers, str(test_company.id),
        lines=[{"description": "Advies", "quantity": "1", "unit_price": "100.00"}],
    )

    # Create payment (full amount)
    response = await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json={"amount": "121.00", "payment_date": "2026-02-15", "payment_method": "bank"},
        headers=auth_headers,
    )
    payment_id = response.json()["id"]

    # Invoice should be paid
    inv = await client.get(f"/api/invoices/{invoice['id']}", headers=auth_headers)
    assert inv.json()["status"] == "paid"

    # Delete payment
    response = await client.delete(
        f"/api/invoices/{invoice['id']}/payments/{payment_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Invoice should revert to sent
    inv = await client.get(f"/api/invoices/{invoice['id']}", headers=auth_headers)
    assert inv.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_delete_payment_reverts_to_partially_paid(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Deleting one of multiple payments should revert to partially_paid."""
    invoice = await create_sent_invoice(
        client, auth_headers, str(test_company.id),
        lines=[{"description": "Advies", "quantity": "1", "unit_price": "100.00"}],
    )
    # Total = 121.00

    # Payment 1: 60.00
    await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json={"amount": "60.00", "payment_date": "2026-02-15", "payment_method": "bank"},
        headers=auth_headers,
    )

    # Payment 2: 61.00 → fully paid
    response = await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json={"amount": "61.00", "payment_date": "2026-02-20", "payment_method": "bank"},
        headers=auth_headers,
    )
    payment2_id = response.json()["id"]

    inv = await client.get(f"/api/invoices/{invoice['id']}", headers=auth_headers)
    assert inv.json()["status"] == "paid"

    # Delete payment 2 → back to partially_paid
    await client.delete(
        f"/api/invoices/{invoice['id']}/payments/{payment2_id}",
        headers=auth_headers,
    )

    inv = await client.get(f"/api/invoices/{invoice['id']}", headers=auth_headers)
    assert inv.json()["status"] == "partially_paid"


@pytest.mark.asyncio
async def test_delete_nonexistent_payment(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Deleting a nonexistent payment should return 404."""
    invoice = await create_sent_invoice(client, auth_headers, str(test_company.id))
    fake_id = str(uuid.uuid4())

    response = await client.delete(
        f"/api/invoices/{invoice['id']}/payments/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ── Payment Summary ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_payment_summary(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Payment summary should show correct totals."""
    invoice = await create_sent_invoice(
        client, auth_headers, str(test_company.id),
        lines=[{"description": "Advies", "quantity": "1", "unit_price": "100.00"}],
    )
    # Total = 121.00

    # Create two payments
    await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json={"amount": "50.00", "payment_date": "2026-02-15", "payment_method": "bank"},
        headers=auth_headers,
    )
    await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json={"amount": "30.00", "payment_date": "2026-02-16", "payment_method": "ideal"},
        headers=auth_headers,
    )

    response = await client.get(
        f"/api/invoices/{invoice['id']}/payment-summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["invoice_total"]) == Decimal("121.00")
    assert Decimal(data["total_paid"]) == Decimal("80.00")
    assert Decimal(data["outstanding"]) == Decimal("41.00")
    assert data["payment_count"] == 2
    assert data["is_fully_paid"] is False


@pytest.mark.asyncio
async def test_payment_summary_empty(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Payment summary with no payments should show full amount outstanding."""
    invoice = await create_sent_invoice(
        client, auth_headers, str(test_company.id),
        lines=[{"description": "Advies", "quantity": "1", "unit_price": "100.00"}],
    )

    response = await client.get(
        f"/api/invoices/{invoice['id']}/payment-summary",
        headers=auth_headers,
    )
    data = response.json()
    assert Decimal(data["total_paid"]) == Decimal("0.00")
    assert Decimal(data["outstanding"]) == Decimal("121.00")
    assert data["payment_count"] == 0
    assert data["is_fully_paid"] is False


@pytest.mark.asyncio
async def test_payment_summary_fully_paid(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Payment summary for a fully paid invoice."""
    invoice = await create_sent_invoice(
        client, auth_headers, str(test_company.id),
        lines=[{"description": "Advies", "quantity": "1", "unit_price": "100.00"}],
    )

    await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json={"amount": "121.00", "payment_date": "2026-02-20", "payment_method": "bank"},
        headers=auth_headers,
    )

    response = await client.get(
        f"/api/invoices/{invoice['id']}/payment-summary",
        headers=auth_headers,
    )
    data = response.json()
    assert Decimal(data["outstanding"]) == Decimal("0.00")
    assert data["is_fully_paid"] is True


# ── Decimal Precision ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decimal_precision(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Financial amounts must maintain exact decimal precision."""
    invoice = await create_sent_invoice(client, auth_headers, str(test_company.id))

    payment = {
        "amount": "1234.56",
        "payment_date": "2026-02-15",
        "payment_method": "bank",
    }
    response = await client.post(
        f"/api/invoices/{invoice['id']}/payments",
        json=payment,
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert Decimal(response.json()["amount"]) == Decimal("1234.56")

    # Verify summary precision
    response = await client.get(
        f"/api/invoices/{invoice['id']}/payment-summary",
        headers=auth_headers,
    )
    assert Decimal(response.json()["total_paid"]) == Decimal("1234.56")


# ── Payment Methods ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_all_valid_payment_methods(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """All valid payment methods should be accepted."""
    invoice = await create_sent_invoice(client, auth_headers, str(test_company.id))
    # Total = 2420.00

    methods = ["bank", "ideal", "cash", "verrekening"]
    for method in methods:
        response = await client.post(
            f"/api/invoices/{invoice['id']}/payments",
            json={
                "amount": "100.00",
                "payment_date": "2026-02-15",
                "payment_method": method,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201, f"Method '{method}' should be accepted"
        assert response.json()["payment_method"] == method
