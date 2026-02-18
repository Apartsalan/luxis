"""Invoices module service — CRUD, auto-numbering, status workflow, totals."""

import math
import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.invoices.models import Expense, Invoice, InvoiceLine
from app.invoices.schemas import (
    ExpenseCreate,
    ExpenseUpdate,
    InvoiceCreate,
    InvoiceUpdate,
)
from app.shared.exceptions import BadRequestError, NotFoundError

# ── Invoice Number Generation ────────────────────────────────────────────────


async def _next_invoice_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate the next invoice number: F{year}-{seq:05d}."""
    year = date.today().year
    prefix = f"F{year}-"

    result = await db.execute(
        select(func.count())
        .select_from(Invoice)
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.invoice_number.like(f"{prefix}%"),
        )
    )
    count = result.scalar_one()
    return f"{prefix}{count + 1:05d}"


# ── Invoice Totals ───────────────────────────────────────────────────────────


def _recalculate_totals(invoice: Invoice) -> None:
    """Recalculate subtotal, BTW, and total from lines."""
    subtotal = Decimal("0")
    for line in invoice.lines:
        subtotal += line.line_total

    invoice.subtotal = subtotal
    invoice.btw_amount = (
        subtotal * invoice.btw_percentage / Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    invoice.total = invoice.subtotal + invoice.btw_amount


# ── Status Workflow ──────────────────────────────────────────────────────────

VALID_TRANSITIONS = {
    "concept": {"approved", "cancelled"},
    "approved": {"sent", "cancelled"},
    "sent": {"paid", "overdue", "cancelled"},
    "overdue": {"paid", "cancelled"},
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
) -> dict:
    """List invoices with pagination, optional status filter and search."""
    query = (
        select(Invoice)
        .where(Invoice.tenant_id == tenant_id, Invoice.is_active.is_(True))
        .order_by(Invoice.invoice_date.desc(), Invoice.invoice_number.desc())
    )

    count_query = (
        select(func.count())
        .select_from(Invoice)
        .where(Invoice.tenant_id == tenant_id, Invoice.is_active.is_(True))
    )

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
            "status": inv.status,
            "contact_id": inv.contact_id,
            "contact_name": inv.contact.name if inv.contact else None,
            "case_id": inv.case_id,
            "case_number": inv.case.case_number if inv.case else None,
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
        select(Invoice).where(
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
    invoice_number = await _next_invoice_number(db, tenant_id)

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

    _recalculate_totals(invoice)
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
        _recalculate_totals(invoice)

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
    """Mark an invoice as paid."""
    invoice = await get_invoice(db, tenant_id, invoice_id)
    _validate_transition(invoice.status, "paid")
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
    max_line = max((l.line_number for l in invoice.lines), default=0)

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
    _recalculate_totals(invoice)
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

    await db.delete(line)
    await db.flush()
    await db.refresh(invoice)
    _recalculate_totals(invoice)
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
