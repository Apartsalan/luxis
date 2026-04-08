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


# ── DF117-22: BIK inheritance from client ──────────────────────────────────


@pytest_asyncio.fixture
async def bik_amount_client(db: AsyncSession, test_tenant: Tenant) -> Contact:
    """Client with default fixed BIK override of €500."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Fixed BIK BV",
        email="info@fixedbik.nl",
        default_bik_override=Decimal("500.00"),
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@pytest_asyncio.fixture
async def bik_pct_client(db: AsyncSession, test_tenant: Tenant) -> Contact:
    """Client with default BIK percentage of 12.5%."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Pct BIK BV",
        email="info@pctbik.nl",
        default_bik_override_percentage=Decimal("12.50"),
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@pytest.mark.asyncio
async def test_case_inherits_fixed_bik_from_client(
    client: AsyncClient, auth_headers: dict, bik_amount_client: Contact
):
    """When client has default_bik_override and case is created without an
    explicit override, the case should inherit the fixed amount."""
    payload = {
        "case_type": "incasso",
        "client_id": str(bik_amount_client.id),
        "date_opened": date.today().isoformat(),
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert float(data["bik_override"]) == 500.00
    assert data.get("bik_override_percentage") is None


@pytest.mark.asyncio
async def test_case_inherits_bik_percentage_from_client(
    client: AsyncClient, auth_headers: dict, bik_pct_client: Contact
):
    """When client has default_bik_override_percentage, the case inherits
    the percentage and the fixed amount stays None."""
    payload = {
        "case_type": "incasso",
        "client_id": str(bik_pct_client.id),
        "date_opened": date.today().isoformat(),
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data.get("bik_override") is None
    assert float(data["bik_override_percentage"]) == 12.50


@pytest.mark.asyncio
async def test_case_explicit_bik_overrides_client_default(
    client: AsyncClient, auth_headers: dict, bik_amount_client: Contact
):
    """Explicit bik_override on the case wins over client default."""
    payload = {
        "case_type": "incasso",
        "client_id": str(bik_amount_client.id),
        "date_opened": date.today().isoformat(),
        "bik_override": "750.00",
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert float(data["bik_override"]) == 750.00


@pytest.mark.asyncio
async def test_case_no_bik_when_client_has_none(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """When client has no default BIK, the case has no override either
    (falls back to WIK-staffel calculation)."""
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": date.today().isoformat(),
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data.get("bik_override") is None
    assert data.get("bik_override_percentage") is None


@pytest.mark.asyncio
async def test_create_contact_with_default_bik_percentage(
    client: AsyncClient, auth_headers: dict
):
    """Creating a contact with default_bik_override_percentage should persist + return."""
    payload = {
        "contact_type": "company",
        "name": "BIK Pct Test",
        "default_bik_override_percentage": "8.50",
    }
    response = await client.post("/api/relations", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert float(data["default_bik_override_percentage"]) == 8.50


# ── DF120: minimum_fee inheritance from client ───────────────────────────────


@pytest.mark.asyncio
async def test_case_inherits_minimum_fee_from_client(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    db: AsyncSession,
):
    """DF120 — when contact has default_minimum_fee, new cases inherit it."""
    test_company.default_minimum_fee = Decimal("100.00")
    await db.commit()

    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": date.today().isoformat(),
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert float(data["minimum_fee"]) == 100.00


@pytest.mark.asyncio
async def test_case_minimum_fee_explicit_overrides_client_default(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    db: AsyncSession,
):
    """An explicit minimum_fee on case create should override the client default."""
    test_company.default_minimum_fee = Decimal("100.00")
    await db.commit()

    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": date.today().isoformat(),
        "minimum_fee": "75.00",
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert float(data["minimum_fee"]) == 75.00


@pytest.mark.asyncio
async def test_case_no_minimum_fee_when_client_has_none(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """No client default → case has no minimum_fee (falls back to system default)."""
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": date.today().isoformat(),
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    assert response.json().get("minimum_fee") is None
