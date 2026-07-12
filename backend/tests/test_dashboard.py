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


@pytest.mark.asyncio
async def test_reports_kpis_debtor_type_uses_case_debtor_type(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant,
    test_company: Contact,
):
    """'Verdeling type debiteur' must classify on Case.debtor_type, not on the
    creditor/client contact that Case.client_id points to (AUDIT-MEDIUM).

    Both cases below have the same *company* creditor (client_id), but their
    debtors differ: one b2c (consumer), one b2b (business). Grouping on the
    creditor would wrongly report both as 'Bedrijf'.
    """
    import uuid
    from datetime import date

    from app.cases.models import Case

    def _case(num: str, debtor_type: str) -> Case:
        return Case(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_number=num,
            case_type="incasso",
            debtor_type=debtor_type,
            status="nieuw",
            is_active=True,
            client_id=test_company.id,  # creditor is a company in both
            date_opened=date.today(),
            total_principal=Decimal("0.00"),
            total_paid=Decimal("0.00"),
        )

    db.add_all([_case("2026-DBT01", "b2c"), _case("2026-DBT02", "b2b")])
    await db.commit()

    resp = await client.get("/api/reports/kpis", headers=auth_headers)
    assert resp.status_code == 200
    breakdown = resp.json()["cases_by_debtor_type"]
    assert breakdown.get("Particulier") == 1  # the b2c debtor
    assert breakdown.get("Bedrijf") == 1  # the b2b debtor


@pytest.mark.asyncio
async def test_reports_collected_sums_payments_in_selected_period(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant,
    test_company: Contact,
):
    import uuid
    from datetime import date

    from dateutil.relativedelta import relativedelta

    from app.cases.models import Case
    from app.collections.models import Payment

    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-COLLECTED",
        case_type="incasso",
        debtor_type="b2b",
        status="betaald",
        is_active=True,
        client_id=test_company.id,
        date_opened=date.today() - relativedelta(months=18),
    )
    db.add(case)
    await db.flush()
    db.add_all(
        [
            Payment(
                tenant_id=test_tenant.id,
                case_id=case.id,
                amount=Decimal("125.50"),
                payment_date=date.today(),
            ),
            Payment(
                tenant_id=test_tenant.id,
                case_id=case.id,
                amount=Decimal("999.00"),
                payment_date=date.today() - relativedelta(months=7),
            ),
        ]
    )
    await db.commit()

    response = await client.get("/api/reports/kpis?months=6", headers=auth_headers)

    assert response.status_code == 200
    assert Decimal(response.json()["total_collected"]) == Decimal("125.50")


@pytest.mark.asyncio
async def test_phase_distribution_includes_cases_without_step(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant,
    test_company: Contact,
):
    import uuid
    from datetime import date

    from app.cases.models import Case
    from app.incasso.models import IncassoPipelineStep

    step = IncassoPipelineStep(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Minnelijke behandeling",
        sort_order=10,
        min_wait_days=0,
        max_wait_days=0,
        step_category="minnelijk",
        debtor_type="both",
    )
    db.add(step)
    await db.flush()

    def make_case(number: str, step_id=None) -> Case:
        return Case(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_number=number,
            case_type="incasso",
            debtor_type="b2b",
            status="in_behandeling",
            is_active=True,
            client_id=test_company.id,
            incasso_step_id=step_id,
            date_opened=date.today(),
            total_principal=Decimal("100.00"),
            total_paid=Decimal("0.00"),
        )

    db.add_all([make_case("2026-PHASE1", step.id), make_case("2026-PHASE2")])
    await db.commit()

    response = await client.get("/api/reports/phase-distribution", headers=auth_headers)

    assert response.status_code == 200
    counts = {row["phase"]: row["count"] for row in response.json()}
    assert counts == {"Minnelijke behandeling": 1, "Geen stap": 1}


async def _seed_active_incasso_with_interest_bik(db, tenant_id, client_id):
    """Active incasso case + claim + statutory rate, so its financial summary has
    interest + BIK on top of the €1000 principal."""
    import uuid
    from datetime import date, timedelta

    from app.cases.models import Case
    from app.collections.models import Claim, InterestRate

    db.add(
        InterestRate(
            id=uuid.uuid4(),
            rate_type="statutory",
            rate=Decimal("8.00"),
            effective_from=date(2023, 1, 1),
        )
    )
    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number="2026-H4001",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        is_active=True,
        client_id=client_id,
        interest_type="statutory",
        date_opened=date.today() - timedelta(days=400),
        total_principal=Decimal("1000.00"),
        total_paid=Decimal("0.00"),
    )
    db.add(case)
    await db.flush()
    db.add(
        Claim(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            case_id=case.id,
            description="Factuur H4",
            principal_amount=Decimal("1000.00"),
            default_date=date.today() - timedelta(days=400),
        )
    )
    await db.commit()
    return case


@pytest.mark.asyncio
async def test_dashboard_outstanding_includes_interest_and_bik(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant, test_company: Contact
):
    """Dashboard 'openstaand' must include interest + BIK — matching the case
    detail's financial summary — not just principal − paid (AUDIT-H4)."""
    case = await _seed_active_incasso_with_interest_bik(db, test_tenant.id, test_company.id)

    fin = await client.get(f"/api/cases/{case.id}/financial-summary", headers=auth_headers)
    assert fin.status_code == 200
    expected = Decimal(str(fin.json()["total_outstanding"]))
    assert expected > Decimal("1000.00")  # interest + BIK sit on top of the principal

    resp = await client.get("/api/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    assert Decimal(str(resp.json()["total_outstanding"])) == expected


@pytest.mark.asyncio
async def test_reports_outstanding_includes_interest_and_bik(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant, test_company: Contact
):
    """Reports-KPI 'openstaand' must include interest + BIK too (AUDIT-H4)."""
    case = await _seed_active_incasso_with_interest_bik(db, test_tenant.id, test_company.id)

    fin = await client.get(f"/api/cases/{case.id}/financial-summary", headers=auth_headers)
    expected = Decimal(str(fin.json()["total_outstanding"]))

    resp = await client.get("/api/reports/kpis", headers=auth_headers)
    assert resp.status_code == 200
    assert Decimal(str(resp.json()["total_outstanding"])) == expected


@pytest.mark.asyncio
async def test_closed_archive_case_not_counted_as_open_work(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant, test_company: Contact
):
    """S175b: een AFGESLOTEN dossier (zichtbaar archief, is_active=True — zoals de hele
    BaseNet-import) telt NIET mee als werkvoorraad of openstaand geld. Vóór deze fix
    blies het 607-zaken-archief het dashboard op tot '610 actieve zaken / €4M openstaand'."""
    import uuid as _uuid
    from datetime import date, timedelta

    from app.cases.models import Case
    from app.collections.models import Claim

    # Eén echt open zaak…
    open_case = await _seed_active_incasso_with_interest_bik(
        db, test_tenant.id, test_company.id
    )
    # …en één afgesloten archiefzaak mét vordering en zonder betalingen (à la import).
    archived = Case(
        id=_uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="IN999901",
        case_type="incasso",
        debtor_type="b2b",
        status="afgesloten",
        is_active=True,  # zichtbaar als historie — precies zoals de BaseNet-import
        client_id=test_company.id,
        interest_type="statutory",
        date_opened=date.today() - timedelta(days=900),
        date_closed=date.today() - timedelta(days=200),
        total_principal=Decimal("50000.00"),
        total_paid=Decimal("0.00"),
    )
    db.add(archived)
    paid = Case(
        id=_uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="IN999902",
        case_type="incasso",
        debtor_type="b2b",
        status="betaald",
        is_active=True,
        client_id=test_company.id,
        date_opened=date.today() - timedelta(days=100),
        date_closed=date.today(),
        total_principal=Decimal("9000.00"),
        total_paid=Decimal("9000.00"),
    )
    db.add(paid)
    db.add(
        Claim(
            id=_uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_id=archived.id,
            description="archiefvordering",
            principal_amount=Decimal("50000.00"),
            invoice_date=date.today() - timedelta(days=900),
            default_date=date.today() - timedelta(days=870),
        )
    )
    await db.commit()

    fin = await client.get(f"/api/cases/{open_case.id}/financial-summary", headers=auth_headers)
    expected = Decimal(str(fin.json()["total_outstanding"]))

    # Dashboard: alleen de open zaak telt — in aantal én in geld.
    resp = await client.get("/api/dashboard/summary", headers=auth_headers)
    data = resp.json()
    assert data["total_active_cases"] == 1
    assert Decimal(str(data["total_outstanding"])) == expected
    statuses = {s["status"] for s in data["cases_by_status"]}
    assert "afgesloten" not in statuses
    assert "betaald" not in statuses

    # Rapporten-KPI's: zelfde regel.
    resp = await client.get("/api/reports/kpis", headers=auth_headers)
    kpis = resp.json()
    assert kpis["active_cases"] == 1
    assert Decimal(str(kpis["total_outstanding"])) == expected


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


@pytest.mark.asyncio
async def test_contacts_this_month_excludes_import(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant,
):
    """S203 #6: geïmporteerde relaties (marker in notes) tellen niet als
    'nieuw deze maand', ook al is created_at de importdag."""
    import uuid

    db.add(Contact(
        id=uuid.uuid4(), tenant_id=test_tenant.id, contact_type="company",
        name="Echt nieuwe relatie", email="nieuw@example.nl",
    ))
    db.add(Contact(
        id=uuid.uuid4(), tenant_id=test_tenant.id, contact_type="company",
        name="Geimporteerde relatie", email="import@example.nl",
        notes="[BaseNet-import] rcode=12345",
    ))
    await db.commit()

    response = await client.get("/api/dashboard/summary", headers=auth_headers)
    data = response.json()
    # Alleen de echte nieuwe relatie telt; de import-relatie niet.
    assert data["contacts_this_month"] == 1
    # Totaal telt beide nog wel.
    assert data["total_contacts"] >= 2
