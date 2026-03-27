"""Tests for the search module — global search across cases, contacts, documents."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.relations.models import Contact

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _seed_data(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Create a contact and case for search tests."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Bakkerij Zonneveld B.V.",
        email="info@zonneveld.nl",
    )
    db.add(contact)
    await db.flush()

    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number="2026-00042",
        case_type="incasso",
        status="nieuw",
        debtor_type="b2b",
        date_opened=date.today(),
        client_id=contact.id,
        description="Openstaande facturen Zonneveld",
    )
    db.add(case)
    await db.commit()
    return {"contact": contact, "case": case}


# ── Search ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_finds_contact(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Search by contact name returns matching contact."""
    await _seed_data(db, test_tenant.id)

    resp = await client.get("/api/search?q=Zonneveld", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "Zonneveld"
    assert data["total"] >= 1
    types = [r["type"] for r in data["results"]]
    assert "contact" in types


@pytest.mark.asyncio
async def test_search_finds_case_by_number(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Search by case number returns matching case."""
    await _seed_data(db, test_tenant.id)

    resp = await client.get("/api/search?q=2026-00042", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    types = [r["type"] for r in data["results"]]
    assert "case" in types


@pytest.mark.asyncio
async def test_search_empty_result(client: AsyncClient, auth_headers: dict):
    """Search for nonexistent term returns empty results."""
    resp = await client.get("/api/search?q=xyznonexistent123", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["results"] == []


@pytest.mark.asyncio
async def test_search_requires_query(client: AsyncClient, auth_headers: dict):
    """Search without query parameter returns 422."""
    resp = await client.get("/api/search", headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_respects_limit(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Search limit parameter caps results."""
    # Create multiple contacts
    for i in range(5):
        db.add(
            Contact(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                contact_type="person",
                name=f"Testpersoon {i}",
                email=f"test{i}@example.nl",
            )
        )
    await db.commit()

    resp = await client.get("/api/search?q=Testpersoon&limit=2", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] <= 2


# ── Tenant isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_tenant_isolation(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
):
    """Search results from tenant A are not visible to tenant B."""
    await _seed_data(db, test_tenant.id)

    resp = await client.get("/api/search?q=Zonneveld", headers=second_auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


# ── Auth ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(client: AsyncClient):
    """Search without auth token returns 401."""
    resp = await client.get("/api/search?q=test")
    assert resp.status_code in (401, 403)
