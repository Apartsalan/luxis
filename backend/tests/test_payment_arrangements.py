"""Tests for payment arrangement installments — LF-15."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.collections.models import InterestRate
from app.relations.models import Contact


async def _seed_interest_rates(db: AsyncSession) -> None:
    """Seed minimal interest rates needed for payment tests."""
    db.add(InterestRate(
        id=uuid.uuid4(),
        rate_type="statutory",
        effective_from=date(2024, 1, 1),
        rate=Decimal("7.00"),
        source="Test fixture",
    ))
    db.add(InterestRate(
        id=uuid.uuid4(),
        rate_type="statutory",
        effective_from=date(2025, 1, 1),
        rate=Decimal("6.00"),
        source="Test fixture",
    ))
    await db.commit()


# ── Helper: create case + claim ──────────────────────────────────────────────


async def _create_case_with_claim(
    client: AsyncClient,
    headers: dict,
    client_id: str,
    principal: str = "3600.00",
) -> tuple[str, str]:
    """Create an incasso case with one claim. Returns (case_id, claim_id)."""
    case_resp = await client.post(
        "/api/cases",
        json={
            "case_type": "incasso",
            "description": "Test incassodossier",
            "interest_type": "statutory",
            "client_id": client_id,
            "date_opened": date.today().isoformat(),
        },
        headers=headers,
    )
    assert case_resp.status_code == 201
    case_id = case_resp.json()["id"]

    claim_resp = await client.post(
        f"/api/cases/{case_id}/claims",
        json={
            "description": "Factuur 2026-001",
            "principal_amount": principal,
            "default_date": (date.today() - timedelta(days=30)).isoformat(),
        },
        headers=headers,
    )
    assert claim_resp.status_code == 201
    return case_id, claim_resp.json()["id"]


# ── Test: create arrangement generates installments ──────────────────────────


@pytest.mark.asyncio
async def test_create_arrangement_generates_monthly_installments(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Creating an arrangement should auto-generate installments."""
    case_id, _ = await _create_case_with_claim(
        client, auth_headers, str(test_company.id)
    )

    start = date.today() + timedelta(days=7)
    resp = await client.post(
        f"/api/cases/{case_id}/arrangements",
        json={
            "total_amount": "3600.00",
            "installment_amount": "600.00",
            "frequency": "monthly",
            "start_date": start.isoformat(),
            "notes": "Afspraak met debiteur",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    arr = resp.json()
    assert arr["status"] == "active"
    assert Decimal(arr["total_amount"]) == Decimal("3600.00")

    # Fetch with installments
    list_resp = await client.get(
        f"/api/cases/{case_id}/arrangements", headers=auth_headers
    )
    assert list_resp.status_code == 200
    arrangements = list_resp.json()
    assert len(arrangements) >= 1

    arr_detail = arrangements[0]
    installments = arr_detail["installments"]
    assert len(installments) == 6  # 3600 / 600 = 6

    # All should be pending
    for inst in installments:
        assert inst["status"] == "pending"
        assert Decimal(inst["amount"]) == Decimal("600.00")
        assert Decimal(inst["paid_amount"]) == Decimal("0")

    # Installment numbers should be 1..6
    numbers = [i["installment_number"] for i in installments]
    assert numbers == [1, 2, 3, 4, 5, 6]


@pytest.mark.asyncio
async def test_rounding_difference_on_last_installment(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Last installment should absorb rounding difference."""
    case_id, _ = await _create_case_with_claim(
        client, auth_headers, str(test_company.id), principal="1000.00"
    )

    start = date.today() + timedelta(days=7)
    resp = await client.post(
        f"/api/cases/{case_id}/arrangements",
        json={
            "total_amount": "1000.00",
            "installment_amount": "333.34",
            "frequency": "monthly",
            "start_date": start.isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201

    list_resp = await client.get(
        f"/api/cases/{case_id}/arrangements", headers=auth_headers
    )
    arr = list_resp.json()[0]
    installments = arr["installments"]
    assert len(installments) == 3  # ceil(1000 / 333.34) = 3

    # First two should be 333.34, last should be 333.32
    assert Decimal(installments[0]["amount"]) == Decimal("333.34")
    assert Decimal(installments[1]["amount"]) == Decimal("333.34")
    assert Decimal(installments[2]["amount"]) == Decimal("333.32")

    # Total should be exactly 1000.00
    total = sum(Decimal(i["amount"]) for i in installments)
    assert total == Decimal("1000.00")


# ── Test: only one active arrangement per case ───────────────────────────────


@pytest.mark.asyncio
async def test_cannot_create_second_active_arrangement(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Should reject creating a second active arrangement."""
    case_id, _ = await _create_case_with_claim(
        client, auth_headers, str(test_company.id)
    )

    start = date.today() + timedelta(days=7)
    payload = {
        "total_amount": "1000.00",
        "installment_amount": "500.00",
        "frequency": "monthly",
        "start_date": start.isoformat(),
    }

    # First should succeed
    resp1 = await client.post(
        f"/api/cases/{case_id}/arrangements", json=payload, headers=auth_headers
    )
    assert resp1.status_code == 201

    # Second should fail with 409 Conflict
    resp2 = await client.post(
        f"/api/cases/{case_id}/arrangements", json=payload, headers=auth_headers
    )
    assert resp2.status_code == 409


# ── Test: record installment payment ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_record_installment_payment(
    client: AsyncClient, auth_headers: dict, test_company: Contact, db
):
    """Recording a payment on an installment should update its status."""
    await _seed_interest_rates(db)
    case_id, _ = await _create_case_with_claim(
        client, auth_headers, str(test_company.id)
    )

    start = date.today() + timedelta(days=7)
    arr_resp = await client.post(
        f"/api/cases/{case_id}/arrangements",
        json={
            "total_amount": "1200.00",
            "installment_amount": "400.00",
            "frequency": "monthly",
            "start_date": start.isoformat(),
        },
        headers=auth_headers,
    )
    assert arr_resp.status_code == 201
    arr_id = arr_resp.json()["id"]

    # Get installments
    list_resp = await client.get(
        f"/api/cases/{case_id}/arrangements", headers=auth_headers
    )
    first_inst = list_resp.json()[0]["installments"][0]
    inst_id = first_inst["id"]

    # Record payment
    pay_resp = await client.post(
        f"/api/cases/{case_id}/arrangements/{arr_id}/installments/{inst_id}/record-payment",
        json={
            "amount": "400.00",
            "payment_date": date.today().isoformat(),
            "payment_method": "bank",
        },
        headers=auth_headers,
    )
    assert pay_resp.status_code == 200
    inst_result = pay_resp.json()
    assert inst_result["status"] == "paid"
    assert Decimal(inst_result["paid_amount"]) == Decimal("400.00")
    assert inst_result["payment_id"] is not None

    # Check that a Payment was also created
    payments_resp = await client.get(
        f"/api/cases/{case_id}/payments", headers=auth_headers
    )
    payments = payments_resp.json()
    assert len(payments) >= 1
    assert any(
        Decimal(p["amount"]) == Decimal("400.00") for p in payments
    )


@pytest.mark.asyncio
async def test_partial_payment_on_installment(
    client: AsyncClient, auth_headers: dict, test_company: Contact, db
):
    """A payment less than the installment amount should set status partial."""
    await _seed_interest_rates(db)
    case_id, _ = await _create_case_with_claim(
        client, auth_headers, str(test_company.id)
    )

    start = date.today() + timedelta(days=7)
    arr_resp = await client.post(
        f"/api/cases/{case_id}/arrangements",
        json={
            "total_amount": "1000.00",
            "installment_amount": "500.00",
            "frequency": "monthly",
            "start_date": start.isoformat(),
        },
        headers=auth_headers,
    )
    arr_id = arr_resp.json()["id"]

    list_resp = await client.get(
        f"/api/cases/{case_id}/arrangements", headers=auth_headers
    )
    inst_id = list_resp.json()[0]["installments"][0]["id"]

    pay_resp = await client.post(
        f"/api/cases/{case_id}/arrangements/{arr_id}/installments/{inst_id}/record-payment",
        json={
            "amount": "250.00",
            "payment_date": date.today().isoformat(),
        },
        headers=auth_headers,
    )
    assert pay_resp.status_code == 200
    assert pay_resp.json()["status"] == "partial"


# ── Test: auto-complete arrangement ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_arrangement_auto_completes_when_all_paid(
    client: AsyncClient, auth_headers: dict, test_company: Contact, db
):
    """Arrangement should auto-complete when all installments are paid."""
    await _seed_interest_rates(db)
    case_id, _ = await _create_case_with_claim(
        client, auth_headers, str(test_company.id)
    )

    start = date.today() + timedelta(days=7)
    arr_resp = await client.post(
        f"/api/cases/{case_id}/arrangements",
        json={
            "total_amount": "600.00",
            "installment_amount": "300.00",
            "frequency": "monthly",
            "start_date": start.isoformat(),
        },
        headers=auth_headers,
    )
    arr_id = arr_resp.json()["id"]

    # Get installments
    list_resp = await client.get(
        f"/api/cases/{case_id}/arrangements", headers=auth_headers
    )
    installments = list_resp.json()[0]["installments"]

    # Pay both installments
    for inst in installments:
        resp = await client.post(
            f"/api/cases/{case_id}/arrangements/{arr_id}/installments/{inst['id']}/record-payment",
            json={
                "amount": "300.00",
                "payment_date": date.today().isoformat(),
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200

    # Check arrangement is completed
    list_resp = await client.get(
        f"/api/cases/{case_id}/arrangements", headers=auth_headers
    )
    assert list_resp.json()[0]["status"] == "completed"


# ── Test: default arrangement ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_default_arrangement(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Defaulting an arrangement should mark pending installments as missed."""
    case_id, _ = await _create_case_with_claim(
        client, auth_headers, str(test_company.id)
    )

    start = date.today() + timedelta(days=7)
    arr_resp = await client.post(
        f"/api/cases/{case_id}/arrangements",
        json={
            "total_amount": "900.00",
            "installment_amount": "300.00",
            "frequency": "monthly",
            "start_date": start.isoformat(),
        },
        headers=auth_headers,
    )
    arr_id = arr_resp.json()["id"]

    # Default it
    resp = await client.patch(
        f"/api/cases/{case_id}/arrangements/{arr_id}/default",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "defaulted"

    # All installments should be missed
    list_resp = await client.get(
        f"/api/cases/{case_id}/arrangements", headers=auth_headers
    )
    for inst in list_resp.json()[0]["installments"]:
        assert inst["status"] == "missed"


# ── Test: cancel arrangement ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_arrangement(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Cancelling an arrangement should waive all pending installments."""
    case_id, _ = await _create_case_with_claim(
        client, auth_headers, str(test_company.id)
    )

    start = date.today() + timedelta(days=7)
    arr_resp = await client.post(
        f"/api/cases/{case_id}/arrangements",
        json={
            "total_amount": "1000.00",
            "installment_amount": "500.00",
            "frequency": "monthly",
            "start_date": start.isoformat(),
        },
        headers=auth_headers,
    )
    arr_id = arr_resp.json()["id"]

    resp = await client.patch(
        f"/api/cases/{case_id}/arrangements/{arr_id}/cancel",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    list_resp = await client.get(
        f"/api/cases/{case_id}/arrangements", headers=auth_headers
    )
    for inst in list_resp.json()[0]["installments"]:
        assert inst["status"] == "waived"


# ── Test: waive single installment ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_waive_installment(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Waiving a single installment should set it to waived."""
    case_id, _ = await _create_case_with_claim(
        client, auth_headers, str(test_company.id)
    )

    start = date.today() + timedelta(days=7)
    arr_resp = await client.post(
        f"/api/cases/{case_id}/arrangements",
        json={
            "total_amount": "1000.00",
            "installment_amount": "500.00",
            "frequency": "monthly",
            "start_date": start.isoformat(),
        },
        headers=auth_headers,
    )
    arr_id = arr_resp.json()["id"]

    list_resp = await client.get(
        f"/api/cases/{case_id}/arrangements", headers=auth_headers
    )
    inst_id = list_resp.json()[0]["installments"][0]["id"]

    resp = await client.patch(
        f"/api/cases/{case_id}/arrangements/{arr_id}/installments/{inst_id}/waive",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "waived"


# ── Test: overdue detection ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mark_overdue_installments(
    client: AsyncClient,
    auth_headers: dict,
    test_company: Contact,
    db,
):
    """Installments past due_date should be marked overdue by the service."""
    from app.collections.service import mark_overdue_installments

    case_id, _ = await _create_case_with_claim(
        client, auth_headers, str(test_company.id)
    )

    # Create arrangement with start date in the past
    past_start = date.today() - timedelta(days=60)
    arr_resp = await client.post(
        f"/api/cases/{case_id}/arrangements",
        json={
            "total_amount": "600.00",
            "installment_amount": "200.00",
            "frequency": "monthly",
            "start_date": past_start.isoformat(),
        },
        headers=auth_headers,
    )
    assert arr_resp.status_code == 201

    # Run overdue check
    count = await mark_overdue_installments(db)
    await db.commit()

    # At least the first installment(s) should be overdue
    assert count >= 1

    # Verify via API
    list_resp = await client.get(
        f"/api/cases/{case_id}/arrangements", headers=auth_headers
    )
    installments = list_resp.json()[0]["installments"]
    overdue_count = sum(1 for i in installments if i["status"] == "overdue")
    assert overdue_count >= 1


# ── Test: weekly frequency ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_weekly_frequency_installments(
    client: AsyncClient, auth_headers: dict, test_company: Contact
):
    """Weekly frequency should generate installments 7 days apart."""
    case_id, _ = await _create_case_with_claim(
        client, auth_headers, str(test_company.id)
    )

    start = date.today() + timedelta(days=7)
    resp = await client.post(
        f"/api/cases/{case_id}/arrangements",
        json={
            "total_amount": "400.00",
            "installment_amount": "100.00",
            "frequency": "weekly",
            "start_date": start.isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201

    list_resp = await client.get(
        f"/api/cases/{case_id}/arrangements", headers=auth_headers
    )
    installments = list_resp.json()[0]["installments"]
    assert len(installments) == 4

    # Check dates are 7 days apart
    dates = [date.fromisoformat(i["due_date"]) for i in installments]
    for i in range(1, len(dates)):
        assert (dates[i] - dates[i - 1]).days == 7
