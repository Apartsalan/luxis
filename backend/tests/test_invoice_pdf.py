"""Tests for invoice PDF generation endpoint."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.relations.models import Contact

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_contact(
    db: AsyncSession, tenant_id: uuid.UUID, name: str = "Test Klant B.V."
) -> Contact:
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name=name,
        visit_address="Keizersgracht 100",
        visit_postcode="1015 AA",
        visit_city="Amsterdam",
        email="info@testklant.nl",
    )
    db.add(contact)
    await db.flush()
    return contact


def _invoice_payload(contact_id: uuid.UUID) -> dict:
    return {
        "contact_id": str(contact_id),
        "invoice_date": "2026-03-01",
        "due_date": "2026-03-31",
        "btw_percentage": "21.00",
        "reference": "Zaak 2026-001",
        "lines": [
            {
                "description": "Juridisch advies maart 2026",
                "quantity": "2",
                "unit_price": "250.00",
            },
            {
                "description": "Griffierecht",
                "quantity": "1",
                "unit_price": "86.00",
            },
        ],
    }


async def _create_concept_invoice(
    client: AsyncClient, auth_headers: dict, contact_id: uuid.UUID
) -> dict:
    payload = _invoice_payload(contact_id)
    resp = await client.post("/api/invoices", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.skipif(
    not __import__("pathlib").Path("/opt/luxis/backend/templates/factuur.html").exists()
    and not __import__("pathlib").Path("templates/factuur.html").exists(),
    reason="factuur.html template not available in CI",
)
async def test_download_invoice_pdf(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Download PDF should return valid PDF bytes with correct headers."""
    contact = await _create_contact(db, test_tenant.id)
    invoice = await _create_concept_invoice(client, auth_headers, contact.id)
    invoice_id = invoice["id"]

    resp = await client.get(f"/api/invoices/{invoice_id}/pdf", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment" in resp.headers["content-disposition"]
    assert invoice["invoice_number"] in resp.headers["content-disposition"]
    # PDF magic bytes
    assert resp.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_download_pdf_not_found(client: AsyncClient, auth_headers: dict):
    """Requesting PDF for non-existent invoice should return 404."""
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/invoices/{fake_id}/pdf", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_download_pdf_approved_status(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """PDF should work for approved invoices too."""
    contact = await _create_contact(db, test_tenant.id)
    invoice = await _create_concept_invoice(client, auth_headers, contact.id)
    invoice_id = invoice["id"]

    # Advance to approved
    resp = await client.post(f"/api/invoices/{invoice_id}/approve", headers=auth_headers)
    assert resp.status_code == 200

    resp = await client.get(f"/api/invoices/{invoice_id}/pdf", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_pdf_contains_correct_totals(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """PDF content should include invoice number and formatted amounts."""
    contact = await _create_contact(db, test_tenant.id)
    invoice = await _create_concept_invoice(client, auth_headers, contact.id)
    invoice_id = invoice["id"]

    resp = await client.get(f"/api/invoices/{invoice_id}/pdf", headers=auth_headers)
    assert resp.status_code == 200

    # Verify the invoice number appears in the filename
    assert invoice["invoice_number"] in resp.headers["content-disposition"]

    # Verify expected totals: 2*250 + 1*86 = 586 subtotal, 123.06 btw, 709.06 total
    assert invoice["subtotal"] == "586.00"
    assert invoice["total"] == "709.06"
