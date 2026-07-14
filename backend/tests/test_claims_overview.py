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


async def _claim(
    db, tenant_id, case_id, *, number, amount, file_id=None, active=True,
    inv_date=date(2026, 1, 1),
):
    claim = Claim(
        id=uuid.uuid4(), tenant_id=tenant_id, case_id=case_id,
        description=f"Factuur {number}", principal_amount=Decimal(amount),
        default_date=date(2026, 1, 1), invoice_number=number,
        invoice_date=inv_date, invoice_file_id=file_id, is_active=active,
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


@pytest.mark.asyncio
async def test_overview_client_filter_and_clients_endpoint(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case_a = await _case(db, test_tenant.id, number="2026-00010")
    case_b = await _case(db, test_tenant.id, number="2026-00011")
    await _claim(db, test_tenant.id, case_a.id, number="A-1", amount="100.00")
    await _claim(db, test_tenant.id, case_b.id, number="B-1", amount="200.00")
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    hdr = {"Authorization": f"Bearer {token}"}

    # Dropdown-voeding: beide opdrachtgevers komen terug
    clients = (await client.get("/api/claims/clients", headers=hdr)).json()
    assert {c["id"] for c in clients} == {str(case_a.client_id), str(case_b.client_id)}

    # Filter op één opdrachtgever
    resp = await client.get(
        f"/api/claims?client_id={case_a.client_id}", headers=hdr
    )
    numbers = [r["invoice_number"] for r in resp.json()["items"]]
    assert numbers == ["A-1"]


@pytest.mark.asyncio
async def test_overview_date_range_and_has_file(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case = await _case(db, test_tenant.id, number="2026-00012")
    file_id = await _case_file(db, test_tenant.id, case.id, test_user.id)
    await _claim(db, test_tenant.id, case.id, number="JAN", amount="10.00", inv_date=date(2026, 1, 15), file_id=file_id)
    await _claim(db, test_tenant.id, case.id, number="MRT", amount="20.00", inv_date=date(2026, 3, 15))
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    hdr = {"Authorization": f"Bearer {token}"}

    # Factuurdatum-bereik: alleen februari-en-eerder valt de MRT-vordering buiten
    resp = await client.get(
        "/api/claims?date_from=2026-01-01&date_to=2026-02-01", headers=hdr
    )
    assert [r["invoice_number"] for r in resp.json()["items"]] == ["JAN"]

    # Wel factuur-PDF
    with_file = await client.get("/api/claims?has_file=true", headers=hdr)
    assert [r["invoice_number"] for r in with_file.json()["items"]] == ["JAN"]
    assert with_file.json()["items"][0]["invoice_file_id"] == str(file_id)

    # Geen factuur-PDF
    without_file = await client.get("/api/claims?has_file=false", headers=hdr)
    assert [r["invoice_number"] for r in without_file.json()["items"]] == ["MRT"]
    assert without_file.json()["items"][0]["invoice_file_id"] is None


@pytest.mark.asyncio
async def test_overview_sort_by_principal(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case = await _case(db, test_tenant.id, number="2026-00013")
    await _claim(db, test_tenant.id, case.id, number="KLEIN", amount="50.00")
    await _claim(db, test_tenant.id, case.id, number="GROOT", amount="9000.00")
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    hdr = {"Authorization": f"Bearer {token}"}

    asc = await client.get("/api/claims?sort_by=principal_amount&sort_dir=asc", headers=hdr)
    assert [r["invoice_number"] for r in asc.json()["items"]] == ["KLEIN", "GROOT"]

    desc = await client.get("/api/claims?sort_by=principal_amount&sort_dir=desc", headers=hdr)
    assert [r["invoice_number"] for r in desc.json()["items"]] == ["GROOT", "KLEIN"]
