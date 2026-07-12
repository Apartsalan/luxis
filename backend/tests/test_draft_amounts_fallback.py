"""S203 #3 — AI-conceptbrief mag niet stil met €0 rente/BIK de review in.

Faalt de bedragenberekening (get_financial_summary), dan valt de draft-context
terug op hoofdsom-only. Die terugval moet zichtbaar gemarkeerd worden zodat
Lisanne niet een nette brief met te lage bedragen verstuurt.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.collections.models import Claim
from app.incasso import automation_service
from app.relations.models import Contact


@pytest_asyncio.fixture
async def case_with_claim(db: AsyncSession, test_tenant: Tenant, test_user: User) -> Case:
    client = Contact(
        id=uuid.uuid4(), tenant_id=test_tenant.id, contact_type="company",
        name="Cliënt BV", email="info@client.nl",
    )
    debtor = Contact(
        id=uuid.uuid4(), tenant_id=test_tenant.id, contact_type="company",
        name="Debiteur BV", email="info@debiteur.nl",
    )
    db.add_all([client, debtor])
    await db.flush()
    case = Case(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_number="2026-98001",
        case_type="incasso", debtor_type="b2b", status="nieuw",
        interest_type="statutory", contractual_compound=True,
        client_id=client.id, opposing_party_id=debtor.id, date_opened=date.today(),
    )
    db.add(case)
    await db.flush()
    db.add(Claim(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        description="Onbetaalde factuur", principal_amount=Decimal("5000.00"),
        invoice_number="2026-001", invoice_date=date(2026, 1, 15),
        default_date=date(2026, 2, 15),
    ))
    await db.commit()
    await db.refresh(case)
    return case


@pytest.mark.asyncio
async def test_amounts_fallback_flag_on_calc_error(
    db: AsyncSession, test_tenant: Tenant, case_with_claim: Case, monkeypatch
):
    async def _boom(*args, **kwargs):
        raise ValueError("geen rente-tarief geseed")

    monkeypatch.setattr("app.collections.service.get_financial_summary", _boom)

    ctx = await automation_service.gather_case_context(
        db, test_tenant.id, case_with_claim.id
    )
    assert ctx["_amounts_fallback"] is True
    # Hoofdsom blijft, maar rente/BIK/BTW zijn 0 in de terugval.
    assert ctx["amounts"]["hoofdsom"] == Decimal("5000.00")
    assert ctx["amounts"]["rente"] == Decimal("0.00")
    assert ctx["amounts"]["incassokosten"] == Decimal("0.00")


@pytest.mark.asyncio
async def test_no_fallback_flag_when_calc_ok(
    db: AsyncSession, test_tenant: Tenant, case_with_claim: Case, monkeypatch
):
    async def _ok(*args, **kwargs):
        return {
            "total_principal": Decimal("5000.00"),
            "total_interest": Decimal("120.00"),
            "bik_amount": Decimal("625.00"),
            "bik_btw": Decimal("0.00"),
            "total_paid": Decimal("0.00"),
            "grand_total": Decimal("5745.00"),
            "total_outstanding": Decimal("5745.00"),
        }

    monkeypatch.setattr("app.collections.service.get_financial_summary", _ok)

    ctx = await automation_service.gather_case_context(
        db, test_tenant.id, case_with_claim.id
    )
    assert ctx["_amounts_fallback"] is False
    assert ctx["amounts"]["rente"] == Decimal("120.00")
