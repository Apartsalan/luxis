"""Collections module service — Claims, Payments, Arrangements, Derdengelden."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.collections.interest import calculate_case_interest
from app.collections.models import (
    Claim,
    Derdengelden,
    InterestRate,
    Payment,
    PaymentArrangement,
    PaymentArrangementInstallment,
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
    RecordInstallmentPayment,
)
from app.collections.wik import calculate_bik
from app.shared.exceptions import BadRequestError, ConflictError, NotFoundError


async def _refresh_case_financials(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> None:
    """Recalculate and update Case.total_principal and Case.total_paid cache."""
    # Sum active claims
    claims = await list_claims(db, tenant_id, case_id)
    total_principal = sum(
        (c.principal_amount for c in claims), Decimal("0")
    )

    # Sum active payments
    payments = await list_payments(db, tenant_id, case_id)
    total_paid = sum(
        (p.amount for p in payments), Decimal("0")
    )

    # Update case
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id)
    )
    case = result.scalar_one_or_none()
    if case:
        case.total_principal = total_principal
        case.total_paid = total_paid
        await db.flush()

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
    await _refresh_case_financials(db, tenant_id, case_id)
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
    await _refresh_case_financials(db, tenant_id, claim.case_id)
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
    case_id = claim.case_id
    claim.is_active = False
    await db.flush()
    await _refresh_case_financials(db, tenant_id, case_id)


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
    bik_override: Decimal | None = None,
    _skip_installment_link: bool = False,
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
                "rate_basis": c.rate_basis,
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

    # BIK costs (LF-12: use override if set)
    if bik_override is not None:
        total_costs = bik_override
    else:
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

    # DF-11: Auto-link payment to installment if active arrangement exists
    if not _skip_installment_link:
        await _auto_link_payment_to_installments(
            db, tenant_id, case_id, payment,
        )

    await _refresh_case_financials(db, tenant_id, case_id)
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
    await _refresh_case_financials(db, tenant_id, payment.case_id)
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
    case_id = payment.case_id
    payment.is_active = False
    await db.flush()
    await _refresh_case_financials(db, tenant_id, case_id)


# ── Payment Arrangements ─────────────────────────────────────────────────────


def _generate_installment_dates(
    start_date: date,
    frequency: str,
    count: int,
) -> list[date]:
    """Generate installment due dates from a start date and frequency."""
    from dateutil.relativedelta import relativedelta

    deltas = {
        "weekly": relativedelta(weeks=1),
        "monthly": relativedelta(months=1),
        "quarterly": relativedelta(months=3),
    }
    delta = deltas[frequency]
    return [start_date + delta * i for i in range(count)]


async def list_arrangements(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> list[dict]:
    """List payment arrangements for a case, with installments."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(PaymentArrangement)
        .options(selectinload(PaymentArrangement.installments))
        .where(
            PaymentArrangement.tenant_id == tenant_id,
            PaymentArrangement.case_id == case_id,
        )
        .order_by(PaymentArrangement.start_date.desc())
    )
    arrangements = list(result.scalars().all())

    out = []
    for arr in arrangements:
        installments = sorted(arr.installments, key=lambda i: i.installment_number)
        out.append({
            "arrangement": arr,
            "installments": installments,
            "paid_count": len([i for i in installments if i.status == "paid"]),
            "total_paid_amount": sum(
                (i.paid_amount for i in installments), Decimal("0")
            ),
        })
    return out


async def get_arrangement(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    arrangement_id: uuid.UUID,
) -> PaymentArrangement:
    """Get a single arrangement with installments."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(PaymentArrangement)
        .options(selectinload(PaymentArrangement.installments))
        .where(
            PaymentArrangement.id == arrangement_id,
            PaymentArrangement.tenant_id == tenant_id,
        )
    )
    arrangement = result.scalar_one_or_none()
    if arrangement is None:
        raise NotFoundError("Betalingsregeling niet gevonden")
    return arrangement


async def create_arrangement(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    data: ArrangementCreate,
) -> PaymentArrangement:
    """Create a payment arrangement with auto-generated installments.

    Validates that there is no other active arrangement for this case.
    Generates installment schedule based on total_amount, installment_amount, and frequency.
    Last installment is adjusted for rounding difference.
    """
    import math

    # Check no other active arrangement exists for this case
    existing = await db.execute(
        select(PaymentArrangement).where(
            PaymentArrangement.tenant_id == tenant_id,
            PaymentArrangement.case_id == case_id,
            PaymentArrangement.status == "active",
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("Er is al een actieve betalingsregeling voor dit dossier")

    # Calculate number of installments
    num_installments = math.ceil(data.total_amount / data.installment_amount)

    # Generate due dates
    due_dates = _generate_installment_dates(
        data.start_date, data.frequency, num_installments
    )

    # Calculate end_date
    end_date = due_dates[-1] if due_dates else data.start_date

    arrangement = PaymentArrangement(
        tenant_id=tenant_id,
        case_id=case_id,
        total_amount=data.total_amount,
        installment_amount=data.installment_amount,
        frequency=data.frequency,
        start_date=data.start_date,
        end_date=end_date,
        status="active",
        notes=data.notes,
    )
    db.add(arrangement)
    await db.flush()

    # Generate installments — last one adjusted for rounding
    remaining = data.total_amount
    for i, due_date in enumerate(due_dates, start=1):
        if i == len(due_dates):
            # Last installment gets the remainder
            amount = remaining
        else:
            amount = min(data.installment_amount, remaining)
        remaining -= amount

        installment = PaymentArrangementInstallment(
            tenant_id=tenant_id,
            arrangement_id=arrangement.id,
            installment_number=i,
            due_date=due_date,
            amount=amount,
            paid_amount=Decimal("0"),
            status="pending",
        )
        db.add(installment)

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


async def record_installment_payment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    arrangement_id: uuid.UUID,
    installment_id: uuid.UUID,
    data: RecordInstallmentPayment,
    user_id: uuid.UUID | None = None,
    *,
    interest_type: str = "statutory",
    contractual_rate: Decimal | None = None,
    contractual_compound: bool = False,
    bik_override: Decimal | None = None,
) -> PaymentArrangementInstallment:
    """Record a payment for a specific installment.

    Creates a Payment record (with art. 6:44 BW distribution) and links it
    to the installment. Updates installment status to paid or partial.
    If all installments are paid, marks the arrangement as completed.
    """
    # Load installment
    result = await db.execute(
        select(PaymentArrangementInstallment).where(
            PaymentArrangementInstallment.id == installment_id,
            PaymentArrangementInstallment.arrangement_id == arrangement_id,
            PaymentArrangementInstallment.tenant_id == tenant_id,
        )
    )
    installment = result.scalar_one_or_none()
    if installment is None:
        raise NotFoundError("Termijn niet gevonden")

    if installment.status in ("paid", "waived"):
        raise BadRequestError("Deze termijn is al betaald of kwijtgescholden")

    # Create a Payment via existing service (art. 6:44 BW distribution)
    payment_data = PaymentCreate(
        amount=data.amount,
        payment_date=data.payment_date,
        description=f"Betalingsregeling termijn {installment.installment_number}",
        payment_method=data.payment_method,
    )
    payment = await create_payment(
        db, tenant_id, case_id, payment_data, user_id,
        interest_type=interest_type,
        contractual_rate=contractual_rate,
        contractual_compound=contractual_compound,
        bik_override=bik_override,
        _skip_installment_link=True,  # Already linking manually below
    )

    # Update installment
    installment.paid_amount = installment.paid_amount + data.amount
    installment.paid_date = data.payment_date
    installment.payment_id = payment.id
    if data.notes:
        installment.notes = data.notes

    if installment.paid_amount >= installment.amount:
        installment.status = "paid"
    else:
        installment.status = "partial"

    await db.flush()

    # Check if all installments are now paid → complete arrangement
    await _check_arrangement_completion(db, tenant_id, arrangement_id)

    await db.refresh(installment)
    return installment


async def default_arrangement(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    arrangement_id: uuid.UUID,
) -> PaymentArrangement:
    """Mark an arrangement as defaulted (wanprestatie).

    Sets all pending/overdue installments to missed.
    """
    arrangement = await get_arrangement(db, tenant_id, arrangement_id)
    if arrangement.status != "active":
        raise BadRequestError("Alleen actieve regelingen kunnen als wanprestatie worden gemarkeerd")

    arrangement.status = "defaulted"

    # Mark all pending/overdue installments as missed
    for inst in arrangement.installments:
        if inst.status in ("pending", "overdue"):
            inst.status = "missed"

    await db.flush()
    await db.refresh(arrangement)
    return arrangement


async def cancel_arrangement(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    arrangement_id: uuid.UUID,
) -> PaymentArrangement:
    """Cancel an arrangement. Waives all pending installments."""
    arrangement = await get_arrangement(db, tenant_id, arrangement_id)
    if arrangement.status != "active":
        raise BadRequestError("Alleen actieve regelingen kunnen worden geannuleerd")

    arrangement.status = "cancelled"

    for inst in arrangement.installments:
        if inst.status in ("pending", "overdue"):
            inst.status = "waived"

    await db.flush()
    await db.refresh(arrangement)
    return arrangement


async def waive_installment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    arrangement_id: uuid.UUID,
    installment_id: uuid.UUID,
) -> PaymentArrangementInstallment:
    """Waive (kwijtschelden) a single installment."""
    result = await db.execute(
        select(PaymentArrangementInstallment).where(
            PaymentArrangementInstallment.id == installment_id,
            PaymentArrangementInstallment.arrangement_id == arrangement_id,
            PaymentArrangementInstallment.tenant_id == tenant_id,
        )
    )
    installment = result.scalar_one_or_none()
    if installment is None:
        raise NotFoundError("Termijn niet gevonden")

    if installment.status in ("paid",):
        raise BadRequestError("Betaalde termijnen kunnen niet worden kwijtgescholden")

    installment.status = "waived"
    await db.flush()

    # Check if all installments are now resolved → complete arrangement
    await _check_arrangement_completion(db, tenant_id, arrangement_id)

    await db.refresh(installment)
    return installment


async def _auto_link_payment_to_installments(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    payment: Payment,
) -> None:
    """DF-11: Auto-link a payment to the next open installment(s).

    When a case has an active payment arrangement, incoming payments are
    automatically matched to the earliest open installment(s) by due_date.
    - Partial: installment stays 'partial'
    - Exact or overshoot: installment becomes 'paid', remainder cascades
    """
    # Find active arrangement for this case
    arr_result = await db.execute(
        select(PaymentArrangement).where(
            PaymentArrangement.case_id == case_id,
            PaymentArrangement.tenant_id == tenant_id,
            PaymentArrangement.status == "active",
        )
    )
    arrangement = arr_result.scalar_one_or_none()
    if arrangement is None:
        return

    # Get open installments sorted by due_date
    inst_result = await db.execute(
        select(PaymentArrangementInstallment).where(
            PaymentArrangementInstallment.arrangement_id == arrangement.id,
            PaymentArrangementInstallment.tenant_id == tenant_id,
            PaymentArrangementInstallment.status.in_(
                ("pending", "partial", "overdue")
            ),
        ).order_by(
            PaymentArrangementInstallment.due_date,
            PaymentArrangementInstallment.installment_number,
        )
    )
    installments = list(inst_result.scalars().all())
    if not installments:
        return

    remaining = payment.amount
    for inst in installments:
        if remaining <= Decimal("0"):
            break

        outstanding = inst.amount - inst.paid_amount
        if outstanding <= Decimal("0"):
            continue

        allocated = min(remaining, outstanding)
        inst.paid_amount = inst.paid_amount + allocated
        inst.paid_date = payment.payment_date
        inst.payment_id = payment.id

        if inst.paid_amount >= inst.amount:
            inst.status = "paid"
        else:
            inst.status = "partial"

        remaining = remaining - allocated

    await db.flush()

    # Check if arrangement is now fully completed
    await _check_arrangement_completion(db, tenant_id, arrangement.id)


async def _check_arrangement_completion(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    arrangement_id: uuid.UUID,
) -> None:
    """Check if all installments are resolved and auto-complete the arrangement."""
    result = await db.execute(
        select(PaymentArrangementInstallment).where(
            PaymentArrangementInstallment.arrangement_id == arrangement_id,
            PaymentArrangementInstallment.tenant_id == tenant_id,
        )
    )
    installments = list(result.scalars().all())

    all_resolved = all(
        i.status in ("paid", "waived") for i in installments
    )
    if all_resolved and installments:
        arr_result = await db.execute(
            select(PaymentArrangement).where(
                PaymentArrangement.id == arrangement_id,
                PaymentArrangement.tenant_id == tenant_id,
            )
        )
        arrangement = arr_result.scalar_one_or_none()
        if arrangement and arrangement.status == "active":
            arrangement.status = "completed"
            await db.flush()


async def mark_overdue_installments(db: AsyncSession) -> int:
    """Mark pending installments past due_date as overdue. Returns count updated."""
    from datetime import date as date_type

    today = date_type.today()
    result = await db.execute(
        select(PaymentArrangementInstallment).where(
            PaymentArrangementInstallment.status == "pending",
            PaymentArrangementInstallment.due_date < today,
        )
    )
    installments = list(result.scalars().all())
    for inst in installments:
        inst.status = "overdue"
    await db.flush()
    return len(installments)


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
    bik_override: Decimal | None = None,
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
            "rate_basis": c.rate_basis,
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

    # Calculate BIK (LF-12: use override if set)
    bik_result = calculate_bik(total_principal)
    if bik_override is not None:
        bik_exclusive = bik_override
        bik_btw = Decimal("0")
        total_bik = bik_override
    else:
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
