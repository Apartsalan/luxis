"""Tests for the cases module — case CRUD, status workflow, parties, activities."""

import uuid

import pytest
from httpx import AsyncClient

from app.relations.models import Contact

# ── Create Case ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_case(
    client: AsyncClient, auth_headers: dict, test_company: Contact, test_person: Contact
):
    """Creating a case should return 201 with auto-generated case number."""
    payload = {
        "case_type": "incasso",
        "description": "Onbetaalde factuur van €5.000",
        "interest_type": "statutory",
        "client_id": str(test_company.id),
        "opposing_party_id": str(test_person.id),
        "date_opened": "2026-02-17",
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["case_number"].startswith("2026-")
    assert data["case_type"] == "incasso"
    assert data["status"] == "nieuw"
    assert data["interest_type"] == "statutory"
    assert data["client"]["name"] == "Acme B.V."
    assert data["opposing_party"]["name"] == "Jan de Vries"


@pytest.mark.asyncio
async def test_create_case_auto_increment(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Multiple cases should get incrementing case numbers."""
    for _ in range(3):
        payload = {
            "case_type": "incasso",
            "client_id": str(test_company.id),
            "date_opened": "2026-02-17",
        }
        await client.post("/api/cases", json=payload, headers=auth_headers)

    response = await client.get("/api/cases", headers=auth_headers)
    data = response.json()
    numbers = sorted([item["case_number"] for item in data["items"]])
    assert numbers == ["2026-00001", "2026-00002", "2026-00003"]


@pytest.mark.asyncio
async def test_create_case_contractual_interest(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Contractual interest requires a rate."""
    # Without rate — should fail
    payload = {
        "case_type": "incasso",
        "interest_type": "contractual",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 400

    # With rate — should succeed
    payload["contractual_rate"] = 8.0
    response = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert float(data["contractual_rate"]) == 8.0


# ── List Cases ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_cases_empty(client: AsyncClient, auth_headers: dict):
    """Empty tenant should return no cases."""
    response = await client.get("/api/cases", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_cases_filter_by_type(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Filtering by case_type should work."""
    # Create an incasso case
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    await client.post("/api/cases", json=payload, headers=auth_headers)

    # Create an advies case
    payload["case_type"] = "advies"
    await client.post("/api/cases", json=payload, headers=auth_headers)

    # Filter by incasso
    response = await client.get("/api/cases?case_type=incasso", headers=auth_headers)
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["case_type"] == "incasso"


# ── Get Case Detail ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_case_detail(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Getting a case by ID should return full detail."""
    # Create case
    payload = {
        "case_type": "incasso",
        "description": "Test zaak",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    create_response = await client.post("/api/cases", json=payload, headers=auth_headers)
    case_id = create_response.json()["id"]

    # Get detail
    response = await client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Test zaak"
    assert "parties" in data
    assert "recent_activities" in data
    # Should have 1 activity (creation)
    assert len(data["recent_activities"]) >= 1
    assert data["recent_activities"][0]["activity_type"] == "status_change"


@pytest.mark.asyncio
async def test_get_case_not_found(client: AsyncClient, auth_headers: dict):
    """Non-existent ID should return 404."""
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/cases/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


# ── Update Case ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_case(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Updating case details should work."""
    # Create case
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    create_response = await client.post("/api/cases", json=payload, headers=auth_headers)
    case_id = create_response.json()["id"]

    # Update
    update_payload = {
        "description": "Bijgewerkte beschrijving",
        "reference": "KL-REF-001",
    }
    response = await client.put(
        f"/api/cases/{case_id}", json=update_payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Bijgewerkte beschrijving"
    assert data["reference"] == "KL-REF-001"


# ── Status Workflow ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_status_workflow(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Status transitions should follow the allowed workflow."""
    # Create case (status: nieuw)
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    create_response = await client.post("/api/cases", json=payload, headers=auth_headers)
    case_id = create_response.json()["id"]

    # nieuw → 14_dagenbrief
    response = await client.post(
        f"/api/cases/{case_id}/status",
        json={"new_status": "14_dagenbrief", "note": "Brief verstuurd"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "14_dagenbrief"

    # 14_dagenbrief → sommatie
    response = await client.post(
        f"/api/cases/{case_id}/status",
        json={"new_status": "sommatie"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "sommatie"


@pytest.mark.asyncio
async def test_status_invalid_transition(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Invalid status transitions should return 409."""
    # Create case (status: nieuw)
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    create_response = await client.post("/api/cases", json=payload, headers=auth_headers)
    case_id = create_response.json()["id"]

    # nieuw → vonnis (NOT allowed — must go through 14_dagenbrief, sommatie, dagvaarding first)
    response = await client.post(
        f"/api/cases/{case_id}/status",
        json={"new_status": "vonnis"},
        headers=auth_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_status_change_sets_date_closed(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Moving to 'betaald' or 'afgesloten' should set date_closed."""
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    create_response = await client.post("/api/cases", json=payload, headers=auth_headers)
    case_id = create_response.json()["id"]

    # nieuw → afgesloten
    response = await client.post(
        f"/api/cases/{case_id}/status",
        json={"new_status": "afgesloten"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["date_closed"] is not None


# ── Case Parties ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_case_party(
    client: AsyncClient, auth_headers: dict, test_company: Contact, test_person: Contact
):
    """Adding a party to a case should work."""
    # Create case
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    create_response = await client.post("/api/cases", json=payload, headers=auth_headers)
    case_id = create_response.json()["id"]

    # Add party
    party_payload = {
        "contact_id": str(test_person.id),
        "role": "deurwaarder",
    }
    response = await client.post(
        f"/api/cases/{case_id}/parties", json=party_payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "deurwaarder"
    assert data["contact"]["name"] == "Jan de Vries"


@pytest.mark.asyncio
async def test_remove_case_party(
    client: AsyncClient, auth_headers: dict, test_company: Contact, test_person: Contact
):
    """Removing a party from a case should work."""
    # Create case
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    create_response = await client.post("/api/cases", json=payload, headers=auth_headers)
    case_id = create_response.json()["id"]

    # Add party
    party_payload = {"contact_id": str(test_person.id), "role": "deurwaarder"}
    party_response = await client.post(
        f"/api/cases/{case_id}/parties", json=party_payload, headers=auth_headers
    )
    party_id = party_response.json()["id"]

    # Remove party
    response = await client.delete(
        f"/api/cases/{case_id}/parties/{party_id}", headers=auth_headers
    )
    assert response.status_code == 204


# ── Case Activities ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_activity(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Adding an activity to a case should work."""
    # Create case
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    create_response = await client.post("/api/cases", json=payload, headers=auth_headers)
    case_id = create_response.json()["id"]

    # Add activity
    activity_payload = {
        "activity_type": "note",
        "title": "Telefonisch contact met debiteur",
        "description": "Debiteur zegt volgende week te betalen",
    }
    response = await client.post(
        f"/api/cases/{case_id}/activities", json=activity_payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["activity_type"] == "note"
    assert data["title"] == "Telefonisch contact met debiteur"


@pytest.mark.asyncio
async def test_list_activities(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Listing activities should include creation activity and custom activities."""
    # Create case
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    create_response = await client.post("/api/cases", json=payload, headers=auth_headers)
    case_id = create_response.json()["id"]

    # Add a note
    await client.post(
        f"/api/cases/{case_id}/activities",
        json={"activity_type": "note", "title": "Test notitie"},
        headers=auth_headers,
    )

    # List activities
    response = await client.get(
        f"/api/cases/{case_id}/activities", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2  # Creation + note


# ── Delete Case ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_case(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Soft-deleting a case should remove it from active list."""
    # Create case
    payload = {
        "case_type": "incasso",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-17",
    }
    create_response = await client.post("/api/cases", json=payload, headers=auth_headers)
    case_id = create_response.json()["id"]

    # Delete
    response = await client.delete(f"/api/cases/{case_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's gone from active list
    response = await client.get("/api/cases", headers=auth_headers)
    assert response.json()["total"] == 0
