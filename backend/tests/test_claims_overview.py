"""Tenant-breed Vorderingen-overzicht (GET /api/claims) — de debiteuren-facturen
die aan de dossiers hangen, los van de kantoorfacturen (invoices-module)."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token
from app.cases.models import Case, CaseFile
from app.collections.models import Claim
from app.relations.models import Contact


async def _case_file(db, tenant_id, case_id, user_id):
    cf = CaseFile(
        id=uuid.uuid4(), tenant_id=tenant_id, case_id=case_id,
        original_filename="factuur.pdf", stored_filename="f.pdf",
        file_size=9, content_type="application/pdf", uploaded_by=user_id,
    )
    db.add(cf)
    await db.flush()
    return cf.id


async def _case(db, tenant_id, *, number, status="in_behandeling", debtor="Debiteur BV"):
    client = Contact(id=uuid.uuid4(), tenant_id=tenant_id, contact_type="person", name="Cliënt")
    opp = Contact(id=uuid.uuid4(), tenant_id=tenant_id, contact_type="company", name=debtor)
    db.add_all([client, opp])
    await db.flush()
    case = Case(
        id=uuid.uuid4(), tenant_id=tenant_id, case_number=number, case_type="incasso",
        status=status, debtor_type="b2b", client_id=client.id, opposing_party_id=opp.id,
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()
    return case


async def _claim(db, tenant_id, case_id, *, number, amount, file_id=None, active=True):
    claim = Claim(
        id=uuid.uuid4(), tenant_id=tenant_id, case_id=case_id,
        description=f"Factuur {number}", principal_amount=Decimal(amount),
        default_date=date(2026, 1, 1), invoice_number=number,
        invoice_date=date(2026, 1, 1), invoice_file_id=file_id, is_active=active,
    )
    db.add(claim)
    await db.flush()
    return claim


@pytest.mark.asyncio
async def test_overview_lists_claims_with_case_and_debtor(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case = await _case(db, test_tenant.id, number="2026-00001", debtor="Wanbetaler BV")
    file_id = await _case_file(db, test_tenant.id, case.id, test_user.id)
    await _claim(db, test_tenant.id, case.id, number="F-100", amount="5000.00", file_id=file_id)
    await _claim(db, test_tenant.id, case.id, number="F-101", amount="1500.00")
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.get("/api/claims", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    assert Decimal(str(body["total_principal"])) == Decimal("6500.00")
    row = next(r for r in body["items"] if r["invoice_number"] == "F-100")
    assert row["case_number"] == "2026-00001"
    assert row["debtor_name"] == "Wanbetaler BV"
    assert row["has_invoice_file"] is True
    assert next(r for r in body["items"] if r["invoice_number"] == "F-101")["has_invoice_file"] is False


@pytest.mark.asyncio
async def test_overview_excludes_inactive_and_searches(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case = await _case(db, test_tenant.id, number="2026-00002", debtor="Zoekbaar BV")
    await _claim(db, test_tenant.id, case.id, number="VIND-MIJ", amount="100.00")
    await _claim(db, test_tenant.id, case.id, number="WEG", amount="999.00", active=False)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    # Inactieve vordering telt niet mee
    resp = await client.get("/api/claims", headers={"Authorization": f"Bearer {token}"})
    numbers = [r["invoice_number"] for r in resp.json()["items"]]
    assert "VIND-MIJ" in numbers and "WEG" not in numbers

    # Zoeken op debiteurnaam
    resp2 = await client.get(
        "/api/claims?search=Zoekbaar", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.json()["total"] == 1
    assert resp2.json()["items"][0]["invoice_number"] == "VIND-MIJ"


@pytest.mark.asyncio
async def test_overview_only_open_filter(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    open_case = await _case(db, test_tenant.id, number="2026-00003", status="in_behandeling")
    closed_case = await _case(db, test_tenant.id, number="2026-00004", status="afgesloten")
    await _claim(db, test_tenant.id, open_case.id, number="OPEN-1", amount="200.00")
    await _claim(db, test_tenant.id, closed_case.id, number="DICHT-1", amount="300.00")
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.get(
        "/api/claims?only_open=true", headers={"Authorization": f"Bearer {token}"}
    )
    numbers = [r["invoice_number"] for r in resp.json()["items"]]
    assert "OPEN-1" in numbers and "DICHT-1" not in numbers
