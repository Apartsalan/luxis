"""Tests for the dashboard module — KPIs and recent activity."""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.relations.models import Contact


@pytest.mark.asyncio
async def test_dashboard_summary_empty(client: AsyncClient, auth_headers: dict):
    """Empty tenant should return zero KPIs."""
    response = await client.get("/api/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_active_cases"] == 0
    # Pydantic serializes Decimal as string in JSON
    assert Decimal(str(data["total_outstanding"])) == Decimal("0")
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

    response = await client.get("/api/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_active_cases"] == 3
    assert data["cases_this_month"] >= 3

    # Check breakdown by type
    type_counts = {t["case_type"]: t["count"] for t in data["cases_by_type"]}
    assert type_counts.get("incasso") == 2
    assert type_counts.get("advies") == 1

    # Check breakdown by status (all should be "nieuw")
    status_counts = {s["status"]: s["count"] for s in data["cases_by_status"]}
    assert status_counts.get("nieuw") == 3


@pytest.mark.asyncio
async def test_dashboard_summary_contacts_counted(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    test_person: Contact,
):
    """Dashboard should count contacts."""
    response = await client.get("/api/dashboard/summary", headers=auth_headers)
    data = response.json()
    assert data["total_contacts"] >= 2


@pytest.mark.asyncio
async def test_recent_activity_empty(client: AsyncClient, auth_headers: dict):
    """Empty tenant should have no recent activity."""
    response = await client.get("/api/dashboard/recent-activity", headers=auth_headers)
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

    response = await client.get("/api/dashboard/recent-activity", headers=auth_headers)
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


# ── Reports KPIs ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reports_kpis_with_closed_case(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_company: Contact,
):
    """KPIs endpoint must not crash when a closed case exists (AUDIT-B2).

    func.avg(date_closed - date_opened) returns a NUMERIC -> Decimal, which has
    no `.days` attribute. avg_days_to_collect must be computed as an int.
    """
    from datetime import date, timedelta

    from app.cases.models import Case

    opened = date.today() - timedelta(days=10)
    case_response = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "client_id": str(test_company.id),
            "date_opened": opened.isoformat(),
        },
        headers=auth_headers,
    )
    assert case_response.status_code == 201
    case_id = case_response.json()["id"]

    # Close the case (date_closed is not exposed on CaseUpdate -> set directly)
    case = (
        await db.execute(select(Case).where(Case.id == case_id))
    ).scalar_one()
    case.date_closed = date.today()
    await db.commit()

    response = await client.get("/api/reports/kpis", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["avg_days_to_collect"] == 10


@pytest.mark.asyncio
async def test_reports_kpis_overdue_derived_from_due_date(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant,
    test_company: Contact,
):
    """overdue_tasks must be derived from due_date, not the stale status column.

    A task past its due date but still marked 'pending' (because the daily batch
    that materializes status='overdue' has not run) must still count as overdue
    (AUDIT-H23).
    """
    import uuid
    from datetime import date, timedelta

    from app.cases.models import Case
    from app.workflow.models import WorkflowTask

    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-08020",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        is_active=True,
        client_id=test_company.id,
        date_opened=date.today(),
        total_principal=Decimal("0.00"),
        total_paid=Decimal("0.00"),
    )
    db.add(case)

    def _task(days: int, status: str) -> WorkflowTask:
        return WorkflowTask(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_id=case.id,
            task_type="manual_review",
            title="Taak",
            due_date=date.today() + timedelta(days=days),
            status=status,
        )

    db.add_all(
        [
            _task(-3, "pending"),   # overdue, stale status -> must count
            _task(-5, "pending"),   # overdue -> must count
            _task(-2, "completed"),  # past due but done -> must NOT count
            _task(+3, "pending"),    # future -> upcoming, not overdue
        ]
    )
    await db.commit()

    resp = await client.get("/api/reports/kpis", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["overdue_tasks"] == 2
    assert data["upcoming_deadlines"] >= 1


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


@pytest.mark.asyncio
async def test_monthly_stats_excludes_inactive_cases(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant,
    test_company: Contact,
):
    """Monthly 'new_cases' must count only active cases — the soft-deleted seed
    cases inflated the chart ('215 nieuwe zaken' vs 2 actief) (AUDIT-MEDIUM)."""
    import uuid
    from datetime import date

    from app.cases.models import Case

    today = date.today()

    def _case(num: str, active: bool) -> Case:
        return Case(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_number=num,
            case_type="incasso",
            debtor_type="b2b",
            status="nieuw",
            is_active=active,
            client_id=test_company.id,
            date_opened=today,
            total_principal=Decimal("0.00"),
            total_paid=Decimal("0.00"),
        )

    db.add_all([
        _case("2026-ACT01", True),
        _case("2026-INA01", False),
        _case("2026-INA02", False),
    ])
    await db.commit()

    resp = await client.get("/api/reports/monthly?months=1", headers=auth_headers)
    assert resp.status_code == 200
    rows = resp.json()
    # Only the active case is counted; the two inactive (seed-style) ones are not.
    assert sum(r["new_cases"] for r in rows) == 1
