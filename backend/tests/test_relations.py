"""Tests for the relations module — contacts CRUD, links, and conflict check."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.relations.models import Contact

# ── List Contacts ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_contacts_empty(client: AsyncClient, auth_headers: dict):
    """Empty tenant should return no contacts."""
    response = await client.get("/api/relations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_list_contacts_with_data(
    client: AsyncClient, auth_headers: dict, test_company: Contact, test_person: Contact
):
    """Should return all active contacts for the tenant."""
    response = await client.get("/api/relations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_contacts_filter_by_type(
    client: AsyncClient, auth_headers: dict, test_company: Contact, test_person: Contact
):
    """Filtering by contact_type should work."""
    response = await client.get(
        "/api/relations?contact_type=company", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["contact_type"] == "company"


@pytest.mark.asyncio
async def test_list_contacts_search(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Search by name should filter results."""
    response = await client.get(
        "/api/relations?search=Acme", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Acme B.V."


@pytest.mark.asyncio
async def test_list_contacts_unauthenticated(client: AsyncClient):
    """Without auth header, should return 401."""
    response = await client.get("/api/relations")
    assert response.status_code == 401


# ── Create Contact ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_company(client: AsyncClient, auth_headers: dict):
    """Creating a company should return 201 with the contact data."""
    payload = {
        "contact_type": "company",
        "name": "Van den Berg Advocaten",
        "email": "info@vandenberg.nl",
        "kvk_number": "99887766",
        "visit_city": "Rotterdam",
    }
    response = await client.post("/api/relations", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Van den Berg Advocaten"
    assert data["contact_type"] == "company"
    assert data["kvk_number"] == "99887766"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_person(client: AsyncClient, auth_headers: dict):
    """Creating a person should return 201."""
    payload = {
        "contact_type": "person",
        "name": "Pieter Bakker",
        "first_name": "Pieter",
        "last_name": "Bakker",
        "email": "pieter@bakker.nl",
        "phone": "+31620000000",
    }
    response = await client.post("/api/relations", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["contact_type"] == "person"
    assert data["first_name"] == "Pieter"
    assert data["last_name"] == "Bakker"


@pytest.mark.asyncio
async def test_create_contact_invalid_type(client: AsyncClient, auth_headers: dict):
    """Invalid contact_type should return 422."""
    payload = {
        "contact_type": "alien",
        "name": "Test",
    }
    response = await client.post("/api/relations", json=payload, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_contact_missing_name(client: AsyncClient, auth_headers: dict):
    """Missing name should return 422."""
    payload = {
        "contact_type": "company",
    }
    response = await client.post("/api/relations", json=payload, headers=auth_headers)
    assert response.status_code == 422


# ── Get Contact Detail ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_contact_detail(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Getting a contact by ID should return full detail."""
    response = await client.get(
        f"/api/relations/{test_company.id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Acme B.V."
    assert data["email"] == "info@acme.nl"
    assert "linked_companies" in data
    assert "linked_persons" in data


@pytest.mark.asyncio
async def test_get_contact_not_found(client: AsyncClient, auth_headers: dict):
    """Non-existent ID should return 404."""
    fake_id = str(uuid.uuid4())
    response = await client.get(
        f"/api/relations/{fake_id}", headers=auth_headers
    )
    assert response.status_code == 404


# ── Update Contact ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_contact(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Updating a contact should change only the provided fields."""
    payload = {
        "name": "Acme International B.V.",
        "email": "global@acme.nl",
    }
    response = await client.put(
        f"/api/relations/{test_company.id}",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Acme International B.V."
    assert data["email"] == "global@acme.nl"
    # Unchanged fields should remain the same
    assert data["kvk_number"] == "12345678"


@pytest.mark.asyncio
async def test_update_contact_partial(
    client: AsyncClient, auth_headers: dict, test_person: Contact
):
    """Partial update should only change specified fields."""
    payload = {"phone": "+31699999999"}
    response = await client.put(
        f"/api/relations/{test_person.id}",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+31699999999"
    assert data["name"] == "Jan de Vries"  # Unchanged


# ── Delete Contact (soft-delete) ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_contact(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Deleting a contact should soft-delete it (set is_active=false)."""
    response = await client.delete(
        f"/api/relations/{test_company.id}", headers=auth_headers
    )
    assert response.status_code == 204

    # Verify it's gone from the default (active) list
    response = await client.get("/api/relations", headers=auth_headers)
    data = response.json()
    names = [item["name"] for item in data["items"]]
    assert "Acme B.V." not in names

    # But should appear when filtering for inactive
    response = await client.get(
        "/api/relations?is_active=false", headers=auth_headers
    )
    data = response.json()
    assert data["total"] >= 1
    names = [item["name"] for item in data["items"]]
    assert "Acme B.V." in names


# ── Contact Links ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_contact_link(
    client: AsyncClient,
    auth_headers: dict,
    test_person: Contact,
    test_company: Contact,
):
    """Linking a person to a company should return 201."""
    payload = {
        "person_id": str(test_person.id),
        "company_id": str(test_company.id),
        "role_at_company": "directeur",
    }
    response = await client.post(
        "/api/relations/links", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["person_id"] == str(test_person.id)
    assert data["company_id"] == str(test_company.id)
    assert data["role_at_company"] == "directeur"


@pytest.mark.asyncio
async def test_create_link_wrong_types(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    test_person: Contact,
):
    """Linking a company as person_id should fail with 409."""
    payload = {
        "person_id": str(test_company.id),  # Wrong — this is a company
        "company_id": str(test_person.id),  # Wrong — this is a person
    }
    response = await client.post(
        "/api/relations/links", json=payload, headers=auth_headers
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_duplicate_link(
    client: AsyncClient,
    auth_headers: dict,
    test_person: Contact,
    test_company: Contact,
):
    """Creating the same link twice should fail with 409."""
    payload = {
        "person_id": str(test_person.id),
        "company_id": str(test_company.id),
    }
    response1 = await client.post(
        "/api/relations/links", json=payload, headers=auth_headers
    )
    assert response1.status_code == 201

    response2 = await client.post(
        "/api/relations/links", json=payload, headers=auth_headers
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_get_contact_with_links(
    client: AsyncClient,
    auth_headers: dict,
    test_person: Contact,
    test_company: Contact,
):
    """After linking, the detail endpoint should show linked entities."""
    # Create a link
    payload = {
        "person_id": str(test_person.id),
        "company_id": str(test_company.id),
        "role_at_company": "contactpersoon",
    }
    await client.post("/api/relations/links", json=payload, headers=auth_headers)

    # Check person detail — should show linked company
    response = await client.get(
        f"/api/relations/{test_person.id}", headers=auth_headers
    )
    data = response.json()
    assert len(data["linked_companies"]) == 1
    assert data["linked_companies"][0]["contact"]["name"] == "Acme B.V."

    # Check company detail — should show linked person
    response = await client.get(
        f"/api/relations/{test_company.id}", headers=auth_headers
    )
    data = response.json()
    assert len(data["linked_persons"]) == 1
    assert data["linked_persons"][0]["contact"]["name"] == "Jan de Vries"


@pytest.mark.asyncio
async def test_delete_contact_link(
    client: AsyncClient,
    auth_headers: dict,
    test_person: Contact,
    test_company: Contact,
):
    """Deleting a link should remove the connection."""
    # Create a link
    payload = {
        "person_id": str(test_person.id),
        "company_id": str(test_company.id),
    }
    response = await client.post(
        "/api/relations/links", json=payload, headers=auth_headers
    )
    link_id = response.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/relations/links/{link_id}", headers=auth_headers
    )
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(
        f"/api/relations/{test_person.id}", headers=auth_headers
    )
    data = response.json()
    assert len(data["linked_companies"]) == 0


# ── Conflict Check ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_conflict_check_by_name(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Conflict check should find contacts by name."""
    payload = {"search_query": "Acme"}
    response = await client.post(
        "/api/relations/conflict-check", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results_found"] >= 1
    assert any(m["name"] == "Acme B.V." for m in data["matches"])


@pytest.mark.asyncio
async def test_conflict_check_by_kvk(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Conflict check should find contacts by KvK number."""
    payload = {"search_query": "12345678"}
    response = await client.post(
        "/api/relations/conflict-check", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results_found"] >= 1


@pytest.mark.asyncio
async def test_conflict_check_by_email(
    client: AsyncClient, auth_headers: dict, test_person: Contact
):
    """Conflict check should find contacts by email."""
    payload = {"search_query": "jan@devries.nl"}
    response = await client.post(
        "/api/relations/conflict-check", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results_found"] >= 1


@pytest.mark.asyncio
async def test_conflict_check_no_results(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Conflict check for a non-existent term should return 0 results."""
    payload = {"search_query": "XYZ-doesnt-exist-999"}
    response = await client.post(
        "/api/relations/conflict-check", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results_found"] == 0
    assert data["matches"] == []


# ── Pagination ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient, auth_headers: dict):
    """Creating many contacts and paginating should work correctly."""
    # Create 5 contacts
    for i in range(5):
        payload = {
            "contact_type": "company",
            "name": f"Bedrijf {i:03d}",
        }
        response = await client.post(
            "/api/relations", json=payload, headers=auth_headers
        )
        assert response.status_code == 201

    # Get page 1 with per_page=2
    response = await client.get(
        "/api/relations?page=1&per_page=2", headers=auth_headers
    )
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["pages"] == 3

    # Get page 3 (last page with 1 item)
    response = await client.get(
        "/api/relations?page=3&per_page=2", headers=auth_headers
    )
    data = response.json()
    assert len(data["items"]) == 1


# ── Tenant Isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tenant_isolation_list_contacts(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
    db: AsyncSession,
    second_tenant: Tenant,
    test_company: Contact,
):
    """Tenant B should NOT see contacts from Tenant A."""
    # Create a contact in Tenant B
    other_contact = Contact(
        id=uuid.uuid4(),
        tenant_id=second_tenant.id,
        contact_type="company",
        name="Other B.V.",
        email="info@other.nl",
    )
    db.add(other_contact)
    await db.commit()

    # Tenant A sees their contacts
    resp_a = await client.get("/api/relations", headers=auth_headers)
    assert resp_a.status_code == 200
    names_a = [c["name"] for c in resp_a.json()["items"]]
    assert "Acme B.V." in names_a
    assert "Other B.V." not in names_a

    # Tenant B sees their contacts
    resp_b = await client.get("/api/relations", headers=second_auth_headers)
    assert resp_b.status_code == 200
    names_b = [c["name"] for c in resp_b.json()["items"]]
    assert "Other B.V." in names_b
    assert "Acme B.V." not in names_b


@pytest.mark.asyncio
async def test_tenant_isolation_get_contact_detail(
    client: AsyncClient,
    second_auth_headers: dict,
    test_company: Contact,
):
    """Tenant B should get 404 when trying to read Tenant A's contact."""
    response = await client.get(
        f"/api/relations/{test_company.id}", headers=second_auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation_update_contact(
    client: AsyncClient,
    second_auth_headers: dict,
    test_company: Contact,
):
    """Tenant B should NOT be able to update Tenant A's contact."""
    response = await client.put(
        f"/api/relations/{test_company.id}",
        json={"name": "Hacked B.V."},
        headers=second_auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation_delete_contact(
    client: AsyncClient,
    second_auth_headers: dict,
    test_company: Contact,
):
    """Tenant B should NOT be able to delete Tenant A's contact."""
    response = await client.delete(
        f"/api/relations/{test_company.id}", headers=second_auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation_conflict_check(
    client: AsyncClient,
    second_auth_headers: dict,
    test_company: Contact,
):
    """Tenant B's conflict check should NOT find Tenant A's contacts."""
    response = await client.post(
        "/api/relations/conflict-check",
        json={"search_query": "Acme"},
        headers=second_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["results_found"] == 0
