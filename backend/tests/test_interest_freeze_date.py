"""S207: rentedatum / bevriezing op de zaak.

De rente moet stoppen op de bevroren datum (afwikkelmoment of handmatig gezet),
zodat een afgewikkelde zaak niet eeuwig doorrent (IN100350). Verifieert:
- get_financial_summary rekent rente tot de bevroren datum i.p.v. vandaag
- volledige betaling zet de bevriesdatum automatisch op de laatste betaaldatum
- heropenen wist de automatische bevriezing weer
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.cases.models import Case
from app.collections.models import Claim, InterestRate
from app.collections.schemas import ClaimCreate, PaymentCreate
from app.collections.service import (
    create_claim,
    create_payment,
    get_financial_summary,
)
from app.relations.models import Contact


async def _seed_rates(db: AsyncSession) -> None:
    db.add(
        InterestRate(
            id=uuid.uuid4(),
            rate_type="commercial",
            rate=Decimal("12.00"),
            effective_from=date(2024, 1, 1),
        )
    )
    await db.flush()


@pytest_asyncio.fixture
async def freeze_case(
    db: AsyncSession, test_tenant: Tenant, test_company: Contact
) -> Case:
    await _seed_rates(db)
    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number=f"{date.today().year}-09001",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        interest_type="commercial",
        contractual_compound=True,
        client_id=test_company.id,
        date_opened=date(2024, 1, 1),
    )
    db.add(case)
    await db.flush()
    db.add(
        Claim(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_id=case.id,
            description="Factuur 2024-001",
            principal_amount=Decimal("10000.00"),
            default_date=date(2024, 1, 1),
        )
    )
    await db.commit()
    await db.refresh(case)
    return case


@pytest.mark.asyncio
async def test_freeze_date_stopt_rente(
    db: AsyncSession, test_tenant: Tenant, freeze_case: Case
):
    # Zonder bevriezing: rente loopt tot vandaag (jaren rente op €10.000).
    live = await get_financial_summary(
        db, test_tenant.id, freeze_case.id,
        freeze_case.interest_type, None, True,
    )
    # Met bevriezing op een vroege datum: veel minder rente.
    freeze_case.interest_freeze_date = date(2024, 7, 1)
    await db.flush()
    frozen = await get_financial_summary(
        db, test_tenant.id, freeze_case.id,
        freeze_case.interest_type, None, True,
    )
    assert frozen["total_interest"] < live["total_interest"]
    assert frozen["calculation_date"] == date(2024, 7, 1)


@pytest.mark.asyncio
async def test_expliciete_calc_date_wint_van_freeze(
    db: AsyncSession, test_tenant: Tenant, freeze_case: Case
):
    freeze_case.interest_freeze_date = date(2024, 7, 1)
    await db.flush()
    # Expliciete peildatum moet de bevriezing overrulen.
    explicit = await get_financial_summary(
        db, test_tenant.id, freeze_case.id,
        freeze_case.interest_type, None, True,
        calc_date=date(2025, 1, 1),
    )
    assert explicit["calculation_date"] == date(2025, 1, 1)


@pytest.mark.asyncio
async def test_volledige_betaling_bevriest_op_laatste_betaaldatum(
    db: AsyncSession, test_tenant: Tenant, freeze_case: Case
):
    # Bereken het volledige openstaande bedrag en betaal dat in één keer.
    summary = await get_financial_summary(
        db, test_tenant.id, freeze_case.id,
        freeze_case.interest_type, None, True,
    )
    pay_date = date.today()
    await create_payment(
        db, test_tenant.id, freeze_case.id,
        PaymentCreate(amount=summary["total_outstanding"], payment_date=pay_date),
        interest_type=freeze_case.interest_type,
        contractual_compound=True,
        cap_to_outstanding=True,
    )
    await db.refresh(freeze_case)
    assert freeze_case.status == "betaald"
    # Bevroren op het afwikkelmoment (laatste betaaldatum), niet op een latere
    # dag → een afgewikkelde zaak rent niet door met spookrente.
    assert freeze_case.interest_freeze_date == pay_date


@pytest.mark.asyncio
async def test_nieuwe_vordering_heropent_gesloten_zaak(
    db: AsyncSession, test_tenant: Tenant, freeze_case: Case
):
    # Zet de zaak op afgesloten met een bevroren rentedatum.
    freeze_case.status = "afgesloten"
    freeze_case.date_closed = date(2025, 1, 1)
    freeze_case.interest_freeze_date = date(2025, 1, 1)
    await db.flush()

    # Nieuwe factuur = nieuwe schuld → zaak weer open, bevriezing weg.
    await create_claim(
        db, test_tenant.id, freeze_case.id,
        ClaimCreate(
            description="Nieuwe factuur na een jaar",
            principal_amount=Decimal("500.00"),
            default_date=date(2026, 1, 1),
        ),
    )
    await db.refresh(freeze_case)
    assert freeze_case.status == "in_behandeling"
    assert freeze_case.date_closed is None
    assert freeze_case.interest_freeze_date is None
