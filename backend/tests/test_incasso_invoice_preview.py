"""Tests for incasso invoice preview — BIK modes + provisie minimum fee.

Covers DF117-04 (BIK percentage-optie) and DF117-09 (minimum_fee applied and
visible) from the Lisanne demo on 2026-04-07.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.cases.models import Case
from app.collections.models import Claim, InterestRate
from app.relations.models import Contact


async def _seed_rates(db: AsyncSession) -> None:
    """Seed a minimum set of statutory interest rates so get_financial_summary works."""
    rate = InterestRate(
        id=uuid.uuid4(),
        rate_type="statutory",
        rate=Decimal("4.00"),
        effective_from=date(2024, 1, 1),
    )
    db.add(rate)
    await db.flush()


@pytest_asyncio.fixture
async def incasso_case(
    db: AsyncSession, test_tenant: Tenant, test_company: Contact
) -> Case:
    """Create an incasso case with a €10,000 claim for BIK testing."""
    await _seed_rates(db)

    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number=f"{date.today().year}-00001",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        interest_type="statutory",
        contractual_compound=True,
        client_id=test_company.id,
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()

    claim = Claim(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_id=case.id,
        description="Factuur 2026-001",
        principal_amount=Decimal("10000.00"),
        default_date=date(2026, 1, 1),
    )
    db.add(claim)
    await db.commit()
    await db.refresh(case)
    return case


# ─── DF117-04: BIK percentage mode ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_bik_default_wik_staffel(
    client: AsyncClient, auth_headers: dict, incasso_case: Case
):
    """Without any override, BIK uses the WIK-staffel. For €10,000 principal:
    15% over €2500 = 375, 10% over 2500 = 250, 5% over 5000 = 250 → €875.
    """
    resp = await client.get(
        f"/api/cases/{incasso_case.id}/incasso-invoice-preview", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["bik"]["is_override"] is False
    assert Decimal(str(data["bik"]["amount"])) == Decimal("875.00")
    assert "WIK-staffel" in data["bik"]["source"]


@pytest.mark.asyncio
async def test_bik_fixed_override_beats_wik(
    client: AsyncClient, auth_headers: dict, incasso_case: Case, db: AsyncSession
):
    """With bik_override set, use the fixed amount."""
    incasso_case.bik_override = Decimal("500.00")
    await db.commit()

    resp = await client.get(
        f"/api/cases/{incasso_case.id}/incasso-invoice-preview", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["bik"]["is_override"] is True
    assert Decimal(str(data["bik"]["amount"])) == Decimal("500.00")
    assert data["bik"]["source"] == "Handmatig ingesteld"


@pytest.mark.asyncio
async def test_bik_percentage_beats_fixed_override(
    client: AsyncClient, auth_headers: dict, incasso_case: Case, db: AsyncSession
):
    """DF117-04: percentage takes precedence over fixed override.
    10% of €10,000 principal = €1000.
    """
    incasso_case.bik_override = Decimal("500.00")  # should be ignored
    incasso_case.bik_override_percentage = Decimal("10.00")
    await db.commit()

    resp = await client.get(
        f"/api/cases/{incasso_case.id}/incasso-invoice-preview", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["bik"]["is_override"] is True
    assert Decimal(str(data["bik"]["amount"])) == Decimal("1000.00")
    assert "10" in data["bik"]["source"]  # percentage mentioned
    assert "hoofdsom" in data["bik"]["source"].lower()


@pytest.mark.asyncio
async def test_bik_percentage_only(
    client: AsyncClient, auth_headers: dict, incasso_case: Case, db: AsyncSession
):
    """DF117-04: percentage alone (no fixed override) also works.
    12.5% of €10,000 = €1250.
    """
    incasso_case.bik_override_percentage = Decimal("12.50")
    await db.commit()

    resp = await client.get(
        f"/api/cases/{incasso_case.id}/incasso-invoice-preview", headers=auth_headers
    )
    data = resp.json()
    assert Decimal(str(data["bik"]["amount"])) == Decimal("1250.00")


# ─── DF117-09: minimum_fee applied to provisie amounts ────────────────────


@pytest.mark.asyncio
async def test_provisie_minimum_fee_applied_when_raw_is_lower(
    client: AsyncClient, auth_headers: dict, incasso_case: Case, db: AsyncSession
):
    """Provisie 10% over a claim of €10,000 → €1000 raw. With minimum_fee of
    €1500, the final amount must be €1500 (minimum forces it up) and
    is_minimum_applied must be True so the UI can show it to Lisanne."""
    incasso_case.provisie_percentage = Decimal("10.00")
    incasso_case.minimum_fee = Decimal("1500.00")
    await db.commit()

    resp = await client.get(
        f"/api/cases/{incasso_case.id}/incasso-invoice-preview", headers=auth_headers
    )
    data = resp.json()
    over_claim = data["provisie"]["over_claim"]
    assert Decimal(str(over_claim["raw_amount"])) == Decimal("1000.00")
    assert Decimal(str(over_claim["amount"])) == Decimal("1500.00")
    assert over_claim["is_minimum_applied"] is True


@pytest.mark.asyncio
async def test_provisie_minimum_fee_not_applied_when_raw_is_higher(
    client: AsyncClient, auth_headers: dict, incasso_case: Case, db: AsyncSession
):
    """When the raw provisie beats the minimum, the minimum should NOT apply.
    15% of €10,000 = €1500 > minimum_fee of €1000 → use €1500, flag False.
    """
    incasso_case.provisie_percentage = Decimal("15.00")
    incasso_case.minimum_fee = Decimal("1000.00")
    await db.commit()

    resp = await client.get(
        f"/api/cases/{incasso_case.id}/incasso-invoice-preview", headers=auth_headers
    )
    data = resp.json()
    over_claim = data["provisie"]["over_claim"]
    assert Decimal(str(over_claim["raw_amount"])) == Decimal("1500.00")
    assert Decimal(str(over_claim["amount"])) == Decimal("1500.00")
    assert over_claim["is_minimum_applied"] is False


@pytest.mark.asyncio
async def test_provisie_fixed_costs_added_before_minimum(
    client: AsyncClient, auth_headers: dict, incasso_case: Case, db: AsyncSession
):
    """fixed_case_costs should be added to raw before comparing to minimum_fee:
    raw (€1000) + fixed (€200) = €1200, minimum €1500 → final €1500.
    """
    incasso_case.provisie_percentage = Decimal("10.00")
    incasso_case.fixed_case_costs = Decimal("200.00")
    incasso_case.minimum_fee = Decimal("1500.00")
    await db.commit()

    resp = await client.get(
        f"/api/cases/{incasso_case.id}/incasso-invoice-preview", headers=auth_headers
    )
    data = resp.json()
    over_claim = data["provisie"]["over_claim"]
    assert Decimal(str(over_claim["amount"])) == Decimal("1500.00")
    assert over_claim["is_minimum_applied"] is True


@pytest.mark.asyncio
async def test_provisie_fixed_costs_added_without_minimum(
    client: AsyncClient, auth_headers: dict, incasso_case: Case, db: AsyncSession
):
    """fixed_costs added to raw when raw+fixed beats minimum:
    raw (€1000) + fixed (€200) = €1200 > minimum €1000 → final €1200.
    """
    incasso_case.provisie_percentage = Decimal("10.00")
    incasso_case.fixed_case_costs = Decimal("200.00")
    incasso_case.minimum_fee = Decimal("1000.00")
    await db.commit()

    resp = await client.get(
        f"/api/cases/{incasso_case.id}/incasso-invoice-preview", headers=auth_headers
    )
    data = resp.json()
    over_claim = data["provisie"]["over_claim"]
    assert Decimal(str(over_claim["amount"])) == Decimal("1200.00")
    assert over_claim["is_minimum_applied"] is False
