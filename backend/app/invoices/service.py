"""Invoices module service — CRUD, status workflow, lines, expenses, voorschotnota, budget."""

import math
import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.invoices.invoice_numbering import (
    next_credit_note_number,
    next_invoice_number,
    next_voorschotnota_number,
)
from app.invoices.models import Expense, Invoice, InvoiceLine
from app.invoices.schemas import (
    BudgetStatusResponse,
    CreditNoteCreate,
    ExpenseCreate,
    ExpenseUpdate,
    InvoiceCreate,
    InvoiceUpdate,
    ProvisieCalculationResponse,
    VoorschotnotaCreate,
)
from app.shared.exceptions import BadRequestError, NotFoundError
from app.time_entries.models import TimeEntry

# ── Invoice Totals ───────────────────────────────────────────────────────────


async def _recalculate_totals(db: AsyncSession, invoice: Invoice) -> None:
    """Recalculate subtotal, BTW, and total from DB aggregate (CQ-15)."""
    result = await db.execute(
        select(func.coalesce(func.sum(InvoiceLine.line_total), Decimal("0.00")))
        .where(InvoiceLine.invoice_id == invoice.id)
    )
    subtotal = result.scalar_one()

    invoice.subtotal = subtotal
    invoice.btw_amount = (
        subtotal * invoice.btw_percentage / Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    invoice.total = invoice.subtotal + invoice.btw_amount


# ── Status Workflow ──────────────────────────────────────────────────────────

VALID_TRANSITIONS = {
    "concept": {"approved", "cancelled"},
    "approved": {"sent", "cancelled"},
    "sent": {"partially_paid", "paid", "overdue", "cancelled"},
    "overdue": {"partially_paid", "paid", "cancelled"},
    "partially_paid": {"paid", "cancelled"},
    "paid": set(),
    "cancelled": set(),
}


def _validate_transition(current: str, new: str) -> None:
    allowed = VALID_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise BadRequestError(
            f"Ongeldige statuswijziging: {current} → {new}"
        )


# ── Invoice CRUD ─────────────────────────────────────────────────────────────


async def list_invoices(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    search: str | None = None,
    case_id: uuid.UUID | None = None,
) -> dict:
    """List invoices with pagination, optional status filter and search."""
    query = (
        select(Invoice)
        .options(selectinload(Invoice.linked_invoice))
        .where(Invoice.tenant_id == tenant_id, Invoice.is_active.is_(True))
        .order_by(Invoice.invoice_date.desc(), Invoice.invoice_number.desc())
    )

    count_query = (
        select(func.count())
        .select_from(Invoice)
        .where(Invoice.tenant_id == tenant_id, Invoice.is_active.is_(True))
    )

    if case_id:
        query = query.where(Invoice.case_id == case_id)
        count_query = count_query.where(Invoice.case_id == case_id)

    if status:
        query = query.where(Invoice.status == status)
        count_query = count_query.where(Invoice.status == status)

    if search:
        pattern = f"%{search}%"
        query = query.where(Invoice.invoice_number.ilike(pattern))
        count_query = count_query.where(Invoice.invoice_number.ilike(pattern))

    total = (await db.execute(count_query)).scalar_one()
    pages = max(1, math.ceil(total / per_page))

    result = await db.execute(
        query.offset((page - 1) * per_page).limit(per_page)
    )
    invoices = list(result.scalars().all())

    items = []
    for inv in invoices:
        items.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_type": inv.invoice_type or "invoice",
            "status": inv.status,
            "contact_id": inv.contact_id,
            "contact_name": inv.contact.name if inv.contact else None,
            "case_id": inv.case_id,
            "case_number": inv.case.case_number if inv.case else None,
            "linked_invoice_id": inv.linked_invoice_id,
            "linked_invoice_number": (
                inv.linked_invoice.invoice_number
                if inv.linked_invoice else None
            ),
            "invoice_date": inv.invoice_date,
            "due_date": inv.due_date,
            "subtotal": inv.subtotal,
            "btw_amount": inv.btw_amount,
            "total": inv.total,
            "created_at": inv.created_at,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


async def get_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> Invoice:
    """Get a single invoice by ID."""
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.contact),
            selectinload(Invoice.case),
            selectinload(Invoice.lines),
            selectinload(Invoice.payments),
            selectinload(Invoice.credit_notes),
            selectinload(Invoice.linked_invoice),
        )
        .where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == tenant_id,
            Invoice.is_active.is_(True),
        )
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise NotFoundError("Factuur niet gevonden")
    return invoice


async def create_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: InvoiceCreate,
) -> Invoice:
    """Create a new invoice with lines."""
    invoice_number = await next_invoice_number(db, tenant_id)

    invoice = Invoice(
        tenant_id=tenant_id,
        invoice_number=invoice_number,
        status="concept",
        contact_id=data.contact_id,
        case_id=data.case_id,
        invoice_date=data.invoice_date,
        due_date=data.due_date,
        btw_percentage=data.btw_percentage,
        reference=data.reference,
        notes=data.notes,
    )
    db.add(invoice)
    await db.flush()

    # Add lines
    for i, line_data in enumerate(data.lines, start=1):
        line_total = (line_data.quantity * line_data.unit_price).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        line = InvoiceLine(
            tenant_id=tenant_id,
            invoice_id=invoice.id,
            line_number=i,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_total,
            time_entry_id=line_data.time_entry_id,
            expense_id=line_data.expense_id,
        )
        db.add(line)

    await db.flush()
    await db.refresh(invoice)

    # Mark linked expenses as invoiced
    for line_data in data.lines:
        if line_data.expense_id:
            exp_result = await db.execute(
                select(Expense).where(
                    Expense.id == line_data.expense_id,
                    Expense.tenant_id == tenant_id,
                )
            )
            expense = exp_result.scalar_one_or_none()
            if expense:
                expense.invoiced = True

    # Mark linked time entries as invoiced (E5)
    for line_data in data.lines:
        if line_data.time_entry_id:
            te_result = await db.execute(
                select(TimeEntry).where(
                    TimeEntry.id == line_data.time_entry_id,
                    TimeEntry.tenant_id == tenant_id,
                )
            )
            time_entry = te_result.scalar_one_or_none()
            if time_entry:
                time_entry.invoiced = True

    await _recalculate_totals(db, invoice)
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def update_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    data: InvoiceUpdate,
) -> Invoice:
    """Update an invoice (only allowed in concept status)."""
    invoice = await get_invoice(db, tenant_id, invoice_id)

    if invoice.status != "concept":
        raise BadRequestError("Alleen conceptfacturen kunnen worden bewerkt")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(invoice, field, value)

    # Recalculate if btw_percentage changed
    if data.btw_percentage is not None:
        await _recalculate_totals(db, invoice)

    await db.flush()
    await db.refresh(invoice)
    return invoice


async def delete_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> None:
    """Soft-delete an invoice (only concept or cancelled)."""
    invoice = await get_invoice(db, tenant_id, invoice_id)

    if invoice.status not in ("concept", "cancelled"):
        raise BadRequestError(
            "Alleen concept- of geannuleerde facturen kunnen worden verwijderd"
        )

    invoice.is_active = False
    await db.flush()


# ── Credit Notes ─────────────────────────────────────────────────────────────


async def create_credit_note(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: CreditNoteCreate,
) -> Invoice:
    """Create a credit note linked to an existing invoice.

    The linked invoice must be in a non-concept, non-cancelled status.
    Credit note lines typically mirror the original invoice lines
    (partial or full credit).
    """
    # Validate linked invoice
    original = await get_invoice(db, tenant_id, data.linked_invoice_id)

    if original.status in ("concept", "cancelled"):
        raise BadRequestError(
            "Credit nota's kunnen alleen worden aangemaakt voor "
            "goedgekeurde, verzonden of betaalde facturen"
        )

    if original.invoice_type == "credit_note":
        raise BadRequestError(
            "Een credit nota kan niet worden aangemaakt voor een andere credit nota"
        )

    credit_note_number = await next_credit_note_number(db, tenant_id)

    credit_note = Invoice(
        tenant_id=tenant_id,
        invoice_number=credit_note_number,
        invoice_type="credit_note",
        status="concept",
        linked_invoice_id=data.linked_invoice_id,
        contact_id=original.contact_id,
        case_id=original.case_id,
        invoice_date=data.invoice_date,
        due_date=data.due_date,
        btw_percentage=data.btw_percentage,
        reference=data.reference,
        notes=data.notes,
    )
    db.add(credit_note)
    await db.flush()

    # Add lines
    for i, line_data in enumerate(data.lines, start=1):
        line_total = (line_data.quantity * line_data.unit_price).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        line = InvoiceLine(
            tenant_id=tenant_id,
            invoice_id=credit_note.id,
            line_number=i,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_total,
        )
        db.add(line)

    await db.flush()
    await db.refresh(credit_note)
    await _recalculate_totals(db, credit_note)
    await db.flush()
    await db.refresh(credit_note)
    return credit_note


# ── Status Transitions ───────────────────────────────────────────────────────


async def approve_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> Invoice:
    """Approve a concept invoice."""
    invoice = await get_invoice(db, tenant_id, invoice_id)
    _validate_transition(invoice.status, "approved")

    if not invoice.lines:
        raise BadRequestError("Factuur heeft geen regels")

    invoice.status = "approved"
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def send_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> Invoice:
    """Mark an invoice as sent."""
    invoice = await get_invoice(db, tenant_id, invoice_id)
    _validate_transition(invoice.status, "sent")
    invoice.status = "sent"
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def mark_paid(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    paid_date: date | None = None,
) -> Invoice:
    """Mark an invoice as paid (CQ-17: verifies payments cover invoice total)."""
    from app.invoices.invoice_payment_service import _total_paid

    invoice = await get_invoice(db, tenant_id, invoice_id)
    _validate_transition(invoice.status, "paid")

    # CQ-17: Verify that recorded payments cover the invoice total
    total_paid = await _total_paid(db, tenant_id, invoice_id)
    if total_paid < invoice.total:
        raise BadRequestError(
            f"Factuur kan niet als betaald worden gemarkeerd: "
            f"totaal betaald ({total_paid}) is minder dan factuurbedrag ({invoice.total}). "
            f"Registreer eerst de betaling(en)."
        )

    invoice.status = "paid"
    invoice.paid_date = paid_date or date.today()
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def cancel_invoice(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> Invoice:
    """Cancel an invoice."""
    invoice = await get_invoice(db, tenant_id, invoice_id)
    _validate_transition(invoice.status, "cancelled")
    invoice.status = "cancelled"
    await db.flush()
    await db.refresh(invoice)
    return invoice


# ── Invoice Lines ────────────────────────────────────────────────────────────


async def add_line(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    description: str,
    quantity: Decimal,
    unit_price: Decimal,
    time_entry_id: uuid.UUID | None = None,
    expense_id: uuid.UUID | None = None,
) -> InvoiceLine:
    """Add a line to a concept invoice."""
    invoice = await get_invoice(db, tenant_id, invoice_id)

    if invoice.status != "concept":
        raise BadRequestError("Regels kunnen alleen aan conceptfacturen worden toegevoegd")

    # Determine next line number
    max_line = max(
        (line.line_number for line in invoice.lines), default=0
    )

    line_total = (quantity * unit_price).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    line = InvoiceLine(
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        line_number=max_line + 1,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        line_total=line_total,
        time_entry_id=time_entry_id,
        expense_id=expense_id,
    )
    db.add(line)

    # Mark expense as invoiced
    if expense_id:
        exp_result = await db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.tenant_id == tenant_id,
            )
        )
        expense = exp_result.scalar_one_or_none()
        if expense:
            expense.invoiced = True

    await db.flush()
    await db.refresh(invoice)
    await _recalculate_totals(db, invoice)
    await db.flush()
    await db.refresh(invoice)
    return line


async def remove_line(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    line_id: uuid.UUID,
) -> None:
    """Remove a line from a concept invoice."""
    invoice = await get_invoice(db, tenant_id, invoice_id)

    if invoice.status != "concept":
        raise BadRequestError("Regels kunnen alleen van conceptfacturen worden verwijderd")

    result = await db.execute(
        select(InvoiceLine).where(
            InvoiceLine.id == line_id,
            InvoiceLine.invoice_id == invoice_id,
            InvoiceLine.tenant_id == tenant_id,
        )
    )
    line = result.scalar_one_or_none()
    if line is None:
        raise NotFoundError("Factuurregel niet gevonden")

    # Un-mark expense if linked
    if line.expense_id:
        exp_result = await db.execute(
            select(Expense).where(
                Expense.id == line.expense_id,
                Expense.tenant_id == tenant_id,
            )
        )
        expense = exp_result.scalar_one_or_none()
        if expense:
            expense.invoiced = False

    # Un-mark time entry if linked (E5)
    if line.time_entry_id:
        te_result = await db.execute(
            select(TimeEntry).where(
                TimeEntry.id == line.time_entry_id,
                TimeEntry.tenant_id == tenant_id,
            )
        )
        time_entry = te_result.scalar_one_or_none()
        if time_entry:
            time_entry.invoiced = False

    await db.delete(line)
    await db.flush()
    await db.refresh(invoice)
    await _recalculate_totals(db, invoice)
    await db.flush()


# ── Expense CRUD ─────────────────────────────────────────────────────────────


async def list_expenses(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    case_id: uuid.UUID | None = None,
    billable_only: bool = False,
    uninvoiced_only: bool = False,
) -> list[Expense]:
    """List expenses, optionally filtered."""
    query = select(Expense).where(
        Expense.tenant_id == tenant_id,
        Expense.is_active.is_(True),
    ).order_by(Expense.expense_date.desc())

    if case_id:
        query = query.where(Expense.case_id == case_id)
    if billable_only:
        query = query.where(Expense.billable.is_(True))
    if uninvoiced_only:
        query = query.where(Expense.invoiced.is_(False))

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_expense(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    expense_id: uuid.UUID,
) -> Expense:
    """Get a single expense."""
    result = await db.execute(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.tenant_id == tenant_id,
            Expense.is_active.is_(True),
        )
    )
    expense = result.scalar_one_or_none()
    if expense is None:
        raise NotFoundError("Verschot niet gevonden")
    return expense


async def create_expense(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: ExpenseCreate,
) -> Expense:
    """Create a new expense."""
    expense = Expense(
        tenant_id=tenant_id,
        **data.model_dump(),
    )
    db.add(expense)
    await db.flush()
    await db.refresh(expense)
    return expense


async def update_expense(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    expense_id: uuid.UUID,
    data: ExpenseUpdate,
) -> Expense:
    """Update an expense."""
    expense = await get_expense(db, tenant_id, expense_id)

    if expense.invoiced:
        raise BadRequestError("Gefactureerde verschotten kunnen niet worden bewerkt")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)

    await db.flush()
    await db.refresh(expense)
    return expense


async def delete_expense(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    expense_id: uuid.UUID,
) -> None:
    """Soft-delete an expense."""
    expense = await get_expense(db, tenant_id, expense_id)

    if expense.invoiced:
        raise BadRequestError("Gefactureerde verschotten kunnen niet worden verwijderd")

    expense.is_active = False
    await db.flush()


# ── LF-20/LF-21: Voorschotnota, Budget, Provisie ──────────────────────────


async def create_voorschotnota(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: VoorschotnotaCreate,
) -> Invoice:
    """Create a voorschotnota (advance invoice) with a single line."""
    invoice_number = await next_voorschotnota_number(db, tenant_id)

    invoice = Invoice(
        tenant_id=tenant_id,
        invoice_number=invoice_number,
        invoice_type="voorschotnota",
        status="concept",
        contact_id=data.contact_id,
        case_id=data.case_id,
        invoice_date=data.invoice_date,
        due_date=data.due_date,
        btw_percentage=data.btw_percentage,
        settlement_type=data.settlement_type,  # DF-13
    )
    db.add(invoice)
    await db.flush()

    # Single line with the advance amount
    description = data.description or "Voorschotnota"
    line_total = data.amount
    line = InvoiceLine(
        tenant_id=tenant_id,
        invoice_id=invoice.id,
        line_number=1,
        description=description,
        quantity=Decimal("1"),
        unit_price=data.amount,
        line_total=line_total,
    )
    db.add(line)
    await db.flush()
    await db.refresh(invoice)
    await _recalculate_totals(db, invoice)
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def get_budget_status(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> BudgetStatusResponse:
    """Calculate budget consumption from time entries + expenses.

    Uses the case's hourly_rate (or user default) to calculate amount from hours.
    """
    from app.cases.models import Case

    # Get case for budget settings
    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id)
    )
    case = case_result.scalar_one_or_none()
    if case is None:
        raise NotFoundError("Zaak niet gevonden")

    # Sum billable time entries (hours)
    te_result = await db.execute(
        select(
            func.coalesce(func.sum(TimeEntry.duration_minutes), 0)
        ).where(
            TimeEntry.tenant_id == tenant_id,
            TimeEntry.case_id == case_id,
            TimeEntry.billable.is_(True),
        )
    )
    total_minutes = te_result.scalar_one()
    used_hours = Decimal(str(total_minutes)) / Decimal("60")
    used_hours = used_hours.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Calculate amount from time entries (using per-entry rate or case rate)
    te_amount_result = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    TimeEntry.duration_minutes
                    * func.coalesce(TimeEntry.hourly_rate, Decimal("0"))
                    / 60
                ),
                Decimal("0.00"),
            )
        ).where(
            TimeEntry.tenant_id == tenant_id,
            TimeEntry.case_id == case_id,
            TimeEntry.billable.is_(True),
        )
    )
    time_amount = Decimal(str(te_amount_result.scalar_one())).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Sum billable expenses
    exp_result = await db.execute(
        select(
            func.coalesce(func.sum(Expense.amount), Decimal("0.00"))
        ).where(
            Expense.tenant_id == tenant_id,
            Expense.case_id == case_id,
            Expense.billable.is_(True),
            Expense.is_active.is_(True),
        )
    )
    expense_amount = exp_result.scalar_one()

    used_amount = (time_amount + expense_amount).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    budget_amount = Decimal(str(case.budget)) if case.budget else None
    budget_hours = Decimal(str(case.budget_hours)) if case.budget_hours else None

    # Calculate percentages
    percentage_amount = None
    percentage_hours = None

    if budget_amount and budget_amount > 0:
        percentage_amount = (
            used_amount / budget_amount * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if budget_hours and budget_hours > 0:
        percentage_hours = (
            used_hours / budget_hours * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Determine status (traffic light)
    max_pct = Decimal("0")
    if percentage_amount is not None:
        max_pct = max(max_pct, percentage_amount)
    if percentage_hours is not None:
        max_pct = max(max_pct, percentage_hours)

    if max_pct >= Decimal("90"):
        status = "red"
    elif max_pct >= Decimal("75"):
        status = "orange"
    else:
        status = "green"

    return BudgetStatusResponse(
        used_amount=used_amount,
        used_hours=used_hours,
        budget_amount=budget_amount,
        budget_hours=budget_hours,
        percentage_amount=percentage_amount,
        percentage_hours=percentage_hours,
        status=status,
    )


async def calculate_provisie(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> ProvisieCalculationResponse:
    """Calculate succesprovisie for an incasso case.

    collected_amount = sum of all payments received (from collections module)
    provisie = collected_amount * provisie_percentage / 100
    total_fee = max(provisie + fixed_case_costs, minimum_fee)
    """
    from app.cases.models import Case
    from app.collections.models import Payment

    # Get case
    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id)
    )
    case = case_result.scalar_one_or_none()
    if case is None:
        raise NotFoundError("Zaak niet gevonden")

    provisie_pct = Decimal(str(case.provisie_percentage or 0))
    fixed_costs = Decimal(str(case.fixed_case_costs or 0))
    min_fee = Decimal(str(case.minimum_fee or 0))

    # Sum all incasso payments for this case
    pay_result = await db.execute(
        select(
            func.coalesce(func.sum(Payment.amount), Decimal("0.00"))
        ).where(
            Payment.tenant_id == tenant_id,
            Payment.case_id == case_id,
        )
    )
    collected_amount = pay_result.scalar_one()

    # Calculate provisie
    provisie_amount = (
        collected_amount * provisie_pct / Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Total fee = max(provisie + fixed costs, minimum fee)
    provisie_plus_costs = provisie_amount + fixed_costs
    total_fee = max(provisie_plus_costs, min_fee)

    return ProvisieCalculationResponse(
        collected_amount=collected_amount,
        provisie_percentage=provisie_pct,
        provisie_amount=provisie_amount,
        fixed_case_costs=fixed_costs,
        minimum_fee=min_fee,
        total_fee=total_fee,
    )


# ── Re-exports from extracted modules (keep router.py working) ──────────────

from app.invoices.invoice_payment_service import (  # noqa: E402, F401
    create_invoice_payment,
    delete_invoice_payment,
    get_advance_balance,
    get_payment_summary,
    get_receivables,
    list_invoice_payments,
)
