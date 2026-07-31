"""S255 — wachter op het consument-etiket dat op een onderneming staat.

De BaseNet-import zet `debtor_type` op b2c zodra de wederpartij een PERSOON is
(`scripts/basenet/mapping.py::resolve_debtor_type`). Een eenmanszaak staat in
BaseNet als persoon — daar valt hij precies tussenuit. S252 vond dat op
IN100077 (Kaandorp): etiket consument, in werkelijkheid eenmanszaak, € 6.300
verschil, omdat de dwingende WIK-staffel alleen voor echte consumenten geldt.

Op het moment van importeren is het niet te zien: het persoonsrecord in de
export bevat geen KvK-nummer of bedrijfsveld (S255 nagemeten op de echte
export). De fout wordt pas zichtbaar als er later ondernemingsgegevens op de
contactkaart komen. Deze sweep loopt de hele database af en vangt die SOORT.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.cases.models import Case
from app.collections.compliance import find_debtor_type_mismatch
from app.relations.models import Contact


async def _case_met_wederpartij(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    case_number: str,
    debtor_type: str,
    contact_type: str = "person",
    legal_form: str | None = None,
    kvk_number: str | None = None,
    status: str = "nieuw",
) -> Case:
    client = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Opdrachtgever B.V.",
    )
    wederpartij = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type=contact_type,
        name="Kaandorp",
        legal_form=legal_form,
        kvk_number=kvk_number,
    )
    db.add_all([client, wederpartij])
    await db.flush()

    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number=case_number,
        case_type="incasso",
        status=status,
        debtor_type=debtor_type,
        client_id=client.id,
        opposing_party_id=wederpartij.id,
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()
    return case


@pytest.mark.asyncio
async def test_consument_etiket_met_rechtsvorm_wordt_gevonden(
    db: AsyncSession, test_tenant: Tenant
):
    """De Kaandorp-fout: b2c-etiket, wederpartij blijkt eenmanszaak."""
    await _case_met_wederpartij(
        db,
        test_tenant.id,
        case_number="2026-95001",
        debtor_type="b2c",
        legal_form="Eenmanszaak",
    )

    treffers = await find_debtor_type_mismatch(db, test_tenant.id)

    assert len(treffers) == 1
    assert treffers[0]["case_number"] == "2026-95001"
    assert treffers[0]["legal_form"] == "Eenmanszaak"
    assert treffers[0]["afgesloten"] is False


@pytest.mark.asyncio
async def test_consument_etiket_met_kvk_nummer_wordt_gevonden(
    db: AsyncSession, test_tenant: Tenant
):
    """Ook zónder rechtsvorm: een KvK-nummer bewijst al een onderneming.

    Zou de wachter alleen op `legal_form` kijken, dan beet hij pas ná een
    KvK-bevraging — en die gebeurt niet vanzelf op elke contactkaart.
    """
    await _case_met_wederpartij(
        db,
        test_tenant.id,
        case_number="2026-95002",
        debtor_type="b2c",
        kvk_number="72908475",
    )

    treffers = await find_debtor_type_mismatch(db, test_tenant.id)

    assert [t["case_number"] for t in treffers] == ["2026-95002"]
    assert treffers[0]["kvk_number"] == "72908475"


@pytest.mark.asyncio
async def test_echte_consument_geeft_geen_melding(
    db: AsyncSession, test_tenant: Tenant
):
    """Een particulier heeft geen rechtsvorm en geen KvK-nummer — geen treffer.

    Zonder deze grens zou de wachter alle 80 consumentendossiers melden en
    daarmee zichzelf uitschakelen.
    """
    await _case_met_wederpartij(
        db,
        test_tenant.id,
        case_number="2026-95003",
        debtor_type="b2c",
    )

    assert await find_debtor_type_mismatch(db, test_tenant.id) == []


@pytest.mark.asyncio
async def test_zakelijk_etiket_op_onderneming_is_correct(
    db: AsyncSession, test_tenant: Tenant
):
    """b2b + rechtsvorm is juist de goede situatie — nooit melden."""
    await _case_met_wederpartij(
        db,
        test_tenant.id,
        case_number="2026-95004",
        debtor_type="b2b",
        contact_type="company",
        legal_form="Besloten Vennootschap",
        kvk_number="88601536",
    )

    assert await find_debtor_type_mismatch(db, test_tenant.id) == []


@pytest.mark.asyncio
async def test_lege_kvk_string_telt_niet_als_onderneming(
    db: AsyncSession, test_tenant: Tenant
):
    """De import schrijft lege strings i.p.v. NULL; die mogen niet meetellen.

    Op prod staan 288 relaties met `kvk_number = ''`. Zonder deze grens zou de
    wachter die allemaal als onderneming aanmerken.
    """
    await _case_met_wederpartij(
        db,
        test_tenant.id,
        case_number="2026-95005",
        debtor_type="b2c",
        kvk_number="",
    )

    assert await find_debtor_type_mismatch(db, test_tenant.id) == []


@pytest.mark.asyncio
async def test_lopend_dossier_staat_boven_archief(
    db: AsyncSession, test_tenant: Tenant
):
    """Bij een lopend dossier gaat er nú nog een verkeerd bedrag de deur uit;
    archief is opruimwerk. De melding noemt het eerste dossier als voorbeeld,
    dus die volgorde bepaalt wat Lisanne als eerste ziet."""
    await _case_met_wederpartij(
        db,
        test_tenant.id,
        case_number="2026-95006-archief",
        debtor_type="b2c",
        legal_form="Eenmanszaak",
        status="afgesloten",
    )
    await _case_met_wederpartij(
        db,
        test_tenant.id,
        case_number="2026-95007-lopend",
        debtor_type="b2c",
        legal_form="Eenmanszaak",
        status="in_behandeling",
    )

    treffers = await find_debtor_type_mismatch(db, test_tenant.id)

    assert [t["case_number"] for t in treffers] == [
        "2026-95007-lopend",
        "2026-95006-archief",
    ]
    assert treffers[0]["afgesloten"] is False
    assert treffers[1]["afgesloten"] is True
