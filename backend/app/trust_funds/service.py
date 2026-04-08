"""Trust funds module service — Business logic for derdengelden transactions.

Implements Dutch Stichting Derdengelden rules (Voda art. 6.19–6.27):
- Deposits are auto-approved
- Disbursements and offsets require two-director approval (4-eyes)
- Balance may NEVER go negative
- Full audit trail via status + approval fields
- Offsets to own invoices require explicit per-transaction client consent
- Transactions are immutable; corrections happen via reversal entries

For single-user tenants (e.g. solo practitioner), the env flag
TRUST_FUNDS_ALLOW_SELF_APPROVAL=true permits one user to approve their own
transactions. This is logged in both approval slots so the audit trail still
shows two distinct approval steps.
"""

import os
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cases.service import get_case
from app.invoices.models import Invoice, InvoicePayment
from app.shared.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.trust_funds.models import TrustTransaction
from app.cases.models import Case
from app.relations.models import Contact
from app.trust_funds.schemas import (
    CONSENT_METHODS,
    TRANSACTION_TYPES,
    CaseTrustSummary,
    ClientTrustOverview,
    EligibleInvoice,
    TrustBalanceSummary,
    TrustOffsetCreate,
    TrustOverviewResponse,
    TrustOverviewTotals,
    TrustTransactionCreate,
)


def _self_approval_allowed() -> bool:
    """Whether a single user may approve their own trust transactions.

    Set by env flag TRUST_FUNDS_ALLOW_SELF_APPROVAL. Default: True for the
    Kesting Legal solo-practice context. Set to "false" once a second user is
    onboarded so the strict 4-eyes principle is restored.
    """
    return os.environ.get("TRUST_FUNDS_ALLOW_SELF_APPROVAL", "true").lower() == "true"

# ── Balance Calculation ──────────────────────────────────────────────────────


async def get_balance(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> TrustBalanceSummary:
    """Calculate the trust fund balance for a case.

    Both disbursements and offsets-to-invoice are debits against the balance.

    total_balance = sum(approved deposits) - sum(approved debits)
    pending_disbursements = sum(pending_approval debits)
    available = total_balance - pending_disbursements
    """
    debit_types = ("disbursement", "offset_to_invoice")

    # Sum approved deposits (excluding reversed)
    result = await db.execute(
        select(func.coalesce(func.sum(TrustTransaction.amount), Decimal("0.00"))).where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.case_id == case_id,
            TrustTransaction.transaction_type == "deposit",
            TrustTransaction.status == "approved",
            TrustTransaction.reversed_by_id.is_(None),
        )
    )
    total_deposits = result.scalar_one()

    # Sum approved debits (disbursements + offsets, excluding reversed)
    result = await db.execute(
        select(func.coalesce(func.sum(TrustTransaction.amount), Decimal("0.00"))).where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.case_id == case_id,
            TrustTransaction.transaction_type.in_(debit_types),
            TrustTransaction.status == "approved",
            TrustTransaction.reversed_by_id.is_(None),
        )
    )
    total_disbursements = result.scalar_one()

    # Sum pending debits (not yet approved but not rejected)
    result = await db.execute(
        select(func.coalesce(func.sum(TrustTransaction.amount), Decimal("0.00"))).where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.case_id == case_id,
            TrustTransaction.transaction_type.in_(debit_types),
            TrustTransaction.status == "pending_approval",
        )
    )
    pending_disbursements = result.scalar_one()

    total_balance = total_deposits - total_disbursements
    available = total_balance - pending_disbursements

    return TrustBalanceSummary(
        case_id=case_id,
        total_deposits=total_deposits,
        total_disbursements=total_disbursements,
        total_balance=total_balance,
        pending_disbursements=pending_disbursements,
        available=available,
    )


# ── Cross-client Overview ────────────────────────────────────────────────────


async def list_overview_by_client(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    only_nonzero: bool = True,
) -> TrustOverviewResponse:
    """Aggregate trust balances per client across all their cases.

    Uses the same filter logic as `get_balance()` (approved & non-reversed for
    balance math, pending for pending_disbursements). Single grouped query per
    aggregation, Python-side client grouping.
    """
    debit_types = ("disbursement", "offset_to_invoice")

    # Per-case approved deposit totals (non-reversed)
    deposits_result = await db.execute(
        select(
            TrustTransaction.case_id,
            func.coalesce(func.sum(TrustTransaction.amount), Decimal("0.00")),
        )
        .where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.transaction_type == "deposit",
            TrustTransaction.status == "approved",
            TrustTransaction.reversed_by_id.is_(None),
        )
        .group_by(TrustTransaction.case_id)
    )
    deposits_by_case: dict[uuid.UUID, Decimal] = dict(deposits_result.all())

    # Per-case approved debit totals (non-reversed)
    debits_result = await db.execute(
        select(
            TrustTransaction.case_id,
            func.coalesce(func.sum(TrustTransaction.amount), Decimal("0.00")),
        )
        .where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.transaction_type.in_(debit_types),
            TrustTransaction.status == "approved",
            TrustTransaction.reversed_by_id.is_(None),
        )
        .group_by(TrustTransaction.case_id)
    )
    debits_by_case: dict[uuid.UUID, Decimal] = dict(debits_result.all())

    # Per-case pending debit totals
    pending_result = await db.execute(
        select(
            TrustTransaction.case_id,
            func.coalesce(func.sum(TrustTransaction.amount), Decimal("0.00")),
        )
        .where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.transaction_type.in_(debit_types),
            TrustTransaction.status == "pending_approval",
        )
        .group_by(TrustTransaction.case_id)
    )
    pending_by_case: dict[uuid.UUID, Decimal] = dict(pending_result.all())

    # Per-case last transaction date (any status, non-reversed)
    last_result = await db.execute(
        select(
            TrustTransaction.case_id,
            func.max(TrustTransaction.transaction_date),
        )
        .where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.reversed_by_id.is_(None),
        )
        .group_by(TrustTransaction.case_id)
    )
    last_date_by_case: dict[uuid.UUID, date] = dict(last_result.all())

    # Tenant-wide pending_approval transaction count (KPI)
    pending_count_result = await db.execute(
        select(func.count())
        .select_from(TrustTransaction)
        .where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.status == "pending_approval",
        )
    )
    pending_approval_count = int(pending_count_result.scalar_one())

    # Load all cases that have any trust transaction, with client
    case_ids = set(deposits_by_case) | set(debits_by_case) | set(pending_by_case)
    if not case_ids:
        return TrustOverviewResponse(
            totals=TrustOverviewTotals(
                total_balance=Decimal("0.00"),
                total_pending_disbursements=Decimal("0.00"),
                client_count=0,
                case_count=0,
                pending_approval_count=pending_approval_count,
            ),
            clients=[],
        )

    cases_result = await db.execute(
        select(Case, Contact)
        .join(Contact, Contact.id == Case.client_id)
        .where(
            Case.tenant_id == tenant_id,
            Case.id.in_(case_ids),
        )
    )
    case_rows = cases_result.all()

    # Group cases by contact
    by_contact: dict[uuid.UUID, tuple[Contact, list[CaseTrustSummary]]] = {}
    for case, contact in case_rows:
        deposits = deposits_by_case.get(case.id, Decimal("0.00"))
        debits = debits_by_case.get(case.id, Decimal("0.00"))
        pending = pending_by_case.get(case.id, Decimal("0.00"))
        total_balance = deposits - debits

        if only_nonzero and total_balance == Decimal("0.00") and pending == Decimal("0.00"):
            continue

        summary = CaseTrustSummary(
            case_id=case.id,
            case_number=case.case_number,
            case_description=case.description,
            total_balance=total_balance,
            pending_disbursements=pending,
            last_transaction_date=last_date_by_case.get(case.id),
        )
        if contact.id not in by_contact:
            by_contact[contact.id] = (contact, [])
        by_contact[contact.id][1].append(summary)

    clients: list[ClientTrustOverview] = []
    tenant_total_balance = Decimal("0.00")
    tenant_total_pending = Decimal("0.00")

    for contact, summaries in by_contact.values():
        client_balance = sum((s.total_balance for s in summaries), Decimal("0.00"))
        client_pending = sum((s.pending_disbursements for s in summaries), Decimal("0.00"))
        clients.append(
            ClientTrustOverview(
                contact_id=contact.id,
                contact_name=contact.name,
                total_balance=client_balance,
                pending_disbursements=client_pending,
                case_count=len(summaries),
                cases=sorted(summaries, key=lambda c: c.case_number),
            )
        )
        tenant_total_balance += client_balance
        tenant_total_pending += client_pending

    clients.sort(key=lambda c: c.contact_name.lower())

    return TrustOverviewResponse(
        totals=TrustOverviewTotals(
            total_balance=tenant_total_balance,
            total_pending_disbursements=tenant_total_pending,
            client_count=len(clients),
            case_count=sum(c.case_count for c in clients),
            pending_approval_count=pending_approval_count,
        ),
        clients=clients,
    )


# ── Create Transaction ───────────────────────────────────────────────────────


async def create_transaction(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TrustTransactionCreate,
) -> TrustTransaction:
    """Create a new trust fund deposit or disbursement.

    Deposits are auto-approved. Disbursements start as pending_approval and
    require balance >= amount. Offsets to invoices use create_offset_to_invoice
    instead — they cannot be created via this generic path.
    """
    if data.transaction_type not in TRANSACTION_TYPES:
        raise BadRequestError(
            f"Ongeldig transactietype: {data.transaction_type}. "
            f"Kies uit: {', '.join(TRANSACTION_TYPES)}"
        )

    if data.transaction_type == "offset_to_invoice":
        raise BadRequestError(
            "Verrekening met factuur moet via /trust-funds/cases/{case_id}/offsets "
            "worden aangemaakt vanwege de verplichte cliëntenconsent-velden."
        )

    # Verify case exists and belongs to tenant
    case = await get_case(db, tenant_id, case_id)

    # For disbursements: check available balance
    if data.transaction_type == "disbursement":
        balance = await get_balance(db, tenant_id, case_id)
        if balance.available < data.amount:
            raise BadRequestError(
                f"Onvoldoende saldo. Beschikbaar: {balance.available}, gevraagd: {data.amount}"
            )

    # Deposits are auto-approved, disbursements need approval
    status = "approved" if data.transaction_type == "deposit" else "pending_approval"

    transaction = TrustTransaction(
        tenant_id=tenant_id,
        case_id=case_id,
        contact_id=case.client_id,
        transaction_type=data.transaction_type,
        amount=data.amount,
        transaction_date=data.transaction_date or date.today(),
        description=data.description,
        payment_method=data.payment_method,
        reference=data.reference,
        beneficiary_name=data.beneficiary_name,
        beneficiary_iban=data.beneficiary_iban,
        status=status,
        created_by=user_id,
    )

    db.add(transaction)
    await db.flush()
    await db.refresh(transaction)

    # Workflow hook: log deposit in audit trail (auto-approved deposits only)
    if data.transaction_type == "deposit" and status == "approved":
        from app.workflow.hooks import on_derdengelden_deposit

        await on_derdengelden_deposit(db, tenant_id, case_id, data.amount, user_id)

    return transaction


# ── Offset to Invoice (Verrekening) ──────────────────────────────────────────


async def _get_invoice_outstanding(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> Decimal:
    """Sum existing payments on an invoice and return the outstanding amount."""
    paid_result = await db.execute(
        select(func.coalesce(func.sum(InvoicePayment.amount), Decimal("0.00"))).where(
            InvoicePayment.tenant_id == tenant_id,
            InvoicePayment.invoice_id == invoice_id,
        )
    )
    paid = paid_result.scalar_one()
    inv_result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id)
    )
    invoice = inv_result.scalar_one_or_none()
    if invoice is None:
        raise NotFoundError("Factuur niet gevonden")
    return invoice.total - paid


async def create_offset_to_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TrustOffsetCreate,
) -> TrustTransaction:
    """Create a verrekening: offset trust balance against own invoice.

    Voda art. 6.19 lid 5: requires explicit per-transaction client consent.
    The actual invoice payment record is only created when the offset is
    fully approved (see approve_transaction).
    """
    case = await get_case(db, tenant_id, case_id)

    # Load + validate target invoice
    inv_result = await db.execute(
        select(Invoice).where(
            Invoice.id == data.target_invoice_id,
            Invoice.tenant_id == tenant_id,
            Invoice.is_active.is_(True),
        )
    )
    invoice = inv_result.scalar_one_or_none()
    if invoice is None:
        raise NotFoundError("Doelfactuur niet gevonden")

    # Same client (use case.client_id since that's the trust beneficiary)
    if invoice.contact_id != case.client_id:
        raise BadRequestError(
            "De factuur hoort niet bij dezelfde cliënt als dit dossier — "
            "verrekening is alleen toegestaan binnen één cliënt."
        )

    if invoice.status not in ("sent", "overdue", "partially_paid"):
        raise BadRequestError(
            f"Verrekening alleen mogelijk op verzonden/te late/deels betaalde facturen. "
            f"Huidige status: {invoice.status}"
        )

    # Check trust balance
    balance = await get_balance(db, tenant_id, case_id)
    if balance.available < data.amount:
        raise BadRequestError(
            f"Onvoldoende derdengelden-saldo. Beschikbaar: €{balance.available}, "
            f"gevraagd: €{data.amount}"
        )

    # Check invoice has enough outstanding
    outstanding = await _get_invoice_outstanding(db, tenant_id, data.target_invoice_id)
    if outstanding < data.amount:
        raise BadRequestError(
            f"Het te verrekenen bedrag (€{data.amount}) is hoger dan het openstaande "
            f"factuurbedrag (€{outstanding})."
        )

    # Validate consent method (already validated in schema, double-check)
    if data.consent_method not in CONSENT_METHODS:
        raise BadRequestError(
            f"Ongeldige consent_method: {data.consent_method}. "
            f"Kies uit: {', '.join(CONSENT_METHODS)}"
        )

    transaction = TrustTransaction(
        tenant_id=tenant_id,
        case_id=case_id,
        contact_id=case.client_id,
        transaction_type="offset_to_invoice",
        amount=data.amount,
        transaction_date=data.transaction_date or date.today(),
        description=data.description,
        payment_method="verrekening",
        target_invoice_id=data.target_invoice_id,
        consent_received_at=data.consent_received_at,
        consent_method=data.consent_method,
        consent_note=data.consent_note,
        consent_document_url=data.consent_document_url,
        status="pending_approval",
        created_by=user_id,
    )

    db.add(transaction)
    await db.flush()
    await db.refresh(transaction)
    return transaction


# ── Eligible invoices for offset ─────────────────────────────────────────────


async def list_eligible_invoices_for_offset(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> list[EligibleInvoice]:
    """List open invoices for the case's client that can be offset against.

    Cross-case query: any open invoice belonging to the same client (the
    trust balance beneficiary) is eligible, not just invoices on this case.
    """
    case = await get_case(db, tenant_id, case_id)

    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.case))
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.contact_id == case.client_id,
            Invoice.is_active.is_(True),
            Invoice.invoice_type != "credit_note",
            Invoice.status.in_(("sent", "overdue", "partially_paid")),
        )
        .order_by(Invoice.due_date.asc())
    )
    invoices = list(result.scalars().all())

    # Single grouped query for paid totals
    invoice_ids = [inv.id for inv in invoices]
    paid_map: dict[uuid.UUID, Decimal] = {}
    if invoice_ids:
        paid_result = await db.execute(
            select(
                InvoicePayment.invoice_id,
                func.coalesce(func.sum(InvoicePayment.amount), Decimal("0.00")),
            )
            .where(
                InvoicePayment.tenant_id == tenant_id,
                InvoicePayment.invoice_id.in_(invoice_ids),
            )
            .group_by(InvoicePayment.invoice_id)
        )
        for inv_id, total_paid in paid_result.all():
            paid_map[inv_id] = total_paid

    out: list[EligibleInvoice] = []
    for inv in invoices:
        paid = paid_map.get(inv.id, Decimal("0.00"))
        outstanding = inv.total - paid
        if outstanding <= Decimal("0"):
            continue
        out.append(
            EligibleInvoice(
                id=inv.id,
                invoice_number=inv.invoice_number,
                invoice_date=inv.invoice_date,
                due_date=inv.due_date,
                total=inv.total,
                paid=paid,
                outstanding=outstanding,
                status=inv.status,
                case_id=inv.case_id,
                case_number=inv.case.case_number if inv.case else None,
            )
        )
    return out


# ── Approve Transaction ──────────────────────────────────────────────────────


async def approve_transaction(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    transaction_id: uuid.UUID,
    approver_id: uuid.UUID,
) -> TrustTransaction:
    """Approve a pending trust fund transaction.

    Rules:
    - Transaction must be pending_approval
    - Strict 4-eyes: approver cannot be the creator AND first approver cannot
      sign off as second approver. UNLESS TRUST_FUNDS_ALLOW_SELF_APPROVAL=true
      (single-user solo-practice tenants), in which case the same user may fill
      both approval slots — still recorded as two separate steps for audit.
    - Re-check balance before final approval of debit transactions
    - For offset_to_invoice: also create the InvoicePayment record on final
      approval, atomically in the same DB transaction.
    """
    transaction = await get_transaction(db, tenant_id, transaction_id)

    if transaction.status != "pending_approval":
        raise BadRequestError(
            "Alleen transacties met status 'pending_approval' kunnen worden goedgekeurd"
        )

    self_ok = _self_approval_allowed()

    # Strict mode: approver cannot be the creator
    if not self_ok and approver_id == transaction.created_by:
        raise ForbiddenError("De aanmaker van een transactie kan deze niet zelf goedkeuren")

    now = datetime.now(UTC)

    if transaction.approved_by_1 is None:
        # First approval
        transaction.approved_by_1 = approver_id
        transaction.approved_at_1 = now
    elif transaction.approved_by_2 is None:
        # Second approval — must be a different person than first approver
        # in strict mode
        if not self_ok and approver_id == transaction.approved_by_1:
            raise ForbiddenError(
                "Tweede goedkeuring moet door een andere persoon dan de eerste goedkeurder"
            )

        debit_types = ("disbursement", "offset_to_invoice")
        # Re-check balance before final approval of debit transactions
        if transaction.transaction_type in debit_types:
            balance = await get_balance(db, tenant_id, transaction.case_id)
            # Available balance already excludes this pending transaction,
            # so we need to add it back for comparison
            effective_available = balance.available + transaction.amount
            if effective_available < transaction.amount:
                raise BadRequestError(
                    f"Onvoldoende saldo voor goedkeuring. "
                    f"Beschikbaar: {effective_available}, gevraagd: {transaction.amount}"
                )

        transaction.approved_by_2 = approver_id
        transaction.approved_at_2 = now
        transaction.status = "approved"

        # For offset_to_invoice: now actually book the payment on the invoice.
        if transaction.transaction_type == "offset_to_invoice":
            await _book_offset_payment(db, tenant_id, transaction, approver_id)
    else:
        raise BadRequestError("Transactie is al volledig goedgekeurd")

    await db.flush()
    await db.refresh(transaction)
    return transaction


async def _book_offset_payment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    transaction: TrustTransaction,
    user_id: uuid.UUID,
) -> None:
    """Create the InvoicePayment row that records the offset on the invoice.

    Called only after the offset has its second approval. Updates invoice
    status (sent → partially_paid → paid) consistent with the regular invoice
    payment flow.
    """
    from app.invoices.invoice_payment_service import _update_invoice_payment_status

    if transaction.target_invoice_id is None:
        raise BadRequestError("Verrekening mist doelfactuur — kan niet worden geboekt")

    # Re-check outstanding (defensive — could have changed since creation)
    inv_result = await db.execute(
        select(Invoice).where(
            Invoice.id == transaction.target_invoice_id,
            Invoice.tenant_id == tenant_id,
        )
    )
    invoice = inv_result.scalar_one_or_none()
    if invoice is None:
        raise NotFoundError("Doelfactuur niet meer aanwezig")

    paid_result = await db.execute(
        select(func.coalesce(func.sum(InvoicePayment.amount), Decimal("0.00"))).where(
            InvoicePayment.tenant_id == tenant_id,
            InvoicePayment.invoice_id == invoice.id,
        )
    )
    current_paid = paid_result.scalar_one()
    if current_paid + transaction.amount > invoice.total:
        outstanding = invoice.total - current_paid
        raise BadRequestError(
            f"Verrekening overschrijdt factuurbedrag. "
            f"Openstaand: {outstanding}, te verrekenen: {transaction.amount}"
        )

    payment = InvoicePayment(
        tenant_id=tenant_id,
        invoice_id=invoice.id,
        amount=transaction.amount,
        payment_date=transaction.transaction_date,
        payment_method="verrekening",
        reference=f"Derdengelden-verrekening {transaction.id}",
        description=f"Verrekening van derdengeldensaldo: {transaction.description}",
        created_by=user_id,
    )
    db.add(payment)
    await db.flush()

    new_total_paid = current_paid + transaction.amount
    await _update_invoice_payment_status(db, invoice, new_total_paid)
    await db.flush()


# ── Reject Transaction ───────────────────────────────────────────────────────


async def reject_transaction(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    transaction_id: uuid.UUID,
    user_id: uuid.UUID,
) -> TrustTransaction:
    """Reject a pending trust fund transaction."""
    transaction = await get_transaction(db, tenant_id, transaction_id)

    if transaction.status != "pending_approval":
        raise BadRequestError(
            "Alleen transacties met status 'pending_approval' kunnen worden afgewezen"
        )

    transaction.status = "rejected"
    await db.flush()
    await db.refresh(transaction)
    return transaction


# ── Get / List ───────────────────────────────────────────────────────────────


async def get_transaction(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    transaction_id: uuid.UUID,
) -> TrustTransaction:
    """Get a single trust transaction by ID."""
    result = await db.execute(
        select(TrustTransaction).where(
            TrustTransaction.id == transaction_id,
            TrustTransaction.tenant_id == tenant_id,
        )
    )
    transaction = result.scalar_one_or_none()
    if transaction is None:
        raise NotFoundError("Transactie niet gevonden")
    return transaction


async def list_transactions(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    *,
    page: int = 1,
    per_page: int = 20,
    transaction_type: str | None = None,
    status: str | None = None,
) -> tuple[list[TrustTransaction], int]:
    """List trust transactions for a case with optional filters."""
    query = select(TrustTransaction).where(
        TrustTransaction.tenant_id == tenant_id,
        TrustTransaction.case_id == case_id,
    )

    if transaction_type:
        query = query.where(TrustTransaction.transaction_type == transaction_type)

    if status:
        query = query.where(TrustTransaction.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Apply pagination and ordering (newest first)
    query = (
        query.order_by(TrustTransaction.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    result = await db.execute(query)
    transactions = list(result.scalars().all())

    return transactions, total
