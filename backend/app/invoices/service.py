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
    """Recalculate subtotal, BTW, and total from per-line VAT (DF2-03).

    BTW is calculated per rate group (Dutch tax law), not per individual line.
    """
    # Group lines by btw_percentage and sum line_totals per group
    result = await db.execute(
        select(
            InvoiceLine.btw_percentage,
            func.coalesce(func.sum(InvoiceLine.line_total), Decimal("0.00")),
        )
        .where(InvoiceLine.invoice_id == invoice.id)
        .group_by(InvoiceLine.btw_percentage)
    )
    groups = result.all()

    subtotal = Decimal("0.00")
    btw_total = Decimal("0.00")
    for btw_pct, group_total in groups:
        subtotal += group_total
        btw_total += (group_total * btw_pct / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    invoice.subtotal = subtotal
    invoice.btw_amount = btw_total
    invoice.total = subtotal + btw_total


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
        raise BadRequestError(f"Ongeldige statuswijziging: {current} → {new}")


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
    contact_id: uuid.UUID | None = None,
) -> dict:
    """List invoices with pagination, optional status filter and search.

    Search now matches against invoice_number, the linked case's case_number,
    and the linked contact's name (DF117-12).
    """
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

    if contact_id:
        query = query.where(Invoice.contact_id == contact_id)
        count_query = count_query.where(Invoice.contact_id == contact_id)

    if status:
        # Accept either a single status or a comma-separated list
        # (bijv. "sent,partially_paid,overdue" voor openstaande facturen)
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        if len(statuses) == 1:
            query = query.where(Invoice.status == statuses[0])
            count_query = count_query.where(Invoice.status == statuses[0])
        elif len(statuses) > 1:
            query = query.where(Invoice.status.in_(statuses))
            count_query = count_query.where(Invoice.status.in_(statuses))

    if search:
        pattern = f"%{search}%"
        # Match invoice_number OR case.case_number OR contact.name
        from sqlalchemy import or_
        from app.cases.models import Case
        from app.relations.models import Contact
        search_filter = or_(
            Invoice.invoice_number.ilike(pattern),
            Invoice.case_id.in_(
                select(Case.id).where(
                    Case.tenant_id == tenant_id,
                    Case.case_number.ilike(pattern),
                )
            ),
            Invoice.contact_id.in_(
                select(Contact.id).where(
                    Contact.tenant_id == tenant_id,
                    Contact.name.ilike(pattern),
                )
            ),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar_one()
    pages = max(1, math.ceil(total / per_page))

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    invoices = list(result.scalars().all())

    items = []
    for inv in invoices:
        items.append(
            {
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
                    inv.linked_invoice.invoice_number if inv.linked_invoice else None
                ),
                "invoice_date": inv.invoice_date,
                "due_date": inv.due_date,
                "subtotal": inv.subtotal,
                "btw_amount": inv.btw_amount,
                "total": inv.total,
                "created_at": inv.created_at,
            }
        )

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
        # Lines inherit invoice-level btw_percentage when not explicitly set
        line_btw = line_data.btw_percentage if line_data.btw_percentage is not None else data.btw_percentage
        line = InvoiceLine(
            tenant_id=tenant_id,
            invoice_id=invoice.id,
            line_number=i,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            line_total=line_total,
            btw_percentage=line_btw,
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
        raise BadRequestError("Alleen concept- of geannuleerde facturen kunnen worden verwijderd")

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

    # Add lines.
    # DF117-17 (Lisanne demo 2026-04-07): credit note line_totals are ALWAYS forced
    # to be negative so they offset the original invoice in dossier-level totals.
    # The frontend dialog mirrors the original invoice lines with positive amounts;
    # accepting that and silently producing positive credit-note totals was the
    # source of Lisanne's "het wordt niet afgehaald" complaint.
    for i, line_data in enumerate(data.lines, start=1):
        raw_line_total = (line_data.quantity * line_data.unit_price).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        # Force negative regardless of input sign (handles both positive and
        # negative input from clients — old API contract used negative
        # unit_price, new frontend dialog uses positive)
        line_total = -abs(raw_line_total)
        # Keep the displayed unit_price negative as well so detail screens are honest
        signed_unit_price = -abs(line_data.unit_price)
        line_btw = line_data.btw_percentage if line_data.btw_percentage is not None else data.btw_percentage
        line = InvoiceLine(
            tenant_id=tenant_id,
            invoice_id=credit_note.id,
            line_number=i,
            description=line_data.description,
            quantity=line_data.quantity,
            unit_price=signed_unit_price,
            line_total=line_total,
            btw_percentage=line_btw,
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
    user_id: uuid.UUID | None = None,
    *,
    skip_email: bool = False,
) -> Invoice:
    """Send an invoice: render to PDF, email it via the connected provider
    (Outlook/Gmail) or SMTP fallback, then mark the invoice as sent.

    Lisanne demo 2026-04-07 (DF117-13): the previous implementation only flipped
    the status to "sent" without actually emailing anything — we now actually
    deliver the PDF to the customer's billing email.

    Args:
        db: Database session.
        tenant_id: Tenant scope.
        invoice_id: Invoice to send.
        user_id: The lawyer triggering the send (used for OAuth account lookup).
            When None (e.g. internal calls / legacy callers), email is skipped.
        skip_email: When True, only the status is updated. Used for tests and
            for cases where the lawyer explicitly opts out of emailing.

    Returns:
        The updated Invoice (status="sent").

    Raises:
        BadRequestError: If the invoice can't transition to "sent" or has no
            recipient email address.
    """
    invoice = await get_invoice(db, tenant_id, invoice_id)
    _validate_transition(invoice.status, "sent")

    if not skip_email and user_id is not None:
        # Determine recipient email: prefer billing_email, fall back to contact.email
        contact = invoice.contact
        if contact is None:
            raise BadRequestError("Factuur heeft geen gekoppelde relatie")
        recipient = (contact.billing_email or contact.email or "").strip()
        if not recipient:
            raise BadRequestError(
                f"Geen e-mailadres bekend voor {contact.name}. "
                "Stel een e-mailadres in op de relatie of vul billing_email."
            )

        # Render PDF
        from app.invoices.invoice_pdf_service import render_invoice_pdf

        pdf_bytes, pdf_filename = await render_invoice_pdf(db, tenant_id, invoice)

        # Build subject + body
        subject = f"Factuur {invoice.invoice_number}"
        recipient_label = contact.name or recipient
        body_html = _build_invoice_email_body(invoice, recipient_label)

        # Send via unified send service (provider-first, SMTP fallback)
        from app.email.send_service import send_with_attachment

        email_log = await send_with_attachment(
            db,
            user_id,
            tenant_id,
            to=recipient,
            subject=subject,
            body_html=body_html,
            attachments=[(pdf_filename, pdf_bytes, "pdf")],
            case_id=invoice.case_id,
            recipient_name=recipient_label,
        )
        if email_log.status != "sent":
            raise BadRequestError(
                f"Verzenden mislukt: {email_log.error_message or 'onbekende fout'}"
            )

    invoice.status = "sent"
    await db.flush()
    await db.refresh(invoice)
    return invoice


def _build_invoice_email_body(invoice: Invoice, recipient_name: str) -> str:
    """Build a friendly Dutch HTML body for the invoice email."""
    from app.documents.docx_service import _fmt_currency, _fmt_date

    return f"""\
<p>Geachte {recipient_name},</p>

<p>In de bijlage treft u factuur <strong>{invoice.invoice_number}</strong> aan
ten bedrage van <strong>{_fmt_currency(invoice.total)}</strong>, met als
vervaldatum {_fmt_date(invoice.due_date)}.</p>

<p>Wij verzoeken u vriendelijk het bedrag voor de vervaldatum over te maken
onder vermelding van het factuurnummer.</p>

<p>Heeft u vragen over deze factuur? Neem gerust contact met ons op.</p>

<p>Met vriendelijke groet,<br>
Kesting Legal</p>
"""


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
    btw_percentage: Decimal | None = None,
    time_entry_id: uuid.UUID | None = None,
    expense_id: uuid.UUID | None = None,
) -> InvoiceLine:
    """Add a line to a concept invoice."""
    invoice = await get_invoice(db, tenant_id, invoice_id)

    if invoice.status != "concept":
        raise BadRequestError("Regels kunnen alleen aan conceptfacturen worden toegevoegd")

    # Inherit invoice-level btw_percentage when not explicitly set
    if btw_percentage is None:
        btw_percentage = invoice.btw_percentage

    # Determine next line number
    max_line = max((line.line_number for line in invoice.lines), default=0)

    line_total = (quantity * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    line = InvoiceLine(
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        line_number=max_line + 1,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        line_total=line_total,
        btw_percentage=btw_percentage,
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
    query = (
        select(Expense)
        .where(
            Expense.tenant_id == tenant_id,
            Expense.is_active.is_(True),
        )
        .order_by(Expense.expense_date.desc())
    )

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
        btw_percentage=data.btw_percentage,
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
        select(func.coalesce(func.sum(TimeEntry.duration_minutes), 0)).where(
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
        select(func.coalesce(func.sum(Expense.amount), Decimal("0.00"))).where(
            Expense.tenant_id == tenant_id,
            Expense.case_id == case_id,
            Expense.billable.is_(True),
            Expense.is_active.is_(True),
        )
    )
    expense_amount = exp_result.scalar_one()

    used_amount = (time_amount + expense_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    budget_amount = Decimal(str(case.budget)) if case.budget else None
    budget_hours = Decimal(str(case.budget_hours)) if case.budget_hours else None

    # Calculate percentages
    percentage_amount = None
    percentage_hours = None

    if budget_amount and budget_amount > 0:
        percentage_amount = (used_amount / budget_amount * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    if budget_hours and budget_hours > 0:
        percentage_hours = (used_hours / budget_hours * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

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
        select(func.coalesce(func.sum(Payment.amount), Decimal("0.00"))).where(
            Payment.tenant_id == tenant_id,
            Payment.case_id == case_id,
        )
    )
    collected_amount = pay_result.scalar_one()

    # Calculate provisie
    provisie_amount = (collected_amount * provisie_pct / Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

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


async def get_incasso_invoice_preview(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> dict:
    """Build a preview of all incasso cost items for invoice creation.

    Combines BIK, interest, and provisie calculations with already-invoiced
    detection to help users create incasso invoices without double-billing.
    """
    from app.cases.models import Case
    from app.collections.models import Claim, Payment
    from app.collections.wik import calculate_bik
    from app.invoices.models import Invoice, InvoiceLine

    # Get case
    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id)
    )
    case = case_result.scalar_one_or_none()
    if case is None:
        raise NotFoundError("Zaak niet gevonden")

    # Total principal (from claims)
    claims_result = await db.execute(
        select(func.coalesce(func.sum(Claim.principal_amount), Decimal("0.00"))).where(
            Claim.tenant_id == tenant_id,
            Claim.case_id == case_id,
        )
    )
    total_principal = claims_result.scalar_one()

    # Collected amount (from payments)
    pay_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), Decimal("0.00"))).where(
            Payment.tenant_id == tenant_id,
            Payment.case_id == case_id,
        )
    )
    collected_amount = pay_result.scalar_one()

    # BIK calculation
    # DF117-04: Three modes — percentage of principal (highest precedence),
    # fixed override, or default WIK-staffel.
    if case.bik_override_percentage is not None:
        bik_pct = Decimal(str(case.bik_override_percentage))
        bik_amount = (total_principal * bik_pct / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        bik_is_override = True
        bik_source = f"{bik_pct}% van hoofdsom (€ {total_principal:,.2f})".replace(",", ".")
    elif case.bik_override is not None:
        bik_amount = case.bik_override
        bik_is_override = True
        bik_source = "Handmatig ingesteld"
    else:
        bik_result = calculate_bik(total_principal)
        bik_amount = bik_result["bik_exclusive"]
        bik_is_override = False
        bik_source = f"WIK-staffel over € {total_principal:,.2f}".replace(",", ".")

    # Interest calculation
    from app.collections.service import get_financial_summary

    fin_summary = await get_financial_summary(
        db,
        tenant_id,
        case_id,
        interest_type=case.interest_type,
        contractual_rate=case.contractual_rate,
        contractual_compound=case.contractual_compound,
        bik_override=case.bik_override,
    )
    interest_amount = Decimal(str(fin_summary.get("total_interest", 0)))
    today_str = date.today().isoformat()

    # Provisie calculation (both bases)
    provisie_pct = Decimal(str(case.provisie_percentage or 0))
    fixed_costs = Decimal(str(case.fixed_case_costs or 0))
    min_fee = Decimal(str(case.minimum_fee or 0))
    provisie_base = case.provisie_base or "collected_amount"

    prov_over_collected_raw = (
        (collected_amount * provisie_pct / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if collected_amount > 0
        else Decimal("0.00")
    )

    prov_over_claim_raw = (
        (total_principal * provisie_pct / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if total_principal > 0
        else Decimal("0.00")
    )

    # DF117-09 (Lisanne demo 2026-04-07): apply minimum_fee to the final amounts
    # so callers don't have to do max() themselves and can read off whether the
    # minimum was the binding constraint.
    prov_over_collected_with_costs = prov_over_collected_raw + fixed_costs
    prov_over_claim_with_costs = prov_over_claim_raw + fixed_costs

    prov_over_collected = max(prov_over_collected_with_costs, min_fee)
    prov_over_claim = max(prov_over_claim_with_costs, min_fee)

    over_collected_min_applied = (
        min_fee > 0 and prov_over_collected_with_costs < min_fee
    )
    over_claim_min_applied = (
        min_fee > 0 and prov_over_claim_with_costs < min_fee
    )

    # Already invoiced detection
    already_result = await db.execute(
        select(InvoiceLine.description, Invoice.invoice_number)
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .where(
            Invoice.tenant_id == tenant_id,
            Invoice.case_id == case_id,
            Invoice.status != "cancelled",
        )
    )
    existing_lines = already_result.all()

    has_bik = False
    has_provisie = False
    has_rente = False
    invoice_numbers = set()
    for desc, inv_num in existing_lines:
        desc_lower = (desc or "").lower()
        if "incassokosten" in desc_lower or "bik" in desc_lower:
            has_bik = True
            invoice_numbers.add(inv_num)
        if "provisie" in desc_lower:
            has_provisie = True
            invoice_numbers.add(inv_num)
        if "rente" in desc_lower:
            has_rente = True
            invoice_numbers.add(inv_num)

    return {
        "bik": {
            "amount": bik_amount,
            "is_override": bik_is_override,
            "source": bik_source,
        },
        "interest": {
            "amount": interest_amount,
            "calc_date": today_str,
            "source": f"Samengestelde rente t/m {today_str}",
        },
        "principal": total_principal,
        "collected_amount": collected_amount,
        "provisie": {
            "percentage": provisie_pct,
            "base": provisie_base,
            "over_collected": {
                "base_amount": collected_amount,
                "amount": prov_over_collected,
                "raw_amount": prov_over_collected_raw,
                "is_minimum_applied": over_collected_min_applied,
            },
            "over_claim": {
                "base_amount": total_principal,
                "amount": prov_over_claim,
                "raw_amount": prov_over_claim_raw,
                "is_minimum_applied": over_claim_min_applied,
            },
            "fixed_costs": fixed_costs,
            "minimum_fee": min_fee,
        },
        "already_invoiced": {
            "has_bik_line": has_bik,
            "has_provisie_line": has_provisie,
            "has_rente_line": has_rente,
            "invoices": sorted(invoice_numbers),
        },
    }


# ── Re-exports from extracted modules (keep router.py working) ──────────────

from app.invoices.invoice_payment_service import (  # noqa: E402, F401
    create_invoice_payment,
    delete_invoice_payment,
    get_advance_balance,
    get_payment_summary,
    get_receivables,
    list_invoice_payments,
)
