"""Collections module service — Claims, Payments, Arrangements, Derdengelden."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collections.interest import calculate_case_interest
from app.collections.models import (
    Claim,
    Derdengelden,
    InterestRate,
    Payment,
    PaymentArrangement,
)
from app.collections.payment_distribution import distribute_payment
from app.collections.schemas import (
    ArrangementCreate,
    ArrangementUpdate,
    ClaimCreate,
    ClaimUpdate,
    DerdengeldenCreate,
    PaymentCreate,
    PaymentUpdate,
)
from app.collections.wik import calculate_bik
from app.shared.exceptions import NotFoundError

# ── Claims ───────────────────────────────────────────────────────────────────


async def list_claims(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> list[Claim]:
    """List all active claims for a case."""
    result = await db.execute(
        select(Claim).where(
            Claim.tenant_id == tenant_id,
            Claim.case_id == case_id,
            Claim.is_active.is_(True),
        ).order_by(Claim.default_date)
    )
    return list(result.scalars().all())


async def create_claim(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    data: ClaimCreate,
) -> Claim:
    """Create a new claim for a case."""
    claim = Claim(
        tenant_id=tenant_id,
        case_id=case_id,
        **data.model_dump(),
    )
    db.add(claim)
    await db.flush()
    await db.refresh(claim)
    return claim


async def update_claim(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    claim_id: uuid.UUID,
    data: ClaimUpdate,
) -> Claim:
    """Update an existing claim."""
    result = await db.execute(
        select(Claim).where(
            Claim.id == claim_id,
            Claim.tenant_id == tenant_id,
        )
    )
    claim = result.scalar_one_or_none()
    if claim is None:
        raise NotFoundError("Vordering niet gevonden")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(claim, field, value)

    await db.flush()
    await db.refresh(claim)
    return claim


async def delete_claim(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    claim_id: uuid.UUID,
) -> None:
    """Soft-delete a claim."""
    result = await db.execute(
        select(Claim).where(
            Claim.id == claim_id,
            Claim.tenant_id == tenant_id,
        )
    )
    claim = result.scalar_one_or_none()
    if claim is None:
        raise NotFoundError("Vordering niet gevonden")
    claim.is_active = False
    await db.flush()


# ── Payments ─────────────────────────────────────────────────────────────────


async def list_payments(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> list[Payment]:
    """List all active payments for a case."""
    result = await db.execute(
        select(Payment).where(
            Payment.tenant_id == tenant_id,
            Payment.case_id == case_id,
            Payment.is_active.is_(True),
        ).order_by(Payment.payment_date)
    )
    return list(result.scalars().all())


async def create_payment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    data: PaymentCreate,
    user_id: uuid.UUID | None = None,
    *,
    interest_type: str = "statutory",
    contractual_rate: Decimal | None = None,
    contractual_compound: bool = False,
) -> Payment:
    """Register a payment for a case.

    Distributes the payment per art. 6:44 BW (costs -> interest -> principal)
    and stores the allocation on the payment record.

    After creating the payment, triggers the workflow payment hook
    to check if the case is fully paid and should auto-transition to 'betaald'.
    """
    # ── Calculate outstanding amounts as of payment date ──────────────
    claims = await list_claims(db, tenant_id, case_id)
    total_principal = sum(
        (c.principal_amount for c in claims), Decimal("0")
    )

    # Interest as of payment date
    if claims:
        claim_dicts = [
            {
                "id": str(c.id),
                "description": c.description,
                "principal_amount": c.principal_amount,
                "default_date": c.default_date,
            }
            for c in claims
        ]
        interest_result = await calculate_case_interest(
            db, str(case_id), interest_type, contractual_rate,
            contractual_compound, claim_dicts, data.payment_date,
        )
        total_interest = interest_result["total_interest"]
    else:
        total_interest = Decimal("0")

    # BIK costs
    bik_result = calculate_bik(total_principal)
    total_costs = bik_result["bik_inclusive"]

    # Subtract previously allocated amounts from existing payments
    existing_payments = await list_payments(db, tenant_id, case_id)
    prev_costs = sum(
        (p.allocated_to_costs for p in existing_payments), Decimal("0")
    )
    prev_interest = sum(
        (p.allocated_to_interest for p in existing_payments), Decimal("0")
    )
    prev_principal = sum(
        (p.allocated_to_principal for p in existing_payments), Decimal("0")
    )

    outstanding_costs = max(Decimal("0"), total_costs - prev_costs)
    outstanding_interest = max(Decimal("0"), total_interest - prev_interest)
    outstanding_principal = max(Decimal("0"), total_principal - prev_principal)

    # ── Distribute per art. 6:44 BW ──────────────────────────────────
    distribution = distribute_payment(
        payment_amount=data.amount,
        outstanding_costs=outstanding_costs,
        outstanding_interest=outstanding_interest,
        outstanding_principal=outstanding_principal,
    )

    payment = Payment(
        tenant_id=tenant_id,
        case_id=case_id,
        amount=data.amount,
        payment_date=data.payment_date,
        description=data.description,
        payment_method=data.payment_method,
        allocated_to_costs=distribution["to_costs"],
        allocated_to_interest=distribution["to_interest"],
        allocated_to_principal=distribution["to_principal"],
    )
    db.add(payment)
    await db.flush()
    await db.refresh(payment)

    # Workflow hook: check if case is fully paid
    from app.workflow.hooks import on_payment_received

    await on_payment_received(db, tenant_id, case_id, data.amount, user_id)

    return payment


async def update_payment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    payment_id: uuid.UUID,
    data: PaymentUpdate,
) -> Payment:
    """Update a payment."""
    result = await db.execute(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.tenant_id == tenant_id,
        )
    )
    payment = result.scalar_one_or_none()
    if payment is None:
        raise NotFoundError("Betaling niet gevonden")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)

    await db.flush()
    await db.refresh(payment)
    return payment


async def delete_payment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    payment_id: uuid.UUID,
) -> None:
    """Soft-delete a payment."""
    result = await db.execute(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.tenant_id == tenant_id,
        )
    )
    payment = result.scalar_one_or_none()
    if payment is None:
        raise NotFoundError("Betaling niet gevonden")
    payment.is_active = False
    await db.flush()


# ── Payment Arrangements ─────────────────────────────────────────────────────


async def list_arrangements(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> list[PaymentArrangement]:
    """List payment arrangements for a case."""
    result = await db.execute(
        select(PaymentArrangement).where(
            PaymentArrangement.tenant_id == tenant_id,
            PaymentArrangement.case_id == case_id,
        ).order_by(PaymentArrangement.start_date.desc())
    )
    return list(result.scalars().all())


async def create_arrangement(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    data: ArrangementCreate,
) -> PaymentArrangement:
    """Create a payment arrangement."""
    arrangement = PaymentArrangement(
        tenant_id=tenant_id,
        case_id=case_id,
        **data.model_dump(),
    )
    db.add(arrangement)
    await db.flush()
    await db.refresh(arrangement)
    return arrangement


async def update_arrangement(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    arrangement_id: uuid.UUID,
    data: ArrangementUpdate,
) -> PaymentArrangement:
    """Update a payment arrangement (e.g. mark as completed/defaulted)."""
    result = await db.execute(
        select(PaymentArrangement).where(
            PaymentArrangement.id == arrangement_id,
            PaymentArrangement.tenant_id == tenant_id,
        )
    )
    arrangement = result.scalar_one_or_none()
    if arrangement is None:
        raise NotFoundError("Betalingsregeling niet gevonden")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(arrangement, field, value)

    await db.flush()
    await db.refresh(arrangement)
    return arrangement


# ── Derdengelden ─────────────────────────────────────────────────────────────


async def list_derdengelden(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> list[Derdengelden]:
    """List derdengelden transactions for a case."""
    result = await db.execute(
        select(Derdengelden).where(
            Derdengelden.tenant_id == tenant_id,
            Derdengelden.case_id == case_id,
        ).order_by(Derdengelden.transaction_date.desc())
    )
    return list(result.scalars().all())


async def create_derdengelden(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    data: DerdengeldenCreate,
    user_id: uuid.UUID | None = None,
) -> Derdengelden:
    """Register a derdengelden transaction.

    Triggers audit trail logging for deposits.
    """
    transaction = Derdengelden(
        tenant_id=tenant_id,
        case_id=case_id,
        **data.model_dump(),
    )
    db.add(transaction)
    await db.flush()
    await db.refresh(transaction)

    # Workflow hook: log deposit in audit trail
    if data.transaction_type == "deposit":
        from app.workflow.hooks import on_derdengelden_deposit

        await on_derdengelden_deposit(
            db, tenant_id, case_id, data.amount, user_id
        )

    return transaction


async def get_derdengelden_balance(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> dict:
    """Calculate derdengelden balance for a case."""
    transactions = await list_derdengelden(db, tenant_id, case_id)

    total_deposits = Decimal("0")
    total_withdrawals = Decimal("0")

    for t in transactions:
        if t.transaction_type == "deposit":
            total_deposits += t.amount
        else:
            total_withdrawals += t.amount

    return {
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "balance": total_deposits - total_withdrawals,
    }


# ── Interest Rates (reference data) ─────────────────────────────────────────


async def list_interest_rates(
    db: AsyncSession,
    rate_type: str | None = None,
) -> list[InterestRate]:
    """List interest rates, optionally filtered by type."""
    query = select(InterestRate).order_by(
        InterestRate.rate_type, InterestRate.effective_from
    )
    if rate_type:
        query = query.where(InterestRate.rate_type == rate_type)
    result = await db.execute(query)
    return list(result.scalars().all())


# ── Financial Summary ────────────────────────────────────────────────────────


async def get_financial_summary(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    interest_type: str,
    contractual_rate: Decimal | None,
    contractual_compound: bool,
    calc_date: date | None = None,
) -> dict:
    """Build a complete financial summary for a case.

    Combines: claims + interest + BIK + payments + derdengelden
    """
    if calc_date is None:
        calc_date = date.today()

    # Get claims
    claims = await list_claims(db, tenant_id, case_id)
    claim_dicts = [
        {
            "id": str(c.id),
            "description": c.description,
            "principal_amount": c.principal_amount,
            "default_date": c.default_date,
        }
        for c in claims
    ]

    # Calculate interest
    interest_result = await calculate_case_interest(
        db,
        str(case_id),
        interest_type,
        contractual_rate,
        contractual_compound,
        claim_dicts,
        calc_date,
    )

    total_principal = interest_result["total_principal"]
    total_interest = interest_result["total_interest"]

    # Calculate BIK
    bik_result = calculate_bik(total_principal)
    bik_exclusive = bik_result["bik_exclusive"]
    bik_btw = bik_result["btw_amount"]
    total_bik = bik_result["bik_inclusive"]

    # Get payments
    payments = await list_payments(db, tenant_id, case_id)
    total_paid = sum(p.amount for p in payments)
    total_paid_costs = sum(p.allocated_to_costs for p in payments)
    total_paid_interest = sum(p.allocated_to_interest for p in payments)
    total_paid_principal = sum(p.allocated_to_principal for p in payments)

    # Grand total
    grand_total = total_principal + total_interest + total_bik
    total_outstanding = grand_total - total_paid

    # Derdengelden
    derdengelden = await get_derdengelden_balance(db, tenant_id, case_id)

    return {
        "case_id": str(case_id),
        "calculation_date": calc_date,
        "total_principal": total_principal,
        "total_paid_principal": total_paid_principal,
        "remaining_principal": total_principal - total_paid_principal,
        "total_interest": total_interest,
        "total_paid_interest": total_paid_interest,
        "remaining_interest": total_interest - total_paid_interest,
        "bik_amount": bik_exclusive,
        "bik_btw": bik_btw,
        "total_bik": total_bik,
        "total_paid_costs": total_paid_costs,
        "remaining_costs": total_bik - total_paid_costs,
        "grand_total": grand_total,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "derdengelden_balance": derdengelden["balance"],
        "interest_details": interest_result,
    }
