"""Tests for claims CRUD — LF-06 (case financial cache) and LF-08 (claim edit)."""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.relations.models import Contact


# ── Helper: create a case ────────────────────────────────────────────────────


async def _create_case(client: AsyncClient, headers: dict, client_id: str) -> dict:
    """Create an incasso case and return JSON response."""
    payload = {
        "case_type": "incasso",
        "description": "Test incassodossier",
        "interest_type": "statutory",
        "client_id": client_id,
        "date_opened": date.today().isoformat(),
    }
    resp = await client.post("/api/cases", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()


# ── LF-06: Case financial cache updated after claim CRUD ─────────────────────


@pytest.mark.asyncio
async def test_create_claim_updates_case_total_principal(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """After creating a claim, Case.total_principal should reflect the sum."""
    case = await _create_case(client, auth_headers, str(test_company.id))
    case_id = case["id"]

    # Initially total_principal should be 0
    resp = await client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert Decimal(str(resp.json()["total_principal"])) == Decimal("0")

    # Create a claim
    claim_payload = {
        "description": "Factuur 2024-001",
        "principal_amount": "1500.00",
        "default_date": date.today().isoformat(),
    }
    resp = await client.post(
        f"/api/cases/{case_id}/claims", json=claim_payload, headers=auth_headers
    )
    assert resp.status_code == 201

    # Case total_principal should now be 1500.00
    resp = await client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert Decimal(str(resp.json()["total_principal"])) == Decimal("1500.00")


@pytest.mark.asyncio
async def test_multiple_claims_sum_in_total_principal(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Multiple claims should sum to total_principal."""
    case = await _create_case(client, auth_headers, str(test_company.id))
    case_id = case["id"]

    for amount in ["1000.00", "2500.50", "750.25"]:
        resp = await client.post(
            f"/api/cases/{case_id}/claims",
            json={
                "description": f"Factuur {amount}",
                "principal_amount": amount,
                "default_date": date.today().isoformat(),
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201

    resp = await client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert Decimal(str(resp.json()["total_principal"])) == Decimal("4250.75")


@pytest.mark.asyncio
async def test_delete_claim_updates_total_principal(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Deleting a claim should reduce total_principal."""
    case = await _create_case(client, auth_headers, str(test_company.id))
    case_id = case["id"]

    # Create two claims
    resp1 = await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Claim 1",
            "principal_amount": "1000.00",
            "default_date": date.today().isoformat(),
        },
        headers=auth_headers,
    )
    claim1_id = resp1.json()["id"]

    await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Claim 2",
            "principal_amount": "500.00",
            "default_date": date.today().isoformat(),
        },
        headers=auth_headers,
    )

    # Total should be 1500
    resp = await client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert Decimal(str(resp.json()["total_principal"])) == Decimal("1500.00")

    # Delete first claim
    resp = await client.delete(f"/api/cases/{case_id}/claims/{claim1_id}", headers=auth_headers)
    assert resp.status_code == 204

    # Total should now be 500
    resp = await client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert Decimal(str(resp.json()["total_principal"])) == Decimal("500.00")


# ── LF-08: Claim update ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_claim(client: AsyncClient, auth_headers: dict, test_company: Contact):
    """Should be able to update all claim fields."""
    case = await _create_case(client, auth_headers, str(test_company.id))
    case_id = case["id"]

    # Create a claim
    resp = await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Origineel",
            "principal_amount": "1000.00",
            "default_date": "2025-01-15",
        },
        headers=auth_headers,
    )
    claim_id = resp.json()["id"]

    # Update it
    resp = await client.put(
        f"/api/cases/{case_id}/claims/{claim_id}",
        json={
            "description": "Bijgewerkt",
            "principal_amount": "2000.00",
            "default_date": "2025-02-01",
            "invoice_number": "INV-2025-001",
            "invoice_date": "2025-01-10",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Bijgewerkt"
    assert Decimal(str(data["principal_amount"])) == Decimal("2000.00")
    assert data["default_date"] == "2025-02-01"
    assert data["invoice_number"] == "INV-2025-001"
    assert data["invoice_date"] == "2025-01-10"


@pytest.mark.asyncio
async def test_update_claim_partial(client: AsyncClient, auth_headers: dict, test_company: Contact):
    """Partial update should only change specified fields."""
    case = await _create_case(client, auth_headers, str(test_company.id))
    case_id = case["id"]

    resp = await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Origineel",
            "principal_amount": "1000.00",
            "default_date": "2025-01-15",
        },
        headers=auth_headers,
    )
    claim_id = resp.json()["id"]

    # Only update description
    resp = await client.put(
        f"/api/cases/{case_id}/claims/{claim_id}",
        json={"description": "Alleen beschrijving gewijzigd"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Alleen beschrijving gewijzigd"
    assert Decimal(str(data["principal_amount"])) == Decimal("1000.00")
    assert data["default_date"] == "2025-01-15"


@pytest.mark.asyncio
async def test_update_claim_updates_total_principal(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Updating a claim amount should update Case.total_principal."""
    case = await _create_case(client, auth_headers, str(test_company.id))
    case_id = case["id"]

    resp = await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Test",
            "principal_amount": "1000.00",
            "default_date": date.today().isoformat(),
        },
        headers=auth_headers,
    )
    claim_id = resp.json()["id"]

    # Verify initial total
    resp = await client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert Decimal(str(resp.json()["total_principal"])) == Decimal("1000.00")

    # Update amount
    resp = await client.put(
        f"/api/cases/{case_id}/claims/{claim_id}",
        json={"principal_amount": "3000.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    # Total should now be 3000
    resp = await client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert Decimal(str(resp.json()["total_principal"])) == Decimal("3000.00")


@pytest.mark.asyncio
async def test_update_nonexistent_claim_returns_404(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Updating a non-existent claim should return 404."""
    case = await _create_case(client, auth_headers, str(test_company.id))
    case_id = case["id"]
    fake_id = "00000000-0000-0000-0000-000000000001"

    resp = await client.put(
        f"/api/cases/{case_id}/claims/{fake_id}",
        json={"description": "Bestaat niet"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ── DF120: rate_basis inheritance per client ─────────────────────────────────


@pytest.mark.asyncio
async def test_claim_inherits_rate_basis_from_client(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    db,
):
    """DF120 — Lisanne demo 2026-04-08:
    When a contact has default_rate_basis="monthly", new claims on cases for
    that client should default to monthly basis (no need to set per claim).
    """
    # Set the default on the client
    test_company.default_rate_basis = "monthly"
    await db.commit()

    case = await _create_case(client, auth_headers, str(test_company.id))
    case_id = case["id"]

    # Create a claim WITHOUT specifying rate_basis
    resp = await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Factuur zonder expliciete rate_basis",
            "principal_amount": "1000.00",
            "default_date": date.today().isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["rate_basis"] == "monthly"

    # Now create a claim WITH explicit rate_basis — should override
    resp = await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Factuur met expliciete yearly",
            "principal_amount": "500.00",
            "default_date": date.today().isoformat(),
            "rate_basis": "yearly",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["rate_basis"] == "yearly"


@pytest.mark.asyncio
async def test_claim_falls_back_to_yearly_without_client_default(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """When a contact has no default_rate_basis, claims default to yearly."""
    case = await _create_case(client, auth_headers, str(test_company.id))
    case_id = case["id"]

    resp = await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Factuur zonder klant-default",
            "principal_amount": "1000.00",
            "default_date": date.today().isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["rate_basis"] == "yearly"
