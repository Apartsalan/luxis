"""Wachter (S251-review): bij een CONSUMENT is de WIK-staffel dwingend.

Foutsoort: de kosten-afspraak van de opdrachtgever (contractuele 15%) lekt naar een
consumentendossier. Dat mag niet — art. 6:96 BW is dwingend recht — en het is extra
gevaarlijk sinds brieven het dossierbedrag afdrukken: een 14-dagenbrief met een te
hoog BIK-bedrag is ongeldig (art. 6:96 lid 6 BW) en kost het recht op incassokosten
volledig.

Twee lekken zaten er (beide bewezen op het ECHTE aanmaak-/wijzigpad vóór de fix):
1. `create_case` erfde de klantkaart-standaard ongeacht het debiteurtype;
2. de wijzig-grendel keek alleen naar een vast bedrag, niet naar een percentage.

Beide vormen én beide routes staan hier, plus de zakelijke tegenhanger — want de
fix mag B2B niet stilletjes zijn 15% afpakken.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.cases.schemas import CaseCreate, CaseUpdate
from app.cases.service import create_case, update_case
from app.collections.models import Claim, InterestRate
from app.collections.service import case_calc_kwargs, get_financial_summary
from app.relations.models import Contact
from app.shared.exceptions import BadRequestError

HOOFDSOM = Decimal("10000.00")
STAFFEL = Decimal("875.00")          # WIK over € 10.000
VIJFTIEN_PCT = Decimal("1500.00")    # wat de bureau-afspraak zou opleveren


@pytest_asyncio.fixture
async def bureau(db: AsyncSession, test_tenant: Tenant) -> Contact:
    """Klantkaart zoals de zes incassobureaus: 15% + bodem € 40."""
    c = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Bureau B.V.",
        is_btw_plichtig=True,
        default_bik_override_percentage=Decimal("15.00"),
        default_bik_minimum_fee=Decimal("40.00"),
    )
    db.add(c)
    db.add(
        InterestRate(
            id=uuid.uuid4(),
            rate_type="statutory",
            rate=Decimal("4.00"),
            effective_from=date(2024, 1, 1),
        )
    )
    await db.commit()
    await db.refresh(c)
    return c


async def _nieuw_dossier(db, tenant_id, user_id, bureau, debtor_type, met_vordering=True):
    case = await create_case(
        db,
        tenant_id,
        user_id,
        CaseCreate(
            case_type="incasso",
            debtor_type=debtor_type,
            client_id=bureau.id,
            date_opened=date.today(),
        ),
    )
    if met_vordering:
        db.add(
            Claim(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                case_id=case.id,
                description="Factuur",
                principal_amount=HOOFDSOM,
                default_date=date.today(),
            )
        )
    await db.commit()
    await db.refresh(case)
    return case


@pytest.mark.asyncio
async def test_consumentendossier_erft_de_kosten_afspraak_niet(
    db: AsyncSession, test_tenant: Tenant, test_user, bureau: Contact
):
    """Nieuw b2c-dossier bij een 15%-bureau → géén afspraak, dus de staffel."""
    case = await _nieuw_dossier(db, test_tenant.id, test_user.id, bureau, "b2c")

    assert case.bik_override_percentage is None
    assert case.bik_override is None

    s = await get_financial_summary(db, test_tenant.id, case.id, **case_calc_kwargs(case))
    assert s["bik_amount"] == STAFFEL
    assert s["bik_amount"] != VIJFTIEN_PCT


@pytest.mark.asyncio
async def test_zakelijk_dossier_erft_de_kosten_afspraak_wel(
    db: AsyncSession, test_tenant: Tenant, test_user, bureau: Contact
):
    """Tegenproef: B2B moet de 15% juist WEL krijgen — anders is de fix te breed."""
    case = await _nieuw_dossier(db, test_tenant.id, test_user.id, bureau, "b2b")

    assert case.bik_override_percentage == Decimal("15.00")

    s = await get_financial_summary(db, test_tenant.id, case.id, **case_calc_kwargs(case))
    assert s["bik_amount"] == VIJFTIEN_PCT


@pytest.mark.asyncio
async def test_percentage_handmatig_op_consument_wordt_geblokkeerd(
    db: AsyncSession, test_tenant: Tenant, test_user, bureau: Contact
):
    """Het tweede lek: een PERCENTAGE boven de staffel kwam er ongehinderd langs."""
    case = await _nieuw_dossier(db, test_tenant.id, test_user.id, bureau, "b2c")

    with pytest.raises(BadRequestError) as fout:
        await update_case(
            db,
            test_tenant.id,
            case.id,
            CaseUpdate(bik_override_percentage=Decimal("15.00")),
        )
    assert "WIK-staffel" in str(fout.value)


@pytest.mark.asyncio
async def test_vast_bedrag_op_consument_blijft_geblokkeerd(
    db: AsyncSession, test_tenant: Tenant, test_user, bureau: Contact
):
    """De bestaande grendel (AUDIT-23) mag niet zijn weggevallen bij het verbreden."""
    case = await _nieuw_dossier(db, test_tenant.id, test_user.id, bureau, "b2c")

    with pytest.raises(BadRequestError):
        await update_case(
            db, test_tenant.id, case.id, CaseUpdate(bik_override=Decimal("1500.00"))
        )


@pytest.mark.asyncio
async def test_percentage_binnen_de_staffel_mag_wel_bij_een_consument(
    db: AsyncSession, test_tenant: Tenant, test_user, bureau: Contact
):
    """Niet alles blokkeren: 5% van € 10.000 = € 500 blijft onder € 875."""
    case = await _nieuw_dossier(db, test_tenant.id, test_user.id, bureau, "b2c")

    updated = await update_case(
        db, test_tenant.id, case.id, CaseUpdate(bik_override_percentage=Decimal("5.00"))
    )
    await db.commit()
    assert updated.bik_override_percentage == Decimal("5.00")


@pytest.mark.asyncio
async def test_omzetten_naar_consument_beoordeelt_de_bestaande_afspraak(
    db: AsyncSession, test_tenant: Tenant, test_user, bureau: Contact
):
    """Sluiproute: eerst zakelijk (erft 15%), daarna omzetten naar particulier.

    Zonder deze check zou het dossier de 15% houden terwijl het inmiddels een
    consument is.
    """
    case = await _nieuw_dossier(db, test_tenant.id, test_user.id, bureau, "b2b")
    assert case.bik_override_percentage == Decimal("15.00")

    with pytest.raises(BadRequestError):
        await update_case(db, test_tenant.id, case.id, CaseUpdate(debtor_type="b2c"))


@pytest.mark.asyncio
async def test_zakelijk_percentage_boven_staffel_blijft_toegestaan(
    db: AsyncSession, test_tenant: Tenant, test_user, bureau: Contact
):
    """B2B mag contractueel meer dan de staffel — de grendel geldt alleen b2c."""
    case = await _nieuw_dossier(db, test_tenant.id, test_user.id, bureau, "b2b")

    updated = await update_case(
        db, test_tenant.id, case.id, CaseUpdate(bik_override_percentage=Decimal("20.00"))
    )
    await db.commit()
    assert updated.bik_override_percentage == Decimal("20.00")
