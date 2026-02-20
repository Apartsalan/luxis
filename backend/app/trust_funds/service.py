"""Trust funds module service — Business logic for derdengelden transactions.

Implements Dutch Stichting Derdengelden rules:
- Deposits are auto-approved
- Disbursements require two-director approval (approver != creator)
- Balance may NEVER go negative
- Full audit trail via status + approval fields
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.service import get_case
from app.shared.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.trust_funds.models import TrustTransaction
from app.trust_funds.schemas import (
    TRANSACTION_TYPES,
    TrustBalanceSummary,
    TrustTransactionCreate,
)

# ── Balance Calculation ──────────────────────────────────────────────────────


async def get_balance(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> TrustBalanceSummary:
    """Calculate the trust fund balance for a case.

    total_balance = sum(approved deposits) - sum(approved disbursements)
    pending_disbursements = sum(pending_approval disbursements)
    available = total_balance - pending_disbursements
    """
    # Sum approved deposits
    result = await db.execute(
        select(func.coalesce(func.sum(TrustTransaction.amount), Decimal("0.00"))).where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.case_id == case_id,
            TrustTransaction.transaction_type == "deposit",
            TrustTransaction.status == "approved",
        )
    )
    total_deposits = result.scalar_one()

    # Sum approved disbursements
    result = await db.execute(
        select(func.coalesce(func.sum(TrustTransaction.amount), Decimal("0.00"))).where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.case_id == case_id,
            TrustTransaction.transaction_type == "disbursement",
            TrustTransaction.status == "approved",
        )
    )
    total_disbursements = result.scalar_one()

    # Sum pending disbursements (not yet approved but not rejected)
    result = await db.execute(
        select(func.coalesce(func.sum(TrustTransaction.amount), Decimal("0.00"))).where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.case_id == case_id,
            TrustTransaction.transaction_type == "disbursement",
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


# ── Create Transaction ───────────────────────────────────────────────────────


async def create_transaction(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TrustTransactionCreate,
) -> TrustTransaction:
    """Create a new trust fund transaction.

    Deposits are auto-approved.
    Disbursements start as pending_approval and require balance >= amount.
    """
    if data.transaction_type not in TRANSACTION_TYPES:
        raise BadRequestError(
            f"Ongeldig transactietype: {data.transaction_type}. "
            f"Kies uit: {', '.join(TRANSACTION_TYPES)}"
        )

    # Verify case exists and belongs to tenant
    case = await get_case(db, tenant_id, case_id)

    # For disbursements: check available balance
    if data.transaction_type == "disbursement":
        balance = await get_balance(db, tenant_id, case_id)
        if balance.available < data.amount:
            raise BadRequestError(
                f"Onvoldoende saldo. Beschikbaar: {balance.available}, "
                f"gevraagd: {data.amount}"
            )

    # Deposits are auto-approved, disbursements need approval
    status = "approved" if data.transaction_type == "deposit" else "pending_approval"

    transaction = TrustTransaction(
        tenant_id=tenant_id,
        case_id=case_id,
        contact_id=case.client_id,
        transaction_type=data.transaction_type,
        amount=data.amount,
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
    return transaction


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
    - Approver cannot be the creator
    - Approver cannot approve twice (1st and 2nd must be different people)
    - After 2nd approval, status becomes 'approved'
    - Re-check balance before final approval of disbursements
    """
    transaction = await get_transaction(db, tenant_id, transaction_id)

    if transaction.status != "pending_approval":
        raise BadRequestError(
            "Alleen transacties met status 'pending_approval' kunnen worden goedgekeurd"
        )

    # Approver cannot be the creator
    if approver_id == transaction.created_by:
        raise ForbiddenError(
            "De aanmaker van een transactie kan deze niet zelf goedkeuren"
        )

    now = datetime.now(UTC)

    if transaction.approved_by_1 is None:
        # First approval
        transaction.approved_by_1 = approver_id
        transaction.approved_at_1 = now
    elif transaction.approved_by_2 is None:
        # Second approval — must be a different person than first approver
        if approver_id == transaction.approved_by_1:
            raise ForbiddenError(
                "Tweede goedkeuring moet door een andere persoon dan de eerste goedkeurder"
            )

        # Re-check balance before final approval of disbursements
        if transaction.transaction_type == "disbursement":
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
    else:
        raise BadRequestError("Transactie is al volledig goedgekeurd")

    await db.flush()
    await db.refresh(transaction)
    return transaction


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
