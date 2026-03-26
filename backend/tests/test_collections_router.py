"""Tests for the collections router — claims CRUD, payments CRUD, BIK, interest, derdengelden."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.collections.models import InterestRate
from app.relations.models import Contact

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_contact(db: AsyncSession, tenant_id: uuid.UUID) -> Contact:
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Debiteur B.V.",
        email="debiteur@example.nl",
    )
    db.add(contact)
    await db.flush()
    return contact


async def _create_case(
    db: AsyncSession, tenant_id: uuid.UUID, **overrides
) -> Case:
    client = await _create_contact(db, tenant_id)
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number="2026-00001",
        case_type="incasso",
        status="nieuw",
        debtor_type="b2b",
        date_opened=date.today(),
        client_id=client.id,
        interest_type="commercial",
    )
    defaults.update(overrides)
    case = Case(**defaults)
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


async def _seed_interest_rates(db: AsyncSession):
    """Seed a minimal interest rate so calculations work."""
    rate = InterestRate(
        id=uuid.uuid4(),
        rate_type="commercial",
        rate=Decimal("10.50"),
        effective_from=date(2024, 1, 1),
    )
    db.add(rate)
    await db.flush()


def _claim_payload(**overrides) -> dict:
    payload = {
        "description": "Openstaande factuur 2024-001",
        "principal_amount": "5000.00",
        "default_date": (date.today() - timedelta(days=90)).isoformat(),
        "invoice_number": "2024-001",
        "rate_basis": "yearly",
    }
    payload.update(overrides)
    return payload


def _payment_payload(**overrides) -> dict:
    payload = {
        "amount": "500.00",
        "payment_date": date.today().isoformat(),
        "description": "Deelbetaling",
        "payment_method": "bank",
    }
    payload.update(overrides)
    return payload


# ── Claims CRUD ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_claim(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    case = await _create_case(db, test_tenant.id)
    resp = await client.post(
        f"/api/cases/{case.id}/claims",
        json=_claim_payload(),
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "Openstaande factuur 2024-001"
    assert Decimal(data["principal_amount"]) == Decimal("5000.00")
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_claims(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    case = await _create_case(db, test_tenant.id)
    await client.post(f"/api/cases/{case.id}/claims", json=_claim_payload(), headers=auth_headers)
    await client.post(
        f"/api/cases/{case.id}/claims",
        json=_claim_payload(description="Factuur 2024-002", principal_amount="3000.00"),
        headers=auth_headers,
    )

    resp = await client.get(f"/api/cases/{case.id}/claims", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_update_claim(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    case = await _create_case(db, test_tenant.id)
    create_resp = await client.post(
        f"/api/cases/{case.id}/claims", json=_claim_payload(), headers=auth_headers
    )
    claim_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/cases/{case.id}/claims/{claim_id}",
        json={"description": "Gewijzigde factuur", "principal_amount": "7500.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Gewijzigde factuur"
    assert Decimal(resp.json()["principal_amount"]) == Decimal("7500.00")


@pytest.mark.asyncio
async def test_delete_claim(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    case = await _create_case(db, test_tenant.id)
    create_resp = await client.post(
        f"/api/cases/{case.id}/claims", json=_claim_payload(), headers=auth_headers
    )
    claim_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/cases/{case.id}/claims/{claim_id}", headers=auth_headers
    )
    assert del_resp.status_code == 204


# ── Payments CRUD ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_payment(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    await _seed_interest_rates(db)
    case = await _create_case(db, test_tenant.id)
    await client.post(f"/api/cases/{case.id}/claims", json=_claim_payload(), headers=auth_headers)

    resp = await client.post(
        f"/api/cases/{case.id}/payments",
        json=_payment_payload(),
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(data["amount"]) == Decimal("500.00")


@pytest.mark.asyncio
async def test_list_payments(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    await _seed_interest_rates(db)
    case = await _create_case(db, test_tenant.id)
    await client.post(f"/api/cases/{case.id}/claims", json=_claim_payload(), headers=auth_headers)
    await client.post(f"/api/cases/{case.id}/payments", json=_payment_payload(), headers=auth_headers)

    resp = await client.get(f"/api/cases/{case.id}/payments", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_delete_payment(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    await _seed_interest_rates(db)
    case = await _create_case(db, test_tenant.id)
    await client.post(f"/api/cases/{case.id}/claims", json=_claim_payload(), headers=auth_headers)
    create_resp = await client.post(
        f"/api/cases/{case.id}/payments", json=_payment_payload(), headers=auth_headers
    )
    payment_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/cases/{case.id}/payments/{payment_id}", headers=auth_headers
    )
    assert del_resp.status_code == 204


# ── BIK Calculation ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bik_calculation(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    case = await _create_case(db, test_tenant.id)
    await client.post(f"/api/cases/{case.id}/claims", json=_claim_payload(), headers=auth_headers)

    resp = await client.get(f"/api/cases/{case.id}/bik", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "bik_exclusive" in data
    assert "bik_inclusive" in data
    assert Decimal(data["principal"]) == Decimal("5000.00")


@pytest.mark.asyncio
async def test_bik_with_btw(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    case = await _create_case(db, test_tenant.id)
    await client.post(f"/api/cases/{case.id}/claims", json=_claim_payload(), headers=auth_headers)

    resp_no_btw = await client.get(f"/api/cases/{case.id}/bik", headers=auth_headers)
    resp_btw = await client.get(f"/api/cases/{case.id}/bik?include_btw=true", headers=auth_headers)

    assert resp_no_btw.status_code == 200
    assert resp_btw.status_code == 200


# ── Interest Calculation ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_interest_calculation(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    await _seed_interest_rates(db)
    case = await _create_case(db, test_tenant.id)
    await client.post(f"/api/cases/{case.id}/claims", json=_claim_payload(), headers=auth_headers)

    resp = await client.get(f"/api/cases/{case.id}/interest", headers=auth_headers)
    assert resp.status_code == 200


# ── Financial Summary ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_financial_summary(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    await _seed_interest_rates(db)
    case = await _create_case(db, test_tenant.id)
    await client.post(f"/api/cases/{case.id}/claims", json=_claim_payload(), headers=auth_headers)

    resp = await client.get(f"/api/cases/{case.id}/financial-summary", headers=auth_headers)
    assert resp.status_code == 200


# ── Interest Rates (reference endpoint) ──────────────────────────────────────


@pytest.mark.asyncio
async def test_list_interest_rates(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
):
    await _seed_interest_rates(db)
    resp = await client.get("/api/interest-rates", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ── Derdengelden ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_derdengelden_crud(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    case = await _create_case(db, test_tenant.id)

    create_resp = await client.post(
        f"/api/cases/{case.id}/derdengelden",
        json={
            "amount": "1500.00",
            "transaction_type": "deposit",
            "transaction_date": date.today().isoformat(),
            "description": "Ontvangst derdengelden",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201

    list_resp = await client.get(
        f"/api/cases/{case.id}/derdengelden", headers=auth_headers
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


@pytest.mark.asyncio
async def test_derdengelden_balance(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_tenant: Tenant
):
    case = await _create_case(db, test_tenant.id)

    resp = await client.get(
        f"/api/cases/{case.id}/derdengelden/balance", headers=auth_headers
    )
    assert resp.status_code == 200


# ── Tenant isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_claims_tenant_isolation(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
):
    case = await _create_case(db, test_tenant.id)
    await client.post(f"/api/cases/{case.id}/claims", json=_claim_payload(), headers=auth_headers)

    resp = await client.get(f"/api/cases/{case.id}/claims", headers=second_auth_headers)
    assert resp.status_code in (403, 404)


# ── Auth ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(client: AsyncClient):
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/cases/{fake_id}/claims")
    assert resp.status_code in (401, 403)
