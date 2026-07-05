"""Cases settlement service — leidt de afwikkelstaat van een dossier af (FIN-2).

Read-only samenstelling over het derdengelden-saldo, de facturen van het dossier
en de geboekte/lopende trust-transacties. Hier zit GEEN boekingslogica — elke
financiele actie houdt zijn eigen beveiligde flow (vier-ogen, consent). De enige
mutatie is het opslaan van de per-dossier routekeuze (een UI-hint).
"""

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.schemas import (
    CaseSettlementResponse,
    SettlementInvoice,
    SettlementTransaction,
)
from app.cases.service import get_case
from app.invoices.models import Invoice
from app.trust_funds.models import TrustTransaction
from app.trust_funds.service import get_balance, get_unsettled_reason


async def get_case_settlement(
    db: AsyncSession, tenant_id: uuid.UUID, case_id: uuid.UUID
) -> CaseSettlementResponse:
    """Bouw de volledige afwikkelstaat van een dossier (bestaan + tenant gevalideerd)."""
    case = await get_case(db, tenant_id, case_id)

    balance = await get_balance(db, tenant_id, case_id)
    unsettled_reason = await get_unsettled_reason(db, tenant_id, case_id)

    # Facturen van dit dossier — alleen echte declaraties (geen credit-nota's/geannuleerd).
    inv_result = await db.execute(
        select(Invoice)
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.case_id == case_id,
            Invoice.is_active.is_(True),
            Invoice.invoice_type != "credit_note",
            Invoice.status != "cancelled",
        )
        .order_by(Invoice.invoice_date.desc())
    )
    invoices: list[SettlementInvoice] = []
    for inv in inv_result.scalars().all():
        paid = sum((p.amount for p in inv.payments), Decimal("0.00"))
        invoices.append(
            SettlementInvoice(
                id=inv.id,
                invoice_number=inv.invoice_number,
                status=inv.status,
                total=inv.total,
                outstanding=inv.total - paid,
            )
        )

    # Geboekte/lopende verrekeningen + uitbetalingen (rejected en gestorneerde eruit).
    tx_result = await db.execute(
        select(TrustTransaction)
        .where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.case_id == case_id,
            TrustTransaction.transaction_type.in_(("offset_to_invoice", "disbursement")),
            TrustTransaction.status != "rejected",
            TrustTransaction.reversed_by_id.is_(None),
        )
        .order_by(TrustTransaction.transaction_date.desc())
    )
    offsets: list[SettlementTransaction] = []
    disbursements: list[SettlementTransaction] = []
    for tx in tx_result.scalars().all():
        item = SettlementTransaction(
            id=tx.id,
            transaction_type=tx.transaction_type,
            amount=tx.amount,
            status=tx.status,
            transaction_date=tx.transaction_date,
            beneficiary_name=tx.beneficiary_name,
        )
        if tx.transaction_type == "offset_to_invoice":
            offsets.append(item)
        else:
            disbursements.append(item)

    suggested = balance.available if balance.available > Decimal("0.00") else Decimal("0.00")

    return CaseSettlementResponse(
        case_id=case_id,
        settlement_route=case.settlement_route,
        total_balance=balance.total_balance,
        available=balance.available,
        pending_disbursements=balance.pending_disbursements,
        suggested_payout=suggested,
        unsettled_reason=unsettled_reason,
        invoices=invoices,
        offsets=offsets,
        disbursements=disbursements,
    )


async def set_settlement_route(
    db: AsyncSession, tenant_id: uuid.UUID, case_id: uuid.UUID, route: str | None
) -> CaseSettlementResponse:
    """Sla de routekeuze op (of wis met None) en geef de verse afwikkelstaat terug.

    ponytail: de route is enkel een UI-hint voor de checklist — de echte boekingen
    hebben hun eigen guards (vier-ogen, consent, saldo). Daarom vrij wijzigbaar,
    ook nadat er al iets geboekt is; dat kan nooit tot een verkeerde boeking leiden.
    """
    case = await get_case(db, tenant_id, case_id)
    case.settlement_route = route
    await db.flush()
    return await get_case_settlement(db, tenant_id, case_id)
