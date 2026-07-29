"""S230/V1 — DB-brede wachter op incassokosten boven de WIK-staffel.

De 27 dossiers uit S229 (samen €9.794,65 te veel) kwamen via de BaseNet-import
binnen en passeerden dus géén van de bestaande wachters: die zitten op de
wijzig-route (AUDIT-23) en op de verzendcontrole, allebei op het moment van
handelen. Deze sweep loopt de hele database af en vangt de SOORT — elke import
of directe schrijfactie die er buitenom komt.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.cases.models import Case
from app.collections.compliance import find_bik_above_staffel
from app.collections.models import Claim
from app.relations.models import Contact

# Hoofdsom €10.000 → staffel = 375 + 250 + 250 = €875,00 (art. 6:96 BW).
# Vlakke 15% zoals in de import: €1.500,00 → €625,00 te veel. Dit is exact
# dossier IN100298 uit de S229-meting, met de hand nagerekend.
HOOFDSOM = Decimal("10000.00")
STAFFEL = Decimal("875.00")
VLAKKE_15_PCT = Decimal("1500.00")


async def _case_met_bik(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    case_number: str,
    debtor_type: str,
    bik_override: Decimal | None = None,
    bik_override_percentage: Decimal | None = None,
    bik_minimum_fee: Decimal | None = None,
    client_btw_plichtig: bool = True,
) -> Case:
    client = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Opdrachtgever B.V.",
        is_btw_plichtig=client_btw_plichtig,
    )
    debtor = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="person",
        name="Debiteur Consument",
    )
    db.add_all([client, debtor])
    await db.flush()

    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number=case_number,
        case_type="incasso",
        status="nieuw",
        debtor_type=debtor_type,
        client_id=client.id,
        opposing_party_id=debtor.id,
        date_opened=date.today(),
        bik_override=bik_override,
        bik_override_percentage=bik_override_percentage,
        bik_minimum_fee=bik_minimum_fee,
    )
    db.add(case)
    await db.flush()

    db.add(
        Claim(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            case_id=case.id,
            description="Factuur",
            principal_amount=HOOFDSOM,
            invoice_date=date.today(),
            default_date=date.today(),
        )
    )
    await db.flush()
    return case


@pytest.mark.asyncio
async def test_sweep_vindt_vlakke_15_procent_bij_consument(
    db: AsyncSession, test_tenant: Tenant
):
    await _case_met_bik(
        db,
        test_tenant.id,
        case_number="2026-96001",
        debtor_type="b2c",
        bik_override=VLAKKE_15_PCT,
    )

    treffers = await find_bik_above_staffel(db, test_tenant.id)

    assert len(treffers) == 1
    assert treffers[0]["case_number"] == "2026-96001"
    assert treffers[0]["staffel"] == STAFFEL
    assert treffers[0]["te_veel"] == VLAKKE_15_PCT - STAFFEL  # € 625,00
    assert treffers[0]["afgesloten"] is False


@pytest.mark.asyncio
async def test_sweep_vindt_ook_zaak_zonder_vorderingen(
    db: AsyncSession, test_tenant: Tenant
):
    """Zonder vorderingen is de hoofdsom 0 → elk handmatig bedrag is te hoog.

    De twee bestaande wachters oordelen zo ook; viel de sweep hierop stil, dan
    was hij een tweede mening in plaats van een wachter.
    """
    case = await _case_met_bik(
        db,
        test_tenant.id,
        case_number="2026-96006",
        debtor_type="b2c",
        bik_override=Decimal("500.00"),
    )
    await db.execute(delete(Claim).where(Claim.case_id == case.id))
    await db.flush()

    treffers = await find_bik_above_staffel(db, test_tenant.id)

    assert [t["case_number"] for t in treffers] == ["2026-96006"]


@pytest.mark.asyncio
async def test_sweep_merkt_afgesloten_dossier_als_archief(
    db: AsyncSession, test_tenant: Tenant
):
    """Vrijwel de hele BaseNet-import kwam binnen als 'afgesloten'; de melding
    moet lopend en archief uit elkaar kunnen houden."""
    case = await _case_met_bik(
        db,
        test_tenant.id,
        case_number="2026-96007",
        debtor_type="b2c",
        bik_override=VLAKKE_15_PCT,
    )
    case.status = "afgesloten"
    await db.flush()

    treffers = await find_bik_above_staffel(db, test_tenant.id)

    assert len(treffers) == 1
    assert treffers[0]["afgesloten"] is True


@pytest.mark.asyncio
async def test_sweep_laat_bedrag_op_de_staffel_met_rust(
    db: AsyncSession, test_tenant: Tenant
):
    """Precies de staffel is toegestaan — de wachter mag niet op gelijk afgaan."""
    await _case_met_bik(
        db,
        test_tenant.id,
        case_number="2026-96002",
        debtor_type="b2c",
        bik_override=STAFFEL,
    )

    assert await find_bik_above_staffel(db, test_tenant.id) == []


@pytest.mark.asyncio
async def test_sweep_negeert_zakelijke_debiteur(db: AsyncSession, test_tenant: Tenant):
    """Bij B2B is de staffel niet dwingend; een hoger bedrag is daar geen fout."""
    await _case_met_bik(
        db,
        test_tenant.id,
        case_number="2026-96003",
        debtor_type="b2b",
        bik_override=VLAKKE_15_PCT,
    )

    assert await find_bik_above_staffel(db, test_tenant.id) == []


@pytest.mark.asyncio
async def test_sweep_negeert_zaak_zonder_handmatig_bedrag(
    db: AsyncSession, test_tenant: Tenant
):
    """Zonder override rekent het systeem zelf de staffel — niets te melden."""
    await _case_met_bik(
        db,
        test_tenant.id,
        case_number="2026-96004",
        debtor_type="b2c",
        bik_override=None,
    )

    assert await find_bik_above_staffel(db, test_tenant.id) == []


@pytest.mark.asyncio
async def test_sweep_telt_btw_mee_bij_niet_btw_plichtige_opdrachtgever(
    db: AsyncSession, test_tenant: Tenant
):
    """Kan de opdrachtgever de btw niet verrekenen, dan mag staffel + 21%.

    €875,00 + 21% = €1.058,75; de vlakke 15% (€1.500,00) blijft ook dan te hoog,
    maar het te-veel is navenant lager.
    """
    await _case_met_bik(
        db,
        test_tenant.id,
        case_number="2026-96005",
        debtor_type="b2c",
        bik_override=VLAKKE_15_PCT,
        client_btw_plichtig=False,
    )

    treffers = await find_bik_above_staffel(db, test_tenant.id)

    assert len(treffers) == 1
    assert treffers[0]["staffel"] == Decimal("1058.75")
    assert treffers[0]["te_veel"] == Decimal("441.25")


# ── S251: de sweep moet OOK de percentage-afspraak zien ──────────────────────
#
# Het gat: de sweep filterde op `bik_override IS NOT NULL` en zag een percentage
# dus nooit. Sinds de klantkaarten een 15%-standaard hebben, erft élk nieuw
# dossier precies die vorm — een consumentendossier zou stil boven de dwingende
# staffel kunnen uitkomen zonder dat één wachter aanslaat.


@pytest.mark.asyncio
async def test_sweep_vindt_percentage_afspraak_bij_consument(
    db: AsyncSession, test_tenant: Tenant
):
    """15% van € 10.000 = € 1.500 vs staffel € 875 → € 625 te veel."""
    await _case_met_bik(
        db,
        test_tenant.id,
        case_number="2026-96007",
        debtor_type="b2c",
        bik_override_percentage=Decimal("15.00"),
    )

    treffers = await find_bik_above_staffel(db, test_tenant.id)

    assert len(treffers) == 1
    assert treffers[0]["case_number"] == "2026-96007"
    assert treffers[0]["bik_override"] == VLAKKE_15_PCT
    assert treffers[0]["te_veel"] == VLAKKE_15_PCT - STAFFEL
    assert treffers[0]["vorm"] == "15.00% van de hoofdsom"


@pytest.mark.asyncio
async def test_sweep_telt_de_bodem_mee_bij_een_klein_percentage(
    db: AsyncSession, test_tenant: Tenant
):
    """De bodem (`bik_minimum_fee`) hoort mee te tellen als hij het percentage
    optilt — anders lijkt een zaak schoon terwijl er meer gevorderd wordt.

    Hoofdsom € 10.000 met een percentage van 1% = € 100, maar een bodem van
    € 1.200 tilt dat naar € 1.200 — boven de staffel van € 875.
    """
    await _case_met_bik(
        db,
        test_tenant.id,
        case_number="2026-96008",
        debtor_type="b2c",
        bik_override_percentage=Decimal("1.00"),
        bik_minimum_fee=Decimal("1200.00"),
    )

    treffers = await find_bik_above_staffel(db, test_tenant.id)

    assert [t["case_number"] for t in treffers] == ["2026-96008"]
    assert treffers[0]["bik_override"] == Decimal("1200.00")
    assert treffers[0]["te_veel"] == Decimal("1200.00") - STAFFEL


@pytest.mark.asyncio
async def test_sweep_laat_zakelijke_percentage_afspraak_met_rust(
    db: AsyncSession, test_tenant: Tenant
):
    """B2B mag contractueel 15% — de staffel is daar niet dwingend."""
    await _case_met_bik(
        db,
        test_tenant.id,
        case_number="2026-96009",
        debtor_type="b2b",
        bik_override_percentage=Decimal("15.00"),
    )

    assert await find_bik_above_staffel(db, test_tenant.id) == []
