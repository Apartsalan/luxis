"""Tests for LF-20/LF-21 billing features — billing methods, voorschotnota,
budget tracking, and provisie calculation.

Financial precision: ALL assertions use Decimal with known-correct values.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.collections.models import Payment
from app.invoices.models import Expense, Invoice, InvoiceLine, InvoicePayment
from app.relations.models import Contact
from app.time_entries.models import TimeEntry

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_contact(
    db: AsyncSession, tenant_id: uuid.UUID, name: str = "Test B.V."
) -> Contact:
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name=name,
        email=f"{name.lower().replace(' ', '').replace('.', '')}@test.nl",
    )
    db.add(contact)
    await db.flush()
    return contact


async def _create_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    client_id: uuid.UUID,
    **overrides,
) -> Case:
    """Create a case with default values, overridable for billing method tests."""
    defaults = {
        "case_number": f"2026-{uuid.uuid4().hex[:5]}",
        "case_type": "incasso",
        "status": "nieuw",
        "date_opened": date.today(),
        "billing_method": "hourly",
        "assigned_to_id": user_id,
    }
    defaults.update(overrides)
    case = Case(
        tenant_id=tenant_id,
        client_id=client_id,
        **defaults,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


# ── Billing Method on Case CRUD ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_case_with_billing_method(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Creating a case with billing_method should persist all billing fields."""
    contact = await _create_contact(db, test_tenant.id)
    await db.commit()

    payload = {
        "case_type": "advies",
        "client_id": str(contact.id),
        "date_opened": str(date.today()),
        "billing_method": "fixed_price",
        "fixed_price_amount": 5000.00,
    }
    resp = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["billing_method"] == "fixed_price"
    assert Decimal(str(data["fixed_price_amount"])) == Decimal("5000.00")


@pytest.mark.asyncio
async def test_create_case_with_budget_cap(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Creating a case with budget_cap should persist budget_hours."""
    contact = await _create_contact(db, test_tenant.id)
    await db.commit()

    payload = {
        "case_type": "advies",
        "client_id": str(contact.id),
        "date_opened": str(date.today()),
        "billing_method": "budget_cap",
        "budget_hours": 40.0,
        "budget": 10000.0,
    }
    resp = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["billing_method"] == "budget_cap"
    assert Decimal(str(data["budget_hours"])) == Decimal("40.00")
    assert Decimal(str(data["budget"])) == Decimal("10000.00")


@pytest.mark.asyncio
async def test_create_case_with_provisie(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Creating an incasso case with provisie settings should persist all fields."""
    contact = await _create_contact(db, test_tenant.id)
    await db.commit()

    payload = {
        "case_type": "incasso",
        "client_id": str(contact.id),
        "date_opened": str(date.today()),
        "billing_method": "hourly",
        "provisie_percentage": 10.0,
        "fixed_case_costs": 250.0,
        "minimum_fee": 500.0,
    }
    resp = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["provisie_percentage"])) == Decimal("10.00")
    assert Decimal(str(data["fixed_case_costs"])) == Decimal("250.00")
    assert Decimal(str(data["minimum_fee"])) == Decimal("500.00")


@pytest.mark.asyncio
async def test_update_case_billing_method(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """Updating billing_method on an existing case should work."""
    contact = await _create_contact(db, test_tenant.id)
    await db.commit()

    # Create hourly case
    payload = {
        "case_type": "advies",
        "client_id": str(contact.id),
        "date_opened": str(date.today()),
    }
    resp = await client.post("/api/cases", json=payload, headers=auth_headers)
    case_id = resp.json()["id"]

    # Update to fixed_price
    resp = await client.put(
        f"/api/cases/{case_id}",
        json={"billing_method": "fixed_price", "fixed_price_amount": 3500.0},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["billing_method"] == "fixed_price"
    assert Decimal(str(resp.json()["fixed_price_amount"])) == Decimal("3500.00")


@pytest.mark.asyncio
async def test_case_default_billing_method_is_hourly(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    """A case created without billing_method should default to 'hourly'."""
    contact = await _create_contact(db, test_tenant.id)
    await db.commit()

    payload = {
        "case_type": "advies",
        "client_id": str(contact.id),
        "date_opened": str(date.today()),
    }
    resp = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["billing_method"] == "hourly"


# ── Voorschotnota ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_voorschotnota(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Creating a voorschotnota should return an invoice with type 'voorschotnota'."""
    contact = await _create_contact(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, contact.id)
    await db.commit()

    payload = {
        "case_id": str(case.id),
        "contact_id": str(contact.id),
        "amount": "2500.00",
        "description": "Voorschot dossierkosten",
        "invoice_date": str(date.today()),
        "due_date": str(date.today() + timedelta(days=14)),
        "btw_percentage": "21.00",
    }
    resp = await client.post(
        "/api/invoices/voorschotnota", json=payload, headers=auth_headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["invoice_type"] == "voorschotnota"
    assert data["invoice_number"].startswith("VN")
    assert Decimal(str(data["subtotal"])) == Decimal("2500.00")
    # BTW: 2500 * 21% = 525.00
    assert Decimal(str(data["btw_amount"])) == Decimal("525.00")
    assert Decimal(str(data["total"])) == Decimal("3025.00")
    assert len(data["lines"]) == 1
    assert data["lines"][0]["description"] == "Voorschot dossierkosten"


@pytest.mark.asyncio
async def test_voorschotnota_numbering(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Multiple voorschotnota's should get incrementing VN-numbers."""
    contact = await _create_contact(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, contact.id)
    await db.commit()

    numbers = []
    for i in range(3):
        payload = {
            "case_id": str(case.id),
            "contact_id": str(contact.id),
            "amount": "1000.00",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=14)),
            "btw_percentage": "21.00",
        }
        resp = await client.post(
            "/api/invoices/voorschotnota", json=payload, headers=auth_headers
        )
        assert resp.status_code == 201
        numbers.append(resp.json()["invoice_number"])

    assert numbers[0].endswith("00001")
    assert numbers[1].endswith("00002")
    assert numbers[2].endswith("00003")


# ── Advance Balance ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_advance_balance_empty(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Advance balance for a case with no voorschotnota's should be zero."""
    contact = await _create_contact(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, contact.id)
    await db.commit()

    resp = await client.get(
        f"/api/cases/{case.id}/advance-balance", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(str(data["total_advance"])) == Decimal("0.00")
    assert Decimal(str(data["total_offset"])) == Decimal("0.00")
    assert Decimal(str(data["available_balance"])) == Decimal("0.00")


# ── Budget Status ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_budget_status_green(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Budget status with low usage should be green."""
    contact = await _create_contact(db, test_tenant.id)
    case = await _create_case(
        db, test_tenant.id, test_user.id, contact.id,
        billing_method="budget_cap",
        budget_hours=Decimal("40.00"),
        budget=Decimal("10000.00"),
    )

    # Add a time entry: 2 hours at €200/hour
    te = TimeEntry(
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        case_id=case.id,
        date=date.today(),
        duration_minutes=120,
        description="Juridisch advies",
        activity_type="other",
        billable=True,
        hourly_rate=Decimal("200.00"),
    )
    db.add(te)
    await db.commit()

    resp = await client.get(
        f"/api/cases/{case.id}/budget-status", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(str(data["used_hours"])) == Decimal("2.00")
    # 120 min * 200 / 60 = 400.00
    assert Decimal(str(data["used_amount"])) == Decimal("400.00")
    assert data["status"] == "green"


@pytest.mark.asyncio
async def test_budget_status_red_over_90_pct(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Budget status at 95% should be red."""
    contact = await _create_contact(db, test_tenant.id)
    case = await _create_case(
        db, test_tenant.id, test_user.id, contact.id,
        billing_method="budget_cap",
        budget_hours=Decimal("10.00"),
    )

    # 9.5 hours = 570 minutes (95% of 10 hours)
    te = TimeEntry(
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        case_id=case.id,
        date=date.today(),
        duration_minutes=570,
        description="Uitgebreid onderzoek",
        activity_type="research",
        billable=True,
        hourly_rate=Decimal("200.00"),
    )
    db.add(te)
    await db.commit()

    resp = await client.get(
        f"/api/cases/{case.id}/budget-status", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(str(data["used_hours"])) == Decimal("9.50")
    assert data["status"] == "red"


@pytest.mark.asyncio
async def test_budget_status_orange(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Budget status between 75-90% should be orange."""
    contact = await _create_contact(db, test_tenant.id)
    case = await _create_case(
        db, test_tenant.id, test_user.id, contact.id,
        billing_method="budget_cap",
        budget_hours=Decimal("10.00"),
    )

    # 8 hours = 480 minutes (80% of 10 hours)
    te = TimeEntry(
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        case_id=case.id,
        date=date.today(),
        duration_minutes=480,
        description="Werkzaamheden",
        activity_type="other",
        billable=True,
        hourly_rate=Decimal("200.00"),
    )
    db.add(te)
    await db.commit()

    resp = await client.get(
        f"/api/cases/{case.id}/budget-status", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "orange"


@pytest.mark.asyncio
async def test_budget_status_includes_expenses(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Budget status should include billable expenses in used_amount."""
    contact = await _create_contact(db, test_tenant.id)
    case = await _create_case(
        db, test_tenant.id, test_user.id, contact.id,
        billing_method="budget_cap",
        budget=Decimal("1000.00"),
    )

    # Add an expense
    expense = Expense(
        tenant_id=test_tenant.id,
        case_id=case.id,
        description="Griffierecht",
        amount=Decimal("85.00"),
        expense_date=date.today(),
        category="griffierecht",
        billable=True,
    )
    db.add(expense)
    await db.commit()

    resp = await client.get(
        f"/api/cases/{case.id}/budget-status", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(str(data["used_amount"])) == Decimal("85.00")


# ── Provisie Calculation ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_provisie_basic_calculation(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Provisie = collected * percentage/100, with fixed costs and minimum fee."""
    contact = await _create_contact(db, test_tenant.id)
    case = await _create_case(
        db, test_tenant.id, test_user.id, contact.id,
        provisie_percentage=Decimal("10.00"),
        fixed_case_costs=Decimal("250.00"),
        minimum_fee=Decimal("500.00"),
    )

    # Add incasso payments totalling €8000
    for amount in [Decimal("3000.00"), Decimal("5000.00")]:
        payment = Payment(
            tenant_id=test_tenant.id,
            case_id=case.id,
            amount=amount,
            payment_date=date.today(),
        )
        db.add(payment)
    await db.commit()

    resp = await client.get(
        f"/api/cases/{case.id}/provisie", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()

    # collected = 8000, provisie = 8000 * 10% = 800
    assert Decimal(str(data["collected_amount"])) == Decimal("8000.00")
    assert Decimal(str(data["provisie_percentage"])) == Decimal("10.00")
    assert Decimal(str(data["provisie_amount"])) == Decimal("800.00")
    assert Decimal(str(data["fixed_case_costs"])) == Decimal("250.00")
    # total_fee = max(800 + 250, 500) = max(1050, 500) = 1050
    assert Decimal(str(data["total_fee"])) == Decimal("1050.00")


@pytest.mark.asyncio
async def test_provisie_minimum_fee_applies(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """When provisie + fixed_costs < minimum_fee, minimum_fee should apply."""
    contact = await _create_contact(db, test_tenant.id)
    case = await _create_case(
        db, test_tenant.id, test_user.id, contact.id,
        provisie_percentage=Decimal("5.00"),
        fixed_case_costs=Decimal("50.00"),
        minimum_fee=Decimal("500.00"),
    )

    # Small payment: €1000
    payment = Payment(
        tenant_id=test_tenant.id,
        case_id=case.id,
        amount=Decimal("1000.00"),
        payment_date=date.today(),
    )
    db.add(payment)
    await db.commit()

    resp = await client.get(
        f"/api/cases/{case.id}/provisie", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()

    # provisie = 1000 * 5% = 50, plus fixed 50 = 100 → min_fee 500 is higher
    assert Decimal(str(data["provisie_amount"])) == Decimal("50.00")
    assert Decimal(str(data["total_fee"])) == Decimal("500.00")


@pytest.mark.asyncio
async def test_provisie_no_payments(
    client: AsyncClient, auth_headers: dict, db: AsyncSession,
    test_tenant: Tenant, test_user: User,
):
    """Provisie with no payments should return zero collected amount."""
    contact = await _create_contact(db, test_tenant.id)
    case = await _create_case(
        db, test_tenant.id, test_user.id, contact.id,
        provisie_percentage=Decimal("10.00"),
        fixed_case_costs=Decimal("0.00"),
        minimum_fee=Decimal("0.00"),
    )
    await db.commit()

    resp = await client.get(
        f"/api/cases/{case.id}/provisie", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(str(data["collected_amount"])) == Decimal("0.00")
    assert Decimal(str(data["provisie_amount"])) == Decimal("0.00")
    assert Decimal(str(data["total_fee"])) == Decimal("0.00")
