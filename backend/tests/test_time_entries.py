"""Tests for the time entries module — CRUD, filters, unbilled, summary, my/today."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token, hash_password
from app.cases.models import Case
from app.relations.models import Contact

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_contact(
    db: AsyncSession, tenant_id: uuid.UUID, name: str = "Test Client B.V."
) -> Contact:
    """Create a minimal contact for case creation."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name=name,
        email=f"{name.lower().replace(' ', '').replace('.', '')}@example.nl",
    )
    db.add(contact)
    await db.flush()
    return contact


async def _create_case(
    db: AsyncSession, tenant_id: uuid.UUID, case_number: str = "2026-00001"
) -> Case:
    """Create a minimal case for time entry tests."""
    client = await _create_contact(db, tenant_id)
    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number=case_number,
        case_type="incasso",
        status="nieuw",
        debtor_type="b2b",
        date_opened=date(2026, 1, 15),
        client_id=client.id,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


def _entry_payload(case_id: uuid.UUID, **overrides) -> dict:
    """Build a time entry creation payload."""
    payload = {
        "case_id": str(case_id),
        "date": "2026-03-01",
        "duration_minutes": 30,
        "description": "Telefonisch overleg debiteur",
        "activity_type": "phone",
        "billable": True,
        "hourly_rate": "250.00",
    }
    payload.update(overrides)
    return payload


# ── CRUD ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_time_entry(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Creating a time entry should return 201 with correct fields."""
    case = await _create_case(db, test_tenant.id)
    payload = _entry_payload(case.id)

    response = await client.post("/api/time-entries", json=payload, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["duration_minutes"] == 30
    assert data["activity_type"] == "phone"
    assert data["billable"] is True
    assert data["invoiced"] is False
    assert data["description"] == "Telefonisch overleg debiteur"
    assert Decimal(data["hourly_rate"]) == Decimal("250.00")
    assert data["case"]["case_number"] == "2026-00001"
    assert data["user"]["full_name"] == "Lisanne Kesting"


@pytest.mark.asyncio
async def test_list_time_entries(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Listing time entries should return all entries for the tenant."""
    case = await _create_case(db, test_tenant.id)

    # Create 3 entries
    for i in range(3):
        payload = _entry_payload(case.id, duration_minutes=15 * (i + 1))
        await client.post("/api/time-entries", json=payload, headers=auth_headers)

    response = await client.get("/api/time-entries", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_update_time_entry(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Updating a time entry should change the specified fields."""
    case = await _create_case(db, test_tenant.id)
    payload = _entry_payload(case.id)

    create_resp = await client.post("/api/time-entries", json=payload, headers=auth_headers)
    entry_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/time-entries/{entry_id}",
        json={"duration_minutes": 60, "activity_type": "meeting", "billable": False},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["duration_minutes"] == 60
    assert data["activity_type"] == "meeting"
    assert data["billable"] is False


@pytest.mark.asyncio
async def test_delete_time_entry(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Deleting a time entry should return 204 and remove the entry."""
    case = await _create_case(db, test_tenant.id)
    payload = _entry_payload(case.id)

    create_resp = await client.post("/api/time-entries", json=payload, headers=auth_headers)
    entry_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/time-entries/{entry_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # Verify it's gone
    list_resp = await client.get("/api/time-entries", headers=auth_headers)
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_entry(client: AsyncClient, auth_headers: dict):
    """Deleting a nonexistent entry should return 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.delete(f"/api/time-entries/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


# ── Filters ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_filter_by_case(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Filtering by case_id should return only entries for that case."""
    case_a = await _create_case(db, test_tenant.id, "2026-00001")
    case_b = await _create_case(db, test_tenant.id, "2026-00002")

    await client.post("/api/time-entries", json=_entry_payload(case_a.id), headers=auth_headers)
    await client.post("/api/time-entries", json=_entry_payload(case_a.id), headers=auth_headers)
    await client.post("/api/time-entries", json=_entry_payload(case_b.id), headers=auth_headers)

    resp = await client.get(f"/api/time-entries?case_id={case_a.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_filter_by_billable(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Filtering by billable flag should return matching entries only."""
    case = await _create_case(db, test_tenant.id)

    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, billable=True),
        headers=auth_headers,
    )
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, billable=False),
        headers=auth_headers,
    )

    resp = await client.get("/api/time-entries?billable=true", headers=auth_headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["billable"] is True


@pytest.mark.asyncio
async def test_filter_by_date_range(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Filtering by date range should return entries within that range."""
    case = await _create_case(db, test_tenant.id)

    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, date="2026-01-15"),
        headers=auth_headers,
    )
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, date="2026-02-15"),
        headers=auth_headers,
    )
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, date="2026-03-15"),
        headers=auth_headers,
    )

    resp = await client.get(
        "/api/time-entries?date_from=2026-02-01&date_to=2026-02-28",
        headers=auth_headers,
    )
    assert len(resp.json()) == 1
    assert resp.json()[0]["date"] == "2026-02-15"


# ── Unbilled ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unbilled_entries(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Unbilled endpoint should return only billable, uninvoiced entries."""
    case = await _create_case(db, test_tenant.id)

    # Billable + not invoiced (should appear)
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, billable=True),
        headers=auth_headers,
    )
    # Not billable (should NOT appear)
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, billable=False),
        headers=auth_headers,
    )

    resp = await client.get("/api/time-entries/unbilled", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["billable"] is True
    assert data[0]["invoiced"] is False


# ── Summary ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_summary_totals(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Summary should correctly calculate total minutes and amounts."""
    case = await _create_case(db, test_tenant.id)

    # Entry 1: 60 min, billable, €250/hr → €250.00
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, duration_minutes=60, billable=True, hourly_rate="250.00"),
        headers=auth_headers,
    )
    # Entry 2: 30 min, billable, €200/hr → €100.00
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, duration_minutes=30, billable=True, hourly_rate="200.00"),
        headers=auth_headers,
    )
    # Entry 3: 45 min, non-billable → €0
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, duration_minutes=45, billable=False, hourly_rate=None),
        headers=auth_headers,
    )

    resp = await client.get("/api/time-entries/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_minutes"] == 135  # 60 + 30 + 45
    assert data["billable_minutes"] == 90  # 60 + 30
    assert data["non_billable_minutes"] == 45
    assert Decimal(data["total_amount"]) == Decimal("350.00")  # 250 + 100


@pytest.mark.asyncio
async def test_summary_per_case_breakdown(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Summary should include per-case breakdown."""
    case_a = await _create_case(db, test_tenant.id, "2026-00001")
    case_b = await _create_case(db, test_tenant.id, "2026-00002")

    await client.post(
        "/api/time-entries",
        json=_entry_payload(case_a.id, duration_minutes=60),
        headers=auth_headers,
    )
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case_b.id, duration_minutes=30),
        headers=auth_headers,
    )

    resp = await client.get("/api/time-entries/summary", headers=auth_headers)
    data = resp.json()

    assert len(data["per_case"]) == 2
    # Sorted by total_minutes desc — case_a (60) first
    assert data["per_case"][0]["case_number"] == "2026-00001"
    assert data["per_case"][0]["total_minutes"] == 60
    assert data["per_case"][1]["case_number"] == "2026-00002"
    assert data["per_case"][1]["total_minutes"] == 30


# ── My/Today ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_my_today(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """My/today should return only today's entries for the current user."""
    case = await _create_case(db, test_tenant.id)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    # Today's entry
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, date=today),
        headers=auth_headers,
    )
    # Yesterday's entry (should NOT appear)
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id, date=yesterday),
        headers=auth_headers,
    )

    resp = await client.get("/api/time-entries/my/today", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["date"] == today


# ── Validation ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invalid_activity_type(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Invalid activity_type should be rejected (422)."""
    case = await _create_case(db, test_tenant.id)
    payload = _entry_payload(case.id, activity_type="invalid_type")

    resp = await client.post("/api/time-entries", json=payload, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_zero_duration_rejected(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Zero or negative duration should be rejected (422)."""
    case = await _create_case(db, test_tenant.id)
    payload = _entry_payload(case.id, duration_minutes=0)

    resp = await client.post("/api/time-entries", json=payload, headers=auth_headers)
    assert resp.status_code == 422


# ── Tenant Isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tenant_isolation(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Entries from another tenant should not be visible."""
    case = await _create_case(db, test_tenant.id)

    # Create entry as the test user
    await client.post(
        "/api/time-entries",
        json=_entry_payload(case.id),
        headers=auth_headers,
    )

    # Create a second tenant + user
    other_tenant = Tenant(
        id=uuid.uuid4(), name="Other Firm", slug="other-firm", kvk_number="99999999"
    )
    db.add(other_tenant)
    await db.flush()

    other_user = User(
        id=uuid.uuid4(),
        tenant_id=other_tenant.id,
        email="other@otherfirm.nl",
        hashed_password=hash_password("password123"),
        full_name="Other User",
        role="admin",
    )
    db.add(other_user)
    await db.commit()

    other_token = create_access_token(str(other_user.id), str(other_tenant.id))
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Other tenant should see 0 entries
    resp = await client.get("/api/time-entries", headers=other_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 0
