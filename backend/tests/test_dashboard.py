"""Tests for the dashboard module — KPIs and recent activity."""

import pytest
from httpx import AsyncClient

from app.relations.models import Contact


@pytest.mark.asyncio
async def test_dashboard_summary_empty(
    client: AsyncClient, auth_headers: dict
):
    """Empty tenant should return zero KPIs."""
    response = await client.get(
        "/api/dashboard/summary", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_active_cases"] == 0
    assert data["total_outstanding"] == 0
    assert data["cases_by_status"] == []
    assert data["cases_by_type"] == []


@pytest.mark.asyncio
async def test_dashboard_summary_with_cases(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Dashboard should reflect created cases."""
    from datetime import date

    # Create a few cases
    for case_type in ["incasso", "incasso", "advies"]:
        await client.post(
            "/api/cases",
            json={
                "case_type": case_type,
                "client_id": str(test_company.id),
                "date_opened": date.today().isoformat(),
            },
            headers=auth_headers,
        )

    response = await client.get(
        "/api/dashboard/summary", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_active_cases"] == 3
    assert data["cases_this_month"] >= 3

    # Check breakdown by type
    type_counts = {
        t["case_type"]: t["count"] for t in data["cases_by_type"]
    }
    assert type_counts.get("incasso") == 2
    assert type_counts.get("advies") == 1

    # Check breakdown by status (all should be "nieuw")
    status_counts = {
        s["status"]: s["count"] for s in data["cases_by_status"]
    }
    assert status_counts.get("nieuw") == 3


@pytest.mark.asyncio
async def test_dashboard_summary_contacts_counted(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    test_person: Contact,
):
    """Dashboard should count contacts."""
    response = await client.get(
        "/api/dashboard/summary", headers=auth_headers
    )
    data = response.json()
    assert data["total_contacts"] >= 2


@pytest.mark.asyncio
async def test_recent_activity_empty(
    client: AsyncClient, auth_headers: dict
):
    """Empty tenant should have no recent activity."""
    response = await client.get(
        "/api/dashboard/recent-activity", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_recent_activity_with_cases(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Creating cases should generate activity entries."""
    # Create a case
    case_response = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": str(test_company.id),
            "date_opened": "2026-02-17",
        },
        headers=auth_headers,
    )
    case_id = case_response.json()["id"]

    # Add a note activity
    await client.post(
        f"/api/cases/{case_id}/activities",
        json={
            "activity_type": "note",
            "title": "Test notitie",
            "description": "Dashboard test",
        },
        headers=auth_headers,
    )

    response = await client.get(
        "/api/dashboard/recent-activity", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2  # At least creation + note
    assert data["items"][0]["case_number"].startswith("2026-")


@pytest.mark.asyncio
async def test_recent_activity_limit(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
):
    """Limit parameter should restrict number of returned items."""
    # Create a case (generates 1 activity)
    await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": str(test_company.id),
            "date_opened": "2026-02-17",
        },
        headers=auth_headers,
    )

    response = await client.get(
        "/api/dashboard/recent-activity?limit=1",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 1


# ── Auth Checks ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dashboard_summary_unauthenticated(client: AsyncClient):
    """Dashboard summary without auth should return 401."""
    response = await client.get("/api/dashboard/summary")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_recent_activity_unauthenticated(client: AsyncClient):
    """Recent activity without auth should return 401."""
    response = await client.get("/api/dashboard/recent-activity")
    assert response.status_code == 401


# ── Tenant Isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tenant_isolation_dashboard_summary(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
    test_company: Contact,
):
    """Tenant B's dashboard should NOT count Tenant A's cases."""
    from datetime import date

    # Create cases in Tenant A
    for _ in range(3):
        await client.post(
            "/api/cases",
            json={
                "case_type": "incasso",
                "client_id": str(test_company.id),
                "date_opened": date.today().isoformat(),
            },
            headers=auth_headers,
        )

    # Tenant A sees 3 cases
    resp_a = await client.get("/api/dashboard/summary", headers=auth_headers)
    assert resp_a.json()["total_active_cases"] == 3

    # Tenant B sees 0 cases
    resp_b = await client.get("/api/dashboard/summary", headers=second_auth_headers)
    assert resp_b.json()["total_active_cases"] == 0


@pytest.mark.asyncio
async def test_tenant_isolation_recent_activity(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
    test_company: Contact,
):
    """Tenant B's recent activity should NOT show Tenant A's activities."""
    # Create a case in Tenant A (generates activity)
    await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": str(test_company.id),
            "date_opened": "2026-02-17",
        },
        headers=auth_headers,
    )

    # Tenant A sees activity
    resp_a = await client.get("/api/dashboard/recent-activity", headers=auth_headers)
    assert resp_a.json()["total"] >= 1

    # Tenant B sees nothing
    resp_b = await client.get("/api/dashboard/recent-activity", headers=second_auth_headers)
    assert resp_b.json()["total"] == 0
