"""Wachter (S251): een brief toont EXACT de bedragen van het Financieel-tabblad.

Foutsoort die hier bewaakt wordt — niet één los geval, maar de hele klasse:
de brief-context stelde zijn eigen `get_financial_summary`-aanroep samen en liet
daarbij de zaakinstellingen weg. Gevolg op prod (audit 29 juli): élke brief toonde
de kale WIK-staffel i.p.v. de kosten-afspraak van het dossier, en negeerde de
rente-bevriezing van een afgewikkeld dossier. 6 verstuurde sommaties met een
verkeerd bedrag.

Elke variant van de afspraak krijgt hier zijn eigen wachter, plus de bevriezing:
zodra iemand opnieuw een eigen aanroep bouwt, valt precies die variant om.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.cases.models import Case
from app.collections.models import Claim, InterestRate
from app.collections.service import case_calc_kwargs, get_financial_summary
from app.documents.docx_service import build_base_context
from app.relations.models import Contact

HOOFDSOM = Decimal("18934.11")
# WIK-staffel over € 18.934,11 = 375 + 250 + 250 + 89,34 = € 964,34
STAFFEL = Decimal("964.34")


def _bedrag(tekst: str) -> Decimal:
    """'€ 2.840,12' → Decimal('2840.12')."""
    return Decimal(tekst.replace("€", "").strip().replace(".", "").replace(",", "."))


async def _seed_rates(db: AsyncSession) -> None:
    db.add(
        InterestRate(
            id=uuid.uuid4(),
            rate_type="statutory",
            rate=Decimal("4.00"),
            effective_from=date(2024, 1, 1),
        )
    )
    await db.flush()


@pytest_asyncio.fixture
async def zaak(db: AsyncSession, test_tenant: Tenant, test_company: Contact) -> Case:
    """Zakelijk incassodossier, contractuele rente 2%/mnd samengesteld."""
    await _seed_rates(db)
    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number=f"{date.today().year}-09251",
        case_type="incasso",
        debtor_type="b2b",
        status="in_behandeling",
        interest_type="contractual",
        contractual_rate=Decimal("2.00"),
        contractual_compound=True,
        client_id=test_company.id,
        date_opened=date.today() - timedelta(days=300),
    )
    db.add(case)
    await db.flush()
    db.add(
        Claim(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_id=case.id,
            description="Factuur LW100730",
            principal_amount=HOOFDSOM,
            default_date=date.today() - timedelta(days=280),
            rate_basis="monthly",
        )
    )
    await db.commit()
    await db.refresh(case)
    return case


async def _brief_en_scherm(db: AsyncSession, tenant_id, case: Case) -> tuple[dict, dict]:
    """De bedragen zoals de BRIEF ze toont, naast die van het FINANCIEEL-TABBLAD."""
    context = await build_base_context(db, tenant_id, case)
    scherm = await get_financial_summary(
        db, tenant_id, case.id, **case_calc_kwargs(case)
    )
    return context, scherm


@pytest.mark.asyncio
async def test_vast_bedrag_afspraak_staat_in_de_brief(
    db: AsyncSession, test_tenant: Tenant, zaak: Case
):
    """Kosten-afspraak als VAST bedrag → brief toont dat bedrag, niet de staffel."""
    zaak.bik_override = Decimal("2840.12")  # 15% van de hoofdsom
    await db.commit()

    context, scherm = await _brief_en_scherm(db, test_tenant.id, zaak)

    assert _bedrag(context["bik_bedrag"]) == Decimal("2840.12")
    assert _bedrag(context["bik_bedrag"]) != STAFFEL, "brief pakt nog de kale staffel"
    assert _bedrag(context["totaal_bik"]) == scherm["total_bik"]
    assert _bedrag(context["totaal_openstaand"]) == scherm["total_outstanding"]


@pytest.mark.asyncio
async def test_percentage_afspraak_staat_in_de_brief(
    db: AsyncSession, test_tenant: Tenant, zaak: Case
):
    """Kosten-afspraak als PERCENTAGE (15%) → brief rekent het percentage."""
    zaak.bik_override_percentage = Decimal("15.00")
    await db.commit()

    context, scherm = await _brief_en_scherm(db, test_tenant.id, zaak)

    verwacht = (HOOFDSOM * Decimal("0.15")).quantize(Decimal("0.01"))
    assert _bedrag(context["bik_bedrag"]) == verwacht
    assert _bedrag(context["bik_bedrag"]) != STAFFEL
    assert _bedrag(context["totaal_verschuldigd"]) == scherm["grand_total"]


@pytest.mark.asyncio
async def test_afspraak_geen_kosten_staat_in_de_brief(
    db: AsyncSession, test_tenant: Tenant, zaak: Case
):
    """Afspraak € 0,00 ('geen kosten rekenen') mag nooit stil staffel worden."""
    zaak.bik_override = Decimal("0.00")
    await db.commit()

    context, _ = await _brief_en_scherm(db, test_tenant.id, zaak)

    assert _bedrag(context["bik_bedrag"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_zonder_afspraak_blijft_de_wettelijke_staffel(
    db: AsyncSession, test_tenant: Tenant, zaak: Case
):
    """Geen afspraak → staffel (art. 6:96 BW). De fix mag dit niet omgooien."""
    context, scherm = await _brief_en_scherm(db, test_tenant.id, zaak)

    assert _bedrag(context["bik_bedrag"]) == STAFFEL
    assert _bedrag(context["totaal_bik"]) == scherm["total_bik"]


@pytest.mark.asyncio
async def test_rente_stopt_op_de_bevriesdatum_ook_in_de_brief(
    db: AsyncSession, test_tenant: Tenant, zaak: Case
):
    """Afgewikkeld dossier: de brief mag geen rente t/m vandaag doorrekenen.

    Prod-geval IN100612: tabblad € 58,41 (t/m stopdatum), brief € 202,79 (t/m
    vandaag) — dezelfde 2%/mnd, alleen een andere einddatum.
    """
    zaak.interest_freeze_date = date.today() - timedelta(days=90)
    await db.commit()

    context, scherm = await _brief_en_scherm(db, test_tenant.id, zaak)

    assert _bedrag(context["totaal_rente"]) == scherm["total_interest"]

    # Bewijs dat de bevriezing écht scheelt: zonder stopdatum is de rente hoger.
    zaak.interest_freeze_date = None
    await db.commit()
    context_los, _ = await _brief_en_scherm(db, test_tenant.id, zaak)
    assert _bedrag(context_los["totaal_rente"]) > _bedrag(context["totaal_rente"])
