"""Tests for default interest inheritance from Contact → Case.

Lisanne demo 2026-04-07: she wants to set a default interest rate per client (relatie)
that is automatically applied when creating a new case for that client, with the
option to override per case.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.relations.models import Contact


@pytest_asyncio.fixture
async def commercial_client(db: AsyncSession, test_tenant: Tenant) -> Contact:
    """Client contact with default_interest_type = commercial."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Commercial Corp B.V.",
        email="info@commercialcorp.nl",
        default_interest_type="commercial",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@pytest_asyncio.fixture
async def contractual_client(db: AsyncSession, test_tenant: Tenant) -> Contact:
    """Client contact with default_interest_type = contractual @ 8.50%."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Contract Co B.V.",
        email="info@contractco.nl",
        default_interest_type="contractual",
        default_contractual_rate=Decimal("8.50"),
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


# ── Inheritance ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_case_inherits_commercial_from_client(
    client: AsyncClient, auth_headers: dict, commercial_client: Contact
):
    """When client has default_interest_type=commercial and case is created
    without an explicit interest_type, the case should inherit commercial."""
    payload = {
        "case_type": "incasso",
        "client_id": str(commercial_client.id),
        "date_opened": date.today().isoformat(),
        # No interest_type — should inherit
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["interest_type"] == "commercial"


@pytest.mark.asyncio
async def test_case_inherits_contractual_with_rate_from_client(
    client: AsyncClient, auth_headers: dict, contractual_client: Contact
):
    """Client with contractual default + rate → case inherits both."""
    payload = {
        "case_type": "incasso",
        "client_id": str(contractual_client.id),
        "date_opened": date.today().isoformat(),
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["interest_type"] == "contractual"
    assert float(data["contractual_rate"]) == 8.50


@pytest.mark.asyncio
async def test_case_explicit_override_wins_over_client_default(
    client: AsyncClient, auth_headers: dict, commercial_client: Contact
):
    """When the case explicitly sends interest_type, the client default is ignored."""
    payload = {
        "case_type": "incasso",
        "client_id": str(commercial_client.id),
        "interest_type": "statutory",  # Override
        "date_opened": date.today().isoformat(),
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["interest_type"] == "statutory"


@pytest.mark.asyncio
async def test_case_falls_back_to_statutory_when_client_has_no_default(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """When client has no default_interest_type, the case falls back to statutory."""
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": date.today().isoformat(),
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["interest_type"] == "statutory"


# ── Contact CRUD with rente fields ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_contact_with_default_interest(
    client: AsyncClient, auth_headers: dict
):
    """Creating a contact with default_interest_type should persist + return it."""
    payload = {
        "contact_type": "company",
        "name": "New Test BV",
        "default_interest_type": "commercial",
    }
    response = await client.post("/api/relations", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["default_interest_type"] == "commercial"

    # Read back
    contact_id = data["id"]
    get_response = await client.get(f"/api/relations/{contact_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["default_interest_type"] == "commercial"


@pytest.mark.asyncio
async def test_update_contact_default_interest_to_contractual(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Updating a contact to contractual rate should persist both fields."""
    payload = {
        "default_interest_type": "contractual",
        "default_contractual_rate": "10.00",
    }
    response = await client.put(
        f"/api/relations/{test_company.id}", json=payload, headers=auth_headers
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["default_interest_type"] == "contractual"
    assert float(data["default_contractual_rate"]) == 10.00
