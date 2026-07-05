"""Tests voor de dossier-afwikkelflow (FIN-2): settlement-endpoint, afsluit-guard, talm-job."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.incasso.models import IncassoPipelineStep
from app.incasso.service import move_case_to_step
from app.notifications.models import Notification
from app.relations.models import Contact
from app.shared.exceptions import BadRequestError
from app.trust_funds.service import process_stale_trust_balances


@pytest.fixture
def case_payload(test_company: Contact) -> dict:
    return {
        "case_type": "advies",
        "description": "Afwikkel test zaak",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-20",
    }


async def _create_case(client: AsyncClient, auth_headers: dict, payload: dict) -> str:
    r = await client.post("/api/cases", json=payload, headers=auth_headers)
    assert r.status_code == 201
    return r.json()["id"]


async def _deposit(
    client: AsyncClient, auth_headers: dict, case_id: str, amount: str, when: str | None = None
) -> None:
    body = {"transaction_type": "deposit", "amount": amount, "description": "Storting debiteur"}
    if when:
        body["transaction_date"] = when
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions", json=body, headers=auth_headers
    )
    assert r.status_code == 201


# ── Settlement endpoint ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_settlement_reports_balance_and_block(
    client: AsyncClient, auth_headers: dict, test_company: Contact, case_payload: dict
):
    """Geld op de stichting → saldo, voorgesteld uit te betalen bedrag én afsluit-blokkade."""
    case_id = await _create_case(client, auth_headers, case_payload)
    await _deposit(client, auth_headers, case_id, "1000.00")

    r = await client.get(f"/api/cases/{case_id}/settlement", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert Decimal(data["total_balance"]) == Decimal("1000.00")
    assert Decimal(data["available"]) == Decimal("1000.00")
    assert Decimal(data["suggested_payout"]) == Decimal("1000.00")
    assert data["unsettled_reason"] is not None  # saldo > 0 → afsluiten geblokkeerd
    assert data["settlement_route"] is None


@pytest.mark.asyncio
async def test_settlement_route_set_and_clear(
    client: AsyncClient, auth_headers: dict, test_company: Contact, case_payload: dict
):
    case_id = await _create_case(client, auth_headers, case_payload)

    r = await client.patch(
        f"/api/cases/{case_id}/settlement", json={"route": "verrekenen"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["settlement_route"] == "verrekenen"

    r = await client.patch(
        f"/api/cases/{case_id}/settlement", json={"route": "onzin"}, headers=auth_headers
    )
    assert r.status_code == 422  # ongeldige route geweigerd

    r = await client.patch(
        f"/api/cases/{case_id}/settlement", json={"route": None}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["settlement_route"] is None


# ── Afsluit-guard op de pipeline-stap ────────────────────────────────────────


@pytest.mark.asyncio
async def test_close_step_blocked_while_trust_balance(
    db: AsyncSession,
    client: AsyncClient,
    auth_headers: dict,
    test_tenant: Tenant,
    test_user: User,
    test_company: Contact,
    case_payload: dict,
):
    """'Afgesloten' (requires_settled) blokkeert bij saldo; 'Betaald' blokkeert bewust niet."""
    case_id = await _create_case(client, auth_headers, case_payload)
    await _deposit(client, auth_headers, case_id, "500.00")

    case = (
        await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
    ).scalar_one()

    afgesloten = IncassoPipelineStep(
        tenant_id=test_tenant.id, name="Afgesloten", sort_order=99,
        step_category="afsluiting", is_terminal=True, requires_settled=True,
    )
    betaald = IncassoPipelineStep(
        tenant_id=test_tenant.id, name="Betaald", sort_order=98,
        step_category="afsluiting", is_terminal=True, requires_settled=False,
    )
    db.add_all([afgesloten, betaald])
    await db.flush()

    with pytest.raises(BadRequestError):
        await move_case_to_step(db, test_tenant.id, case, afgesloten, user_id=test_user.id)

    # 'Betaald' mag wél: het geld staat daar terecht, wachtend op uitbetaling.
    hist = await move_case_to_step(db, test_tenant.id, case, betaald, user_id=test_user.id)
    assert hist.step_id == betaald.id


# ── Talm-signaal (stilstaand saldo) ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_stale_trust_notifies_and_dedups(
    db: AsyncSession,
    client: AsyncClient,
    auth_headers: dict,
    test_tenant: Tenant,
    test_company: Contact,
    case_payload: dict,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    old = (date.today() - timedelta(days=10)).isoformat()
    await _deposit(client, auth_headers, case_id, "800.00", when=old)

    n1 = await process_stale_trust_balances(db, test_tenant.id)
    assert n1 == 1  # één actieve gebruiker → één melding

    notes = (
        await db.execute(select(Notification).where(Notification.type == "trust_stale"))
    ).scalars().all()
    assert len(notes) == 1
    assert notes[0].case_id == uuid.UUID(case_id)

    # Binnen het dedup-venster levert opnieuw draaien niks nieuws op.
    n2 = await process_stale_trust_balances(db, test_tenant.id)
    assert n2 == 0


@pytest.mark.asyncio
async def test_recent_trust_not_flagged(
    db: AsyncSession,
    client: AsyncClient,
    auth_headers: dict,
    test_tenant: Tenant,
    test_company: Contact,
    case_payload: dict,
):
    """Een vers saldo (vandaag geboekt) is niet 'stil' en wordt niet gemeld."""
    case_id = await _create_case(client, auth_headers, case_payload)
    await _deposit(client, auth_headers, case_id, "800.00")

    n = await process_stale_trust_balances(db, test_tenant.id)
    assert n == 0
