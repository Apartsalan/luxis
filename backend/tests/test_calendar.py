"""Tests for the calendar module — CRUD, filters, tenant isolation."""

import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.relations.models import Contact

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_contact(db: AsyncSession, tenant_id: uuid.UUID) -> Contact:
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Test Client B.V.",
        email="test@example.nl",
    )
    db.add(contact)
    await db.flush()
    return contact


async def _create_case(db: AsyncSession, tenant_id: uuid.UUID) -> Case:
    client = await _create_contact(db, tenant_id)
    from datetime import date

    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number="2026-00001",
        case_type="incasso",
        status="nieuw",
        debtor_type="b2b",
        date_opened=date.today(),
        client_id=client.id,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


def _event_payload(**overrides) -> dict:
    now = datetime.now(tz=None)
    payload = {
        "title": "Zitting rechtbank Amsterdam",
        "event_type": "hearing",
        "start_time": (now + timedelta(days=7)).isoformat(),
        "end_time": (now + timedelta(days=7, hours=1)).isoformat(),
        "all_day": False,
        "location": "Rechtbank Amsterdam",
        "reminder_minutes": 60,
    }
    payload.update(overrides)
    return payload


# ── CRUD ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_event(client: AsyncClient, auth_headers: dict):
    """Creating an event returns 201 with correct fields."""
    payload = _event_payload()
    resp = await client.post("/api/calendar/events", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Zitting rechtbank Amsterdam"
    assert data["event_type"] == "hearing"
    assert data["location"] == "Rechtbank Amsterdam"
    assert data["reminder_minutes"] == 60
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_events(client: AsyncClient, auth_headers: dict):
    """Listing events returns created events."""
    await client.post("/api/calendar/events", json=_event_payload(), headers=auth_headers)
    await client.post(
        "/api/calendar/events",
        json=_event_payload(title="Telefoongesprek cliënt", event_type="call"),
        headers=auth_headers,
    )

    resp = await client.get("/api/calendar/events", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_event(client: AsyncClient, auth_headers: dict):
    """Getting a single event returns the correct data."""
    create_resp = await client.post(
        "/api/calendar/events", json=_event_payload(), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = await client.get(f"/api/calendar/events/{event_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == event_id


@pytest.mark.asyncio
async def test_get_event_not_found(client: AsyncClient, auth_headers: dict):
    """Getting a nonexistent event returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/calendar/events/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_event(client: AsyncClient, auth_headers: dict):
    """Updating an event changes the specified fields."""
    create_resp = await client.post(
        "/api/calendar/events", json=_event_payload(), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/calendar/events/{event_id}",
        json={"title": "Gewijzigde zitting", "location": "Rechtbank Den Haag"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Gewijzigde zitting"
    assert data["location"] == "Rechtbank Den Haag"
    assert data["event_type"] == "hearing"  # unchanged


@pytest.mark.asyncio
async def test_delete_event(client: AsyncClient, auth_headers: dict):
    """Deleting an event returns 204 and the event is no longer listed."""
    create_resp = await client.post(
        "/api/calendar/events", json=_event_payload(), headers=auth_headers
    )
    event_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/calendar/events/{event_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/calendar/events/{event_id}", headers=auth_headers)
    assert get_resp.status_code == 404


# ── Filters ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_filter_by_event_type(client: AsyncClient, auth_headers: dict):
    """Filtering by event_type returns only matching events."""
    await client.post(
        "/api/calendar/events", json=_event_payload(event_type="hearing"), headers=auth_headers
    )
    await client.post(
        "/api/calendar/events",
        json=_event_payload(title="Bellen", event_type="call"),
        headers=auth_headers,
    )

    resp = await client.get("/api/calendar/events?event_type=hearing", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert all(e["event_type"] == "hearing" for e in data)


@pytest.mark.asyncio
async def test_filter_by_case_id(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Filtering by case_id returns only events linked to that case."""
    case = await _create_case(db, test_tenant.id)
    await client.post(
        "/api/calendar/events",
        json=_event_payload(case_id=str(case.id)),
        headers=auth_headers,
    )
    await client.post(
        "/api/calendar/events",
        json=_event_payload(title="Ander event"),
        headers=auth_headers,
    )

    resp = await client.get(f"/api/calendar/events?case_id={case.id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert all(e["case_id"] == str(case.id) for e in data)


# ── Tenant isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tenant_isolation(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
):
    """Events from tenant A are not visible to tenant B."""
    await client.post(
        "/api/calendar/events",
        json=_event_payload(title="Tenant A event"),
        headers=auth_headers,
    )

    resp = await client.get("/api/calendar/events", headers=second_auth_headers)
    assert resp.status_code == 200
    titles = [e["title"] for e in resp.json()]
    assert "Tenant A event" not in titles


# ── Auth ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(client: AsyncClient):
    """Requests without auth token return 401."""
    resp = await client.get("/api/calendar/events")
    assert resp.status_code in (401, 403)
