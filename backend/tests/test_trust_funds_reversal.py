"""Tests for trust funds reversal (storno) flow — H15 + H16.

Voda/NOvA: trust bookings are immutable; corrections happen via reversal
entries (tegenboeking) with their own audit trail. Reversals of debits
(disbursement/offset) require the same two-approval flow; reversals of
deposits apply immediately but may never make the balance negative.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.relations.models import Contact
from app.trust_funds.models import TrustTransaction

# ── Helpers ──────────────────────────────────────────────────────────────────


@pytest.fixture
def case_payload(test_company: Contact) -> dict:
    return {
        "case_type": "advies",
        "description": "Storno test zaak",
        "client_id": str(test_company.id),
        "date_opened": "2026-02-20",
    }


async def _create_case(client: AsyncClient, headers: dict, payload: dict) -> str:
    r = await client.post("/api/cases", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _create_deposit(
    client: AsyncClient, headers: dict, case_id: str, amount: str
) -> dict:
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json={
            "transaction_type": "deposit",
            "amount": amount,
            "description": f"Storting {amount}",
            "payment_method": "bank",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _create_approved_disbursement(
    client: AsyncClient, headers: dict, case_id: str, amount: str
) -> dict:
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json={
            "transaction_type": "disbursement",
            "amount": amount,
            "description": f"Uitbetaling {amount}",
            "beneficiary_name": "J. Jansen",
            "beneficiary_iban": "NL91ABNA0417164300",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    tx = r.json()
    # Self-approval enabled in test env: same user fills both slots
    for _ in range(2):
        r = await client.post(
            f"/api/trust-funds/transactions/{tx['id']}/approve", headers=headers
        )
        assert r.status_code == 200, r.text
    return r.json()


async def _balance(client: AsyncClient, headers: dict, case_id: str) -> dict:
    r = await client.get(f"/api/trust-funds/cases/{case_id}/balance", headers=headers)
    assert r.status_code == 200
    return r.json()


async def _reverse(
    client: AsyncClient, headers: dict, tx_id: str, reason: str = "Foutieve boeking"
):
    return await client.post(
        f"/api/trust-funds/transactions/{tx_id}/reverse",
        json={"reason": reason},
        headers=headers,
    )


# ── Deposit reversal ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reverse_deposit_restores_balance(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    case_payload: dict,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    deposit = await _create_deposit(client, auth_headers, case_id, "5000.00")

    r = await _reverse(client, auth_headers, deposit["id"], "Verkeerd dossier")
    assert r.status_code == 200, r.text
    reversal = r.json()

    assert reversal["transaction_type"] == "reversal"
    assert Decimal(reversal["amount"]) == Decimal("5000.00")
    assert reversal["status"] == "approved"  # deposit-storno: direct
    assert reversal["reverses_id"] == deposit["id"]
    assert "Verkeerd dossier" in reversal["description"]

    # Origineel wijst naar de storno
    orig = (
        await db.execute(
            select(TrustTransaction).where(
                TrustTransaction.id == uuid.UUID(deposit["id"])
            )
        )
    ).scalar_one()
    assert orig.reversed_by_id == uuid.UUID(reversal["id"])

    balance = await _balance(client, auth_headers, case_id)
    assert Decimal(balance["total_balance"]) == Decimal("0.00")
    assert Decimal(balance["available"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_reverse_deposit_refused_when_money_already_paid_out(
    client: AsyncClient,
    auth_headers: dict,
    case_payload: dict,
):
    """Saldo mag nooit negatief: storting storneren kan niet als het geld
    al (deels) is uitbetaald."""
    case_id = await _create_case(client, auth_headers, case_payload)
    deposit = await _create_deposit(client, auth_headers, case_id, "5000.00")
    await _create_approved_disbursement(client, auth_headers, case_id, "3000.00")

    r = await _reverse(client, auth_headers, deposit["id"])
    assert r.status_code == 400
    assert "saldo" in r.json()["detail"].lower()


# ── Disbursement reversal (vier-ogen) ────────────────────────────────────────


@pytest.mark.asyncio
async def test_reverse_disbursement_requires_approval_then_restores_balance(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    case_payload: dict,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    await _create_deposit(client, auth_headers, case_id, "5000.00")
    disb = await _create_approved_disbursement(client, auth_headers, case_id, "2000.00")

    balance = await _balance(client, auth_headers, case_id)
    assert Decimal(balance["total_balance"]) == Decimal("3000.00")

    r = await _reverse(client, auth_headers, disb["id"], "Geld retour van bank")
    assert r.status_code == 200, r.text
    reversal = r.json()
    assert reversal["status"] == "pending_approval"  # vier-ogen op debit-storno

    # Nog geen effect vóór goedkeuring
    balance = await _balance(client, auth_headers, case_id)
    assert Decimal(balance["total_balance"]) == Decimal("3000.00")

    for _ in range(2):
        r = await client.post(
            f"/api/trust-funds/transactions/{reversal['id']}/approve",
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text

    # Na volledige goedkeuring: origineel gestorneerd, saldo hersteld
    orig = (
        await db.execute(
            select(TrustTransaction).where(TrustTransaction.id == uuid.UUID(disb["id"]))
        )
    ).scalar_one()
    assert orig.reversed_by_id == uuid.UUID(reversal["id"])

    balance = await _balance(client, auth_headers, case_id)
    assert Decimal(balance["total_balance"]) == Decimal("5000.00")


# ── Guards ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reverse_guards(
    client: AsyncClient,
    auth_headers: dict,
    case_payload: dict,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    deposit = await _create_deposit(client, auth_headers, case_id, "1000.00")

    # Eerste storno OK
    r = await _reverse(client, auth_headers, deposit["id"])
    assert r.status_code == 200
    reversal_id = r.json()["id"]

    # Nogmaals storneren → 400
    r = await _reverse(client, auth_headers, deposit["id"])
    assert r.status_code == 400

    # Een storno zelf storneren → 400
    r = await _reverse(client, auth_headers, reversal_id)
    assert r.status_code == 400

    # Pending transactie storneren → 400 (gebruik reject daarvoor)
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json={
            "transaction_type": "deposit",
            "amount": "500.00",
            "description": "Nieuwe storting",
        },
        headers=auth_headers,
    )
    new_deposit_id = r.json()["id"]
    r2 = await client.post(
        f"/api/trust-funds/cases/{case_id}/transactions",
        json={
            "transaction_type": "disbursement",
            "amount": "100.00",
            "description": "Pending uitbetaling",
            "beneficiary_name": "X",
            "beneficiary_iban": "NL91ABNA0417164300",
        },
        headers=auth_headers,
    )
    assert r2.status_code == 201
    pending_id = r2.json()["id"]
    r = await _reverse(client, auth_headers, pending_id)
    assert r.status_code == 400
    assert new_deposit_id  # storting blijft bruikbaar

    # Reden verplicht
    r = await client.post(
        f"/api/trust-funds/transactions/{pending_id}/reverse",
        json={"reason": ""},
        headers=auth_headers,
    )
    assert r.status_code in (400, 422)


# ── Mutatie-CSV toont storno's ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mutaties_csv_includes_reversal(
    client: AsyncClient,
    auth_headers: dict,
    case_payload: dict,
):
    case_id = await _create_case(client, auth_headers, case_payload)
    deposit = await _create_deposit(client, auth_headers, case_id, "750.00")
    r = await _reverse(client, auth_headers, deposit["id"])
    assert r.status_code == 200

    r = await client.get("/api/trust-funds/reports/mutaties.csv", headers=auth_headers)
    assert r.status_code == 200
    body = r.text
    assert "reversal" in body
    assert "ja" in body  # origineel gemarkeerd als reversed


# ── Offset reversal heropent factuur ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_reverse_offset_reopens_invoice(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_company: Contact,
    case_payload: dict,
):
    """Storno van een verrekening verwijdert de factuurbetaling en zet de
    factuurstatus terug, naast het herstellen van het derdengeldensaldo."""
    from app.invoices.models import Invoice as InvoiceModel
    from app.invoices.models import InvoicePayment

    case_id = await _create_case(client, auth_headers, case_payload)
    await _create_deposit(client, auth_headers, case_id, "2000.00")

    # Verzonden factuur van 1210 incl. BTW (1000 + 21%)
    r = await client.post(
        "/api/invoices",
        json={
            "contact_id": str(test_company.id),
            "invoice_date": "2026-02-01",
            "due_date": "2026-03-01",
            "btw_percentage": "21.00",
            "lines": [
                {"description": "Honorarium", "quantity": "10", "unit_price": "100.00"}
            ],
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    invoice_id = r.json()["id"]
    r = await client.post(f"/api/invoices/{invoice_id}/approve", headers=auth_headers)
    assert r.status_code == 200
    res = await db.execute(
        select(InvoiceModel).where(InvoiceModel.id == uuid.UUID(invoice_id))
    )
    invoice_obj = res.scalar_one()
    invoice_obj.status = "sent"
    await db.commit()

    # Verrekening aanmaken + volledig goedkeuren (self-approval)
    r = await client.post(
        f"/api/trust-funds/cases/{case_id}/offsets",
        json={
            "amount": "1210.00",
            "description": "Verrekening met factuur",
            "target_invoice_id": invoice_id,
            "consent_received_at": "2026-04-08",
            "consent_method": "email",
            "consent_note": "Bevestigd per email door cliënt",
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    offset_id = r.json()["id"]
    for _ in range(2):
        r = await client.post(
            f"/api/trust-funds/transactions/{offset_id}/approve", headers=auth_headers
        )
        assert r.status_code == 200, r.text

    # Factuur is nu betaald, saldo verlaagd
    r = await client.get(f"/api/invoices/{invoice_id}", headers=auth_headers)
    assert r.json()["status"] == "paid"
    balance = await _balance(client, auth_headers, case_id)
    assert Decimal(balance["total_balance"]) == Decimal("790.00")

    # Storno van de verrekening + vier-ogen goedkeuring
    r = await _reverse(client, auth_headers, offset_id, "Cliënt betwist declaratie")
    assert r.status_code == 200, r.text
    reversal_id = r.json()["id"]
    assert r.json()["status"] == "pending_approval"
    for _ in range(2):
        r = await client.post(
            f"/api/trust-funds/transactions/{reversal_id}/approve",
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text

    # Factuurbetaling weg, status terug naar sent, saldo hersteld
    payments = (
        (
            await db.execute(
                select(InvoicePayment).where(
                    InvoicePayment.invoice_id == uuid.UUID(invoice_id)
                )
            )
        )
        .scalars()
        .all()
    )
    assert payments == []
    r = await client.get(f"/api/invoices/{invoice_id}", headers=auth_headers)
    assert r.json()["status"] == "sent"
    balance = await _balance(client, auth_headers, case_id)
    assert Decimal(balance["total_balance"]) == Decimal("2000.00")


# ── Undo executed match (H16) ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_undo_executed_match_restores_everything(
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    test_company: Contact,
):
    """Een uitgevoerde bank-match terugdraaien: betaling soft-deleted,
    trust-storting gestorneerd, transactie weer koppelbaar."""
    from app.ai_agent.payment_matching_models import (
        BankStatementImport,
        BankTransaction,
        ImportStatus,
        MatchMethod,
        MatchStatus,
        PaymentMatch,
    )
    from app.ai_agent.payment_matching_service import execute_match, undo_match
    from app.cases.models import Case
    from app.collections.models import Claim, InterestRate, Payment

    # Seed rates + incasso case
    for rate_type, rate_val in [("statutory", "6.00"), ("commercial", "11.50")]:
        db.add(
            InterestRate(
                id=uuid.uuid4(),
                rate_type=rate_type,
                effective_from=date(2024, 1, 1),
                rate=Decimal(rate_val),
                source="Test fixture",
            )
        )
    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-00077",
        description="Undo test",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        is_active=True,
        client_id=test_company.id,
        assigned_to_id=test_user.id,
        date_opened=date.today() - timedelta(days=30),
        total_principal=Decimal("5000.00"),
        total_paid=Decimal("0.00"),
    )
    db.add(case)
    db.add(
        Claim(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_id=case.id,
            description="Factuur X",
            principal_amount=Decimal("5000.00"),
            default_date=date.today() - timedelta(days=60),
            invoice_number="2026-077",
        )
    )
    imp = BankStatementImport(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        filename="t.csv",
        bank="rabobank",
        status=ImportStatus.COMPLETED,
        imported_by_id=test_user.id,
    )
    db.add(imp)
    await db.flush()
    txn = BankTransaction(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        import_id=imp.id,
        transaction_date=date(2026, 3, 1),
        amount=Decimal("1000.00"),
        counterparty_name="Debiteur BV",
        is_matched=True,
    )
    db.add(txn)
    await db.flush()
    match = PaymentMatch(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        transaction_id=txn.id,
        case_id=case.id,
        match_method=MatchMethod.MANUAL,
        confidence=100,
        status=MatchStatus.APPROVED,
    )
    db.add(match)
    await db.flush()

    executed = await execute_match(db, test_tenant.id, match.id, test_user.id)
    assert executed.status == MatchStatus.EXECUTED
    await db.flush()

    undone = await undo_match(
        db, test_tenant.id, match.id, test_user.id, reason="Verkeerd dossier"
    )
    assert undone is not None
    assert undone.status == MatchStatus.REJECTED

    # Betaling soft-deleted
    payment = (
        await db.execute(select(Payment).where(Payment.id == executed.payment_id))
    ).scalar_one()
    assert payment.is_active is False

    # Trust-storting gestorneerd
    trust_orig = (
        await db.execute(
            select(TrustTransaction).where(
                TrustTransaction.id == executed.trust_transaction_id
            )
        )
    ).scalar_one()
    assert trust_orig.reversed_by_id is not None

    # Transactie weer koppelbaar
    await db.refresh(txn)
    assert txn.is_matched is False
