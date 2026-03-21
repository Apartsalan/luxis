"""Invoice payment service — payments, receivables, and aging."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.invoices.models import PAYMENT_METHODS, Invoice, InvoicePayment
from app.invoices.schemas import (
    AdvanceBalanceResponse,
    AgingBucket,
    ContactReceivable,
    InvoicePaymentCreate,
    InvoicePaymentSummary,
    ReceivablesSummary,
)
from app.shared.exceptions import BadRequestError, NotFoundError


async def _total_paid(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> Decimal:
    """Sum all payments for an invoice."""
    result = await db.execute(
        select(
            func.coalesce(func.sum(InvoicePayment.amount), Decimal("0.00"))
        ).where(
            InvoicePayment.tenant_id == tenant_id,
            InvoicePayment.invoice_id == invoice_id,
        )
    )
    return result.scalar_one()


async def _update_invoice_payment_status(
    db: AsyncSession,
    invoice: Invoice,
    total_paid: Decimal,
) -> None:
    """Automatically update invoice status based on total payments.

    Rules:
    - total_paid >= total → paid
    - 0 < total_paid < total → partially_paid
    - total_paid == 0 → revert to sent (from partially_paid or paid)
    """
    if total_paid >= invoice.total:
        invoice.status = "paid"
        invoice.paid_date = date.today()
    elif total_paid > Decimal("0"):
        invoice.status = "partially_paid"
        invoice.paid_date = None
    else:
        # No payments remaining — revert to sent
        if invoice.status in ("partially_paid", "paid"):
            invoice.status = "sent"
            invoice.paid_date = None


async def create_invoice_payment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    user_id: uuid.UUID,
    data: InvoicePaymentCreate,
) -> InvoicePayment:
    """Record a payment against an invoice.

    Validates:
    - Invoice must be in a payable status (sent, overdue, partially_paid)
    - Payment method must be valid
    - Total payments cannot exceed invoice total
    """
    from app.invoices.service import get_invoice

    invoice = await get_invoice(db, tenant_id, invoice_id)

    payable_statuses = ("sent", "overdue", "partially_paid")
    if invoice.status not in payable_statuses:
        raise BadRequestError(
            f"Betalingen kunnen alleen worden geregistreerd op facturen met "
            f"status: verzonden, te laat, of deels betaald. "
            f"Huidige status: {invoice.status}"
        )

    if data.payment_method not in PAYMENT_METHODS:
        raise BadRequestError(
            f"Ongeldige betaalmethode: {data.payment_method}. "
            f"Kies uit: {', '.join(PAYMENT_METHODS)}"
        )

    # Check that total won't exceed invoice total
    current_paid = await _total_paid(db, tenant_id, invoice_id)
    if current_paid + data.amount > invoice.total:
        outstanding = invoice.total - current_paid
        raise BadRequestError(
            f"Betaling overschrijdt factuurbedrag. "
            f"Openstaand: {outstanding}, betaling: {data.amount}"
        )

    payment = InvoicePayment(
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        amount=data.amount,
        payment_date=data.payment_date,
        payment_method=data.payment_method,
        reference=data.reference,
        description=data.description,
        created_by=user_id,
    )
    db.add(payment)
    await db.flush()

    # Update invoice status
    new_total_paid = current_paid + data.amount
    await _update_invoice_payment_status(db, invoice, new_total_paid)
    await db.flush()

    await db.refresh(payment)
    return payment


async def list_invoice_payments(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> list[InvoicePayment]:
    """List all payments for an invoice, newest first."""
    from app.invoices.service import get_invoice

    # Verify invoice exists
    await get_invoice(db, tenant_id, invoice_id)

    result = await db.execute(
        select(InvoicePayment)
        .where(
            InvoicePayment.tenant_id == tenant_id,
            InvoicePayment.invoice_id == invoice_id,
        )
        .order_by(InvoicePayment.payment_date.desc(), InvoicePayment.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_invoice_payment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    payment_id: uuid.UUID,
) -> None:
    """Delete a payment and recalculate invoice status."""
    from app.invoices.service import get_invoice

    invoice = await get_invoice(db, tenant_id, invoice_id)

    result = await db.execute(
        select(InvoicePayment).where(
            InvoicePayment.id == payment_id,
            InvoicePayment.invoice_id == invoice_id,
            InvoicePayment.tenant_id == tenant_id,
        )
    )
    payment = result.scalar_one_or_none()
    if payment is None:
        raise NotFoundError("Betaling niet gevonden")

    await db.delete(payment)
    await db.flush()

    # Recalculate status
    new_total_paid = await _total_paid(db, tenant_id, invoice_id)
    await _update_invoice_payment_status(db, invoice, new_total_paid)
    await db.flush()
    await db.refresh(invoice)


async def get_payment_summary(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> InvoicePaymentSummary:
    """Get payment summary for an invoice."""
    from app.invoices.service import get_invoice

    invoice = await get_invoice(db, tenant_id, invoice_id)

    total_paid = await _total_paid(db, tenant_id, invoice_id)
    outstanding = invoice.total - total_paid

    # Count payments
    count_result = await db.execute(
        select(func.count())
        .select_from(InvoicePayment)
        .where(
            InvoicePayment.tenant_id == tenant_id,
            InvoicePayment.invoice_id == invoice_id,
        )
    )
    payment_count = count_result.scalar_one()

    return InvoicePaymentSummary(
        invoice_id=invoice_id,
        invoice_total=invoice.total,
        total_paid=total_paid,
        outstanding=outstanding,
        payment_count=payment_count,
        is_fully_paid=total_paid >= invoice.total,
    )


async def get_receivables(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> ReceivablesSummary:
    """Build aging receivables overview grouped by contact.

    Considers all active invoices in payable statuses (sent, overdue,
    partially_paid) and calculates outstanding amounts using payment totals.
    Groups into 0-30, 31-60, 61-90, 90+ day aging buckets based on due_date.
    """
    # Fetch all outstanding invoices
    result = await db.execute(
        select(Invoice)
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.is_active.is_(True),
            Invoice.status.in_(("sent", "overdue", "partially_paid")),
        )
        .order_by(Invoice.due_date.asc())
    )
    invoices = list(result.scalars().all())

    today = date.today()

    # CQ-11: Single grouped aggregate query instead of N+1
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

    # Per-invoice: calculate outstanding amount (total - payments)
    contact_map: dict[uuid.UUID, dict] = {}

    for inv in invoices:
        paid = paid_map.get(inv.id, Decimal("0.00"))
        outstanding = inv.total - paid
        if outstanding <= Decimal("0"):
            continue

        # Determine aging bucket
        days_past_due = (today - inv.due_date).days
        if days_past_due <= 30:
            bucket = "current"
        elif days_past_due <= 60:
            bucket = "days_31_60"
        elif days_past_due <= 90:
            bucket = "days_61_90"
        else:
            bucket = "days_90_plus"

        cid = inv.contact_id
        if cid not in contact_map:
            contact_map[cid] = {
                "contact_id": cid,
                "contact_name": inv.contact.name if inv.contact else "Onbekend",
                "invoice_count": 0,
                "total_outstanding": Decimal("0"),
                "current": {"count": 0, "total": Decimal("0")},
                "days_31_60": {"count": 0, "total": Decimal("0")},
                "days_61_90": {"count": 0, "total": Decimal("0")},
                "days_90_plus": {"count": 0, "total": Decimal("0")},
                "oldest_due_date": inv.due_date,
            }

        entry = contact_map[cid]
        entry["invoice_count"] += 1
        entry["total_outstanding"] += outstanding
        entry[bucket]["count"] += 1
        entry[bucket]["total"] += outstanding
        if inv.due_date < entry["oldest_due_date"]:
            entry["oldest_due_date"] = inv.due_date

    # Build summary totals
    total_outstanding = Decimal("0")
    total_overdue = Decimal("0")
    sum_current = AgingBucket()
    sum_31_60 = AgingBucket()
    sum_61_90 = AgingBucket()
    sum_90_plus = AgingBucket()

    contacts: list[ContactReceivable] = []
    for data in sorted(
        contact_map.values(), key=lambda x: x["total_outstanding"], reverse=True
    ):
        total_outstanding += data["total_outstanding"]
        total_overdue += (
            data["days_31_60"]["total"]
            + data["days_61_90"]["total"]
            + data["days_90_plus"]["total"]
        )

        cr = ContactReceivable(
            contact_id=data["contact_id"],
            contact_name=data["contact_name"],
            invoice_count=data["invoice_count"],
            total_outstanding=data["total_outstanding"],
            current=AgingBucket(**data["current"]),
            days_31_60=AgingBucket(**data["days_31_60"]),
            days_61_90=AgingBucket(**data["days_61_90"]),
            days_90_plus=AgingBucket(**data["days_90_plus"]),
            oldest_due_date=data["oldest_due_date"],
        )
        contacts.append(cr)

        sum_current.count += data["current"]["count"]
        sum_current.total += data["current"]["total"]
        sum_31_60.count += data["days_31_60"]["count"]
        sum_31_60.total += data["days_31_60"]["total"]
        sum_61_90.count += data["days_61_90"]["count"]
        sum_61_90.total += data["days_61_90"]["total"]
        sum_90_plus.count += data["days_90_plus"]["count"]
        sum_90_plus.total += data["days_90_plus"]["total"]

    return ReceivablesSummary(
        total_outstanding=total_outstanding,
        total_overdue=total_overdue,
        current=sum_current,
        days_31_60=sum_31_60,
        days_61_90=sum_61_90,
        days_90_plus=sum_90_plus,
        contacts=contacts,
    )


async def get_advance_balance(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> AdvanceBalanceResponse:
    """Calculate available advance balance for a case.

    total_advance = sum of payments on paid voorschotnota's for this case
    total_offset = sum of payments with method 'verrekening' on regular invoices for this case
    available_balance = total_advance - total_offset
    """
    # Find all paid voorschotnota's for this case
    vn_result = await db.execute(
        select(
            func.coalesce(func.sum(InvoicePayment.amount), Decimal("0.00"))
        )
        .select_from(InvoicePayment)
        .join(Invoice, InvoicePayment.invoice_id == Invoice.id)
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.case_id == case_id,
            Invoice.invoice_type == "voorschotnota",
            Invoice.is_active.is_(True),
        )
    )
    total_advance = vn_result.scalar_one()

    # Find verrekening payments on regular invoices for this case
    offset_result = await db.execute(
        select(
            func.coalesce(func.sum(InvoicePayment.amount), Decimal("0.00"))
        )
        .select_from(InvoicePayment)
        .join(Invoice, InvoicePayment.invoice_id == Invoice.id)
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.case_id == case_id,
            Invoice.invoice_type == "invoice",
            Invoice.is_active.is_(True),
            InvoicePayment.payment_method == "verrekening",
        )
    )
    total_offset = offset_result.scalar_one()

    available = total_advance - total_offset

    return AdvanceBalanceResponse(
        case_id=case_id,
        total_advance=total_advance,
        total_offset=total_offset,
        available_balance=available,
    )
