"""Tests for the invoices module — CRUD, status workflow, lines, BTW, expenses."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.relations.models import Contact

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_contact(
    db: AsyncSession, tenant_id: uuid.UUID, name: str = "Acme B.V."
) -> Contact:
    """Create a minimal contact for invoice tests."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name=name,
        email=f"{name.lower().replace(' ', '').replace('.', '')}@test.nl",
    )
    db.add(contact)
    await db.flush()
    return contact


def _invoice_payload(contact_id: uuid.UUID, **overrides) -> dict:
    """Build an invoice creation payload with one line."""
    payload = {
        "contact_id": str(contact_id),
        "invoice_date": "2026-03-01",
        "due_date": "2026-03-31",
        "btw_percentage": "21.00",
        "lines": [
            {
                "description": "Juridisch advies maart 2026",
                "quantity": "2",
                "unit_price": "250.00",
            }
        ],
    }
    payload.update(overrides)
    return payload


async def _create_concept_invoice(
    client: AsyncClient, auth_headers: dict, contact_id: uuid.UUID, **overrides
) -> dict:
    """Create a concept invoice and return the response data."""
    payload = _invoice_payload(contact_id, **overrides)
    resp = await client.post("/api/invoices", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()


async def _advance_to_sent(client: AsyncClient, auth_headers: dict, invoice_id: str) -> dict:
    """Advance invoice through concept → approved → sent.

    Uses skip_email=true so the test fixtures don't need to set up an OAuth
    email account or mock the provider. The actual emailing flow is covered
    by dedicated tests in test_invoice_send_email.py.
    """
    await client.post(f"/api/invoices/{invoice_id}/approve", headers=auth_headers)
    resp = await client.post(
        f"/api/invoices/{invoice_id}/send?skip_email=true", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── Invoice CRUD ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_invoice(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Creating an invoice should return 201 with auto-generated number and correct totals."""
    contact = await _create_contact(db, test_tenant.id)
    data = await _create_concept_invoice(client, auth_headers, contact.id)

    assert data["invoice_number"].startswith("F")
    assert data["status"] == "concept"
    assert Decimal(data["subtotal"]) == Decimal("500.00")  # 2 * 250
    assert Decimal(data["btw_amount"]) == Decimal("105.00")  # 500 * 21%
    assert Decimal(data["total"]) == Decimal("605.00")  # 500 + 105
    assert len(data["lines"]) == 1


@pytest.mark.asyncio
async def test_invoice_auto_numbering(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Multiple invoices should get incrementing numbers."""
    contact = await _create_contact(db, test_tenant.id)

    numbers = []
    for _ in range(3):
        data = await _create_concept_invoice(client, auth_headers, contact.id)
        numbers.append(data["invoice_number"])

    assert numbers[0].endswith("00001")
    assert numbers[1].endswith("00002")
    assert numbers[2].endswith("00003")


@pytest.mark.asyncio
async def test_list_invoices(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Listing invoices should return paginated results."""
    contact = await _create_contact(db, test_tenant.id)
    for _ in range(3):
        await _create_concept_invoice(client, auth_headers, contact.id)

    resp = await client.get("/api/invoices", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_invoices_multi_status_filter(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """DF117-19 — status accepteert comma-gescheiden lijst voor 'openstaand'.

    'sent,partially_paid,overdue' is de frontend-filter voor openstaande
    facturen. Moet meerdere statussen kunnen matchen via IN ().
    """
    contact = await _create_contact(db, test_tenant.id)
    # 2 concept invoices (mogen NIET terugkomen bij status=sent,...)
    for _ in range(2):
        await _create_concept_invoice(client, auth_headers, contact.id)

    # Comma-filter met 1 status — alleen concept match, niet sent
    resp = await client.get(
        "/api/invoices?status=sent,partially_paid,overdue",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0  # geen van de 2 concept invoices matcht

    # Single status blijft werken (backwards compat)
    resp2 = await client.get(
        "/api/invoices?status=concept",
        headers=auth_headers,
    )
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 2

    # Comma-filter mét concept erbij — beide concept invoices matchen
    resp3 = await client.get(
        "/api/invoices?status=concept,sent",
        headers=auth_headers,
    )
    assert resp3.status_code == 200
    assert resp3.json()["total"] == 2


@pytest.mark.asyncio
async def test_get_invoice(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Getting a single invoice should return full details with lines."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)

    resp = await client.get(f"/api/invoices/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == created["id"]
    assert len(data["lines"]) == 1


@pytest.mark.asyncio
async def test_update_concept_invoice(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Updating a concept invoice should change the specified fields."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)

    resp = await client.put(
        f"/api/invoices/{created['id']}",
        json={"reference": "REF-2026-001", "notes": "Aangepaste factuur"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["reference"] == "REF-2026-001"
    assert resp.json()["notes"] == "Aangepaste factuur"


@pytest.mark.asyncio
async def test_delete_concept_invoice(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Deleting a concept invoice should soft-delete it (204)."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)

    resp = await client.delete(f"/api/invoices/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204

    # Should no longer appear in list
    list_resp = await client.get("/api/invoices", headers=auth_headers)
    assert list_resp.json()["total"] == 0


# ── Status Workflow ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_status_workflow_happy_path(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Full workflow: concept → approved → sent → paid."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)
    inv_id = created["id"]

    # Approve
    resp = await client.post(f"/api/invoices/{inv_id}/approve", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    # Send (skip_email — actual email-sending flow is covered by
    # tests/test_invoice_send_email.py)
    resp = await client.post(
        f"/api/invoices/{inv_id}/send?skip_email=true", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"

    # Record payment covering the full invoice total
    # (auto-transitions to "paid" via _update_invoice_payment_status)
    invoice_total = created["total"]
    resp = await client.post(
        f"/api/invoices/{inv_id}/payments",
        json={
            "amount": str(invoice_total),
            "payment_date": str(date.today()),
            "payment_method": "bank",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201

    # Verify the payment auto-transitioned the invoice to "paid"
    resp = await client.get(f"/api/invoices/{inv_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"
    assert resp.json()["paid_date"] is not None


@pytest.mark.asyncio
async def test_cancel_invoice(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Cancelling an invoice should change status to cancelled."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)

    resp = await client.post(f"/api/invoices/{created['id']}/cancel", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cannot_update_approved_invoice(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Updating an approved invoice should fail (400)."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)

    await client.post(f"/api/invoices/{created['id']}/approve", headers=auth_headers)

    resp = await client.put(
        f"/api/invoices/{created['id']}",
        json={"reference": "should-fail"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_cannot_delete_sent_invoice(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Deleting a sent invoice should fail (400)."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)
    await _advance_to_sent(client, auth_headers, created["id"])

    resp = await client.delete(f"/api/invoices/{created['id']}", headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_approve_empty_invoice_fails(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Approving an invoice without lines should fail (400) or creation rejects empty lines."""
    contact = await _create_contact(db, test_tenant.id)
    # Create invoice without lines
    payload = _invoice_payload(contact.id, lines=[])
    resp = await client.post("/api/invoices", json=payload, headers=auth_headers)

    if resp.status_code != 201:
        # API rejects empty invoice at creation — that's also valid
        assert resp.status_code in (400, 422)
        return

    inv_id = resp.json()["id"]
    resp = await client.post(f"/api/invoices/{inv_id}/approve", headers=auth_headers)
    assert resp.status_code == 400


# ── BTW Calculation ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_btw_calculation_precision(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """BTW calculation should use Decimal precision with ROUND_HALF_UP."""
    contact = await _create_contact(db, test_tenant.id)

    # 3 * 33.33 = 99.99 subtotal, 21% BTW = 20.9979 → 21.00 (ROUND_HALF_UP)
    payload = _invoice_payload(
        contact.id,
        lines=[{"description": "Test", "quantity": "3", "unit_price": "33.33"}],
    )
    resp = await client.post("/api/invoices", json=payload, headers=auth_headers)
    data = resp.json()

    assert Decimal(data["subtotal"]) == Decimal("99.99")
    assert Decimal(data["btw_amount"]) == Decimal("21.00")  # 99.99 * 0.21 = 20.9979 → 21.00
    assert Decimal(data["total"]) == Decimal("120.99")


@pytest.mark.asyncio
async def test_zero_btw_invoice(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Invoice with 0% BTW should have btw_amount = 0."""
    contact = await _create_contact(db, test_tenant.id)
    data = await _create_concept_invoice(client, auth_headers, contact.id, btw_percentage="0.00")

    assert Decimal(data["btw_amount"]) == Decimal("0.00")
    assert Decimal(data["total"]) == Decimal(data["subtotal"])


# ── Invoice Lines ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_line_to_concept(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Adding a line to a concept invoice should update totals."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)
    inv_id = created["id"]

    # Add a second line: 1 * 100 = 100
    resp = await client.post(
        f"/api/invoices/{inv_id}/lines",
        json={"description": "Extra werkzaamheden", "quantity": "1", "unit_price": "100.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 201

    # Verify totals updated
    inv_resp = await client.get(f"/api/invoices/{inv_id}", headers=auth_headers)
    inv_data = inv_resp.json()
    assert len(inv_data["lines"]) == 2
    assert Decimal(inv_data["subtotal"]) == Decimal("600.00")  # 500 + 100
    assert Decimal(inv_data["total"]) == Decimal("726.00")  # 600 + 126


@pytest.mark.asyncio
async def test_remove_line_from_concept(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Removing a line from a concept should update totals."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)
    inv_id = created["id"]
    line_id = created["lines"][0]["id"]

    resp = await client.delete(f"/api/invoices/{inv_id}/lines/{line_id}", headers=auth_headers)
    assert resp.status_code == 204

    # Totals should be 0
    inv_resp = await client.get(f"/api/invoices/{inv_id}", headers=auth_headers)
    assert Decimal(inv_resp.json()["subtotal"]) == Decimal("0.00")
    assert Decimal(inv_resp.json()["total"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_cannot_add_line_to_approved(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Adding a line to an approved invoice should fail (400)."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)
    inv_id = created["id"]

    await client.post(f"/api/invoices/{inv_id}/approve", headers=auth_headers)

    resp = await client.post(
        f"/api/invoices/{inv_id}/lines",
        json={"description": "Should fail", "quantity": "1", "unit_price": "50.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ── Credit Notes ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_credit_note(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Creating a credit note should link it to the original invoice and produce
    a NEGATIVE total (so it offsets the original in dossier totals)."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)
    inv_id = created["id"]

    # Must be approved/sent first
    await _advance_to_sent(client, auth_headers, inv_id)

    # User sends POSITIVE amounts (this is what the frontend dialog does — it
    # mirrors the original invoice lines with their positive values).
    cn_payload = {
        "linked_invoice_id": inv_id,
        "invoice_date": "2026-03-15",
        "due_date": "2026-04-15",
        "lines": [
            {"description": "Creditering", "quantity": "2", "unit_price": "250.00"},
        ],
    }
    resp = await client.post("/api/invoices/credit-note", json=cn_payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["invoice_number"].startswith("CN")
    assert data["invoice_type"] == "credit_note"
    assert data["linked_invoice_id"] == inv_id
    # Critical: even though positive amounts were sent, totals must be NEGATIVE
    # so they offset the original invoice in dossier totals (DF117-17 fix).
    assert Decimal(data["subtotal"]) == Decimal("-500.00"), \
        f"Credit note subtotal should be negative, got {data['subtotal']}"
    assert Decimal(data["btw_amount"]) == Decimal("-105.00"), \
        f"Credit note BTW should be negative, got {data['btw_amount']}"
    assert Decimal(data["total"]) == Decimal("-605.00"), \
        f"Credit note total should be negative, got {data['total']}"


@pytest.mark.asyncio
async def test_credit_note_negative_input_also_works(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Backwards compat: if user sends NEGATIVE amounts (old API behavior),
    the credit note should still end up with negative totals — not double-negated."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)
    inv_id = created["id"]
    await _advance_to_sent(client, auth_headers, inv_id)

    cn_payload = {
        "linked_invoice_id": inv_id,
        "invoice_date": "2026-03-15",
        "due_date": "2026-04-15",
        "lines": [
            {"description": "Creditering", "quantity": "1", "unit_price": "-250.00"},
        ],
    }
    resp = await client.post("/api/invoices/credit-note", json=cn_payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    # Should be -250 (1 line @ -250), not +250 (double-flipped) and not -500
    assert Decimal(data["subtotal"]) == Decimal("-250.00")


@pytest.mark.asyncio
async def test_credit_note_offsets_dossier_totals(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Lisanne demo 2026-04-07: a credit note must offset the linked invoice
    when summing totals on the dossier (DF117-17). Math check via list endpoint:

    invoice €605 + credit note €605 = €0 net
    """
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)
    inv_id = created["id"]
    await _advance_to_sent(client, auth_headers, inv_id)

    # Full credit
    cn_payload = {
        "linked_invoice_id": inv_id,
        "invoice_date": "2026-03-15",
        "due_date": "2026-04-15",
        "lines": [
            {"description": "Volledige creditering", "quantity": "2", "unit_price": "250.00"},
        ],
    }
    cn_resp = await client.post("/api/invoices/credit-note", json=cn_payload, headers=auth_headers)
    assert cn_resp.status_code == 201

    # List both — sum should be zero net
    list_resp = await client.get(
        f"/api/invoices?contact_id={contact.id}", headers=auth_headers
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) == 2
    net_total = sum(Decimal(str(i["total"])) for i in items)
    assert net_total == Decimal("0.00"), \
        f"Original (€605) + full credit note should net to €0.00, got €{net_total}"


@pytest.mark.asyncio
async def test_credit_note_partial_offsets_dossier_totals(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Partial credit: invoice €605 + credit note for 1 of 2 hours (€302.50)
    should net to €302.50."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)
    inv_id = created["id"]
    await _advance_to_sent(client, auth_headers, inv_id)

    cn_payload = {
        "linked_invoice_id": inv_id,
        "invoice_date": "2026-03-15",
        "due_date": "2026-04-15",
        "lines": [
            {"description": "Half crediteren", "quantity": "1", "unit_price": "250.00"},
        ],
    }
    cn_resp = await client.post("/api/invoices/credit-note", json=cn_payload, headers=auth_headers)
    assert cn_resp.status_code == 201
    cn_data = cn_resp.json()
    assert Decimal(cn_data["total"]) == Decimal("-302.50")  # -250 - 21% BTW

    list_resp = await client.get(
        f"/api/invoices?contact_id={contact.id}", headers=auth_headers
    )
    items = list_resp.json()["items"]
    net_total = sum(Decimal(str(i["total"])) for i in items)
    assert net_total == Decimal("302.50"), \
        f"€605 - €302.50 should net to €302.50, got €{net_total}"


@pytest.mark.asyncio
async def test_credit_note_preserves_per_line_btw(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """DF120 — Lisanne demo 2026-04-08:
    Creditnota mag GEEN BTW rekenen over regels die in de originele factuur
    0% (onbelaste verschotten) hadden. De per-regel BTW moet behouden blijven.

    Origineel: 1 regel €100 @ 21% + 1 regel €50 @ 0% = €171 totaal
    Volledige creditnota met correcte per-regel BTW: −€171 (NIET −€181,50)
    """
    contact = await _create_contact(db, test_tenant.id)

    # Create an invoice with TWO lines at different BTW rates
    payload = {
        "contact_id": str(contact.id),
        "invoice_date": "2026-03-01",
        "due_date": "2026-03-31",
        "btw_percentage": "21.00",  # header default, but per-line overrides
        "lines": [
            {
                "description": "Juridisch advies (belast)",
                "quantity": "1",
                "unit_price": "100.00",
                "btw_percentage": "21.00",
            },
            {
                "description": "Onbelaste verschotten (griffierecht)",
                "quantity": "1",
                "unit_price": "50.00",
                "btw_percentage": "0.00",
            },
        ],
    }
    resp = await client.post("/api/invoices", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    inv = resp.json()
    # Sanity: original invoice total is €100 + 21% = €121 + €50 = €171
    assert Decimal(inv["subtotal"]) == Decimal("150.00")
    assert Decimal(inv["btw_amount"]) == Decimal("21.00")  # only 21 on the 100
    assert Decimal(inv["total"]) == Decimal("171.00")
    inv_id = inv["id"]

    await _advance_to_sent(client, auth_headers, inv_id)

    # Create credit note mirroring the original with per-line btw_percentage
    cn_payload = {
        "linked_invoice_id": inv_id,
        "invoice_date": "2026-03-15",
        "due_date": "2026-04-15",
        "lines": [
            {
                "description": "Creditering advies",
                "quantity": "1",
                "unit_price": "100.00",
                "btw_percentage": "21.00",
            },
            {
                "description": "Creditering verschotten",
                "quantity": "1",
                "unit_price": "50.00",
                "btw_percentage": "0.00",
            },
        ],
    }
    resp = await client.post(
        "/api/invoices/credit-note", json=cn_payload, headers=auth_headers
    )
    assert resp.status_code == 201
    cn = resp.json()

    # Critical: credit note totals must mirror the original with CORRECT BTW
    assert Decimal(cn["subtotal"]) == Decimal("-150.00")
    assert Decimal(cn["btw_amount"]) == Decimal("-21.00"), \
        f"BTW on credit note should only be 21% of the €100 line, got {cn['btw_amount']}"
    assert Decimal(cn["total"]) == Decimal("-171.00"), \
        f"Credit note total should be exactly -€171.00 (not -€181.50), got {cn['total']}"

    # Per-line verification: second line has 0% BTW preserved
    cn_lines = cn["lines"]
    assert len(cn_lines) == 2
    line_by_desc = {l["description"]: l for l in cn_lines}
    assert Decimal(line_by_desc["Creditering advies"]["btw_percentage"]) == Decimal("21.00")
    assert Decimal(line_by_desc["Creditering verschotten"]["btw_percentage"]) == Decimal("0.00")

    # Dossier-level: original (+171) + credit note (-171) = 0 net
    list_resp = await client.get(
        f"/api/invoices?contact_id={contact.id}", headers=auth_headers
    )
    items = list_resp.json()["items"]
    assert len(items) == 2
    net = sum(Decimal(str(i["total"])) for i in items)
    assert net == Decimal("0.00"), f"Full credit should net to zero, got €{net}"


# ── Expenses CRUD ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_expense_crud(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Create, list, update, and delete an expense."""
    # Create
    payload = {
        "description": "Griffierecht kantonrechter",
        "amount": "85.00",
        "expense_date": "2026-03-01",
        "category": "griffierecht",
        "billable": True,
    }
    resp = await client.post("/api/expenses", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    expense = resp.json()
    assert Decimal(expense["amount"]) == Decimal("85.00")
    assert expense["category"] == "griffierecht"

    # List
    resp = await client.get("/api/expenses", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Update
    resp = await client.put(
        f"/api/expenses/{expense['id']}",
        json={"amount": "90.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert Decimal(resp.json()["amount"]) == Decimal("90.00")

    # Delete
    resp = await client.delete(f"/api/expenses/{expense['id']}", headers=auth_headers)
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get("/api/expenses", headers=auth_headers)
    assert len(resp.json()) == 0


# ── Invoice Payments (aanvullend op test_invoice_payments.py) ────────────────


@pytest.mark.asyncio
async def test_payment_summary(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Payment summary should show correct paid/outstanding amounts."""
    contact = await _create_contact(db, test_tenant.id)
    created = await _create_concept_invoice(client, auth_headers, contact.id)
    inv_id = created["id"]
    await _advance_to_sent(client, auth_headers, inv_id)

    # Record a partial payment
    await client.post(
        f"/api/invoices/{inv_id}/payments",
        json={
            "amount": "200.00",
            "payment_date": "2026-03-10",
            "payment_method": "bank",
        },
        headers=auth_headers,
    )

    # Check summary
    resp = await client.get(f"/api/invoices/{inv_id}/payment-summary", headers=auth_headers)
    assert resp.status_code == 200
    summary = resp.json()
    assert Decimal(summary["total_paid"]) == Decimal("200.00")
    assert Decimal(summary["outstanding"]) == Decimal("405.00")  # 605 - 200
    assert summary["is_fully_paid"] is False
    assert summary["payment_count"] == 1
