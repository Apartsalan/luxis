"""Invoices module endpoints — Invoices, Lines, Payments, and Expenses."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.invoices import service
from app.invoices.schemas import (
    AdvanceBalanceResponse,
    BudgetStatusResponse,
    CreditNoteCreate,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    IncassoInvoicePreviewResponse,
    InvoiceCreate,
    InvoiceLineCreate,
    InvoiceLineResponse,
    InvoicePaymentCreate,
    InvoicePaymentRead,
    InvoicePaymentSummary,
    InvoiceResponse,
    InvoiceUpdate,
    PaginatedInvoices,
    ProvisieCalculationResponse,
    ReceivablesSummary,
    VoorschotnotaCreate,
)
from app.shared.sanitize import content_disposition

router = APIRouter(prefix="/api/invoices", tags=["invoices"])
expenses_router = APIRouter(prefix="/api/expenses", tags=["expenses"])

# ── Invoice CRUD ─────────────────────────────────────────────────────────────


@router.get("", response_model=PaginatedInvoices)
async def list_invoices(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    case_id: uuid.UUID | None = Query(default=None),
    contact_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List invoices with pagination and optional filters."""
    return await service.list_invoices(
        db,
        current_user.tenant_id,
        page=page,
        per_page=per_page,
        status=status,
        search=search,
        case_id=case_id,
        contact_id=contact_id,
    )


@router.get("/receivables", response_model=ReceivablesSummary)
async def get_receivables(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aging receivables overview (debiteurenoverzicht)."""
    return await service.get_receivables(db, current_user.tenant_id)


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_invoice(
    data: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new invoice."""
    invoice = await service.create_invoice(db, current_user.tenant_id, data)
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single invoice with all lines."""
    return await service.get_invoice(db, current_user.tenant_id, invoice_id)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    data: InvoiceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an invoice (concept only)."""
    return await service.update_invoice(db, current_user.tenant_id, invoice_id, data)


@router.delete(
    "/{invoice_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_invoice(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete an invoice (concept/cancelled only)."""
    await service.delete_invoice(db, current_user.tenant_id, invoice_id)


# ── Credit Notes ─────────────────────────────────────────────────────────────


@router.post(
    "/credit-note",
    response_model=InvoiceResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_credit_note(
    data: CreditNoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a credit note linked to an existing invoice."""
    return await service.create_credit_note(db, current_user.tenant_id, data)


# ── Voorschotnota ───────────────────────────────────────────────────────────


@router.post(
    "/voorschotnota",
    response_model=InvoiceResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_voorschotnota(
    data: VoorschotnotaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a voorschotnota (advance invoice)."""
    invoice = await service.create_voorschotnota(db, current_user.tenant_id, data)
    await db.commit()
    await db.refresh(invoice)
    return invoice


# ── Case Financial Endpoints (LF-20/LF-21) ─────────────────────────────────

cases_billing_router = APIRouter(prefix="/api/cases", tags=["cases-billing"])


@cases_billing_router.get(
    "/{case_id}/advance-balance",
    response_model=AdvanceBalanceResponse,
)
async def get_advance_balance(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get advance balance (voorschot saldo) for a case."""
    return await service.get_advance_balance(db, current_user.tenant_id, case_id)


@cases_billing_router.get(
    "/{case_id}/budget-status",
    response_model=BudgetStatusResponse,
)
async def get_budget_status(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get budget consumption status for a case."""
    return await service.get_budget_status(db, current_user.tenant_id, case_id)


@cases_billing_router.get(
    "/{case_id}/provisie",
    response_model=ProvisieCalculationResponse,
)
async def get_provisie(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calculate succesprovisie for an incasso case."""
    return await service.calculate_provisie(db, current_user.tenant_id, case_id)


@cases_billing_router.get(
    "/{case_id}/incasso-invoice-preview",
    response_model=IncassoInvoicePreviewResponse,
)
async def get_incasso_invoice_preview(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview all incasso cost items for invoice creation.

    Returns pre-calculated BIK, interest, and provisie amounts plus
    already-invoiced detection to prevent accidental double-billing.
    """
    return await service.get_incasso_invoice_preview(db, current_user.tenant_id, case_id)


# ── Status Transitions ───────────────────────────────────────────────────────


@router.post("/{invoice_id}/approve", response_model=InvoiceResponse)
async def approve_invoice(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a concept invoice."""
    return await service.approve_invoice(db, current_user.tenant_id, invoice_id)


@router.post("/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an invoice as sent."""
    return await service.send_invoice(db, current_user.tenant_id, invoice_id)


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceResponse)
async def mark_paid(
    invoice_id: uuid.UUID,
    paid_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an invoice as paid."""
    return await service.mark_paid(db, current_user.tenant_id, invoice_id, paid_date)


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
async def cancel_invoice(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an invoice."""
    return await service.cancel_invoice(db, current_user.tenant_id, invoice_id)


# ── Invoice Lines ────────────────────────────────────────────────────────────


@router.post(
    "/{invoice_id}/lines",
    response_model=InvoiceLineResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def add_line(
    invoice_id: uuid.UUID,
    data: InvoiceLineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a line to a concept invoice."""
    return await service.add_line(
        db,
        current_user.tenant_id,
        invoice_id,
        description=data.description,
        quantity=data.quantity,
        unit_price=data.unit_price,
        btw_percentage=data.btw_percentage,  # None = inherit from invoice
        time_entry_id=data.time_entry_id,
        expense_id=data.expense_id,
    )


@router.delete(
    "/{invoice_id}/lines/{line_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def remove_line(
    invoice_id: uuid.UUID,
    line_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a line from a concept invoice."""
    await service.remove_line(db, current_user.tenant_id, invoice_id, line_id)


# ── Invoice Payments ─────────────────────────────────────────────────────────


@router.post(
    "/{invoice_id}/payments",
    response_model=InvoicePaymentRead,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_payment(
    invoice_id: uuid.UUID,
    data: InvoicePaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a payment against an invoice."""
    return await service.create_invoice_payment(
        db, current_user.tenant_id, invoice_id, current_user.id, data
    )


@router.get(
    "/{invoice_id}/payments",
    response_model=list[InvoicePaymentRead],
)
async def list_payments(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all payments for an invoice."""
    return await service.list_invoice_payments(db, current_user.tenant_id, invoice_id)


@router.delete(
    "/{invoice_id}/payments/{payment_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_payment(
    invoice_id: uuid.UUID,
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a payment from an invoice."""
    await service.delete_invoice_payment(db, current_user.tenant_id, invoice_id, payment_id)


@router.get(
    "/{invoice_id}/payment-summary",
    response_model=InvoicePaymentSummary,
)
async def get_payment_summary(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get payment summary for an invoice (total paid, outstanding)."""
    return await service.get_payment_summary(db, current_user.tenant_id, invoice_id)


# ── Invoice PDF ──────────────────────────────────────────────────────────────


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download invoice as PDF."""
    invoice = await service.get_invoice(db, current_user.tenant_id, invoice_id)

    from app.invoices.invoice_pdf_service import render_invoice_pdf

    pdf_bytes, filename = await render_invoice_pdf(db, current_user.tenant_id, invoice)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": content_disposition("attachment", filename)},
    )


# ── Expenses ─────────────────────────────────────────────────────────────────


@expenses_router.get("", response_model=list[ExpenseResponse])
async def list_expenses(
    case_id: uuid.UUID | None = Query(default=None),
    billable_only: bool = Query(default=False),
    uninvoiced_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List expenses with optional filters."""
    return await service.list_expenses(
        db,
        current_user.tenant_id,
        case_id=case_id,
        billable_only=billable_only,
        uninvoiced_only=uninvoiced_only,
    )


@expenses_router.post(
    "",
    response_model=ExpenseResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_expense(
    data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new expense."""
    return await service.create_expense(db, current_user.tenant_id, data)


@expenses_router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single expense."""
    return await service.get_expense(db, current_user.tenant_id, expense_id)


@expenses_router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: uuid.UUID,
    data: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an expense."""
    return await service.update_expense(db, current_user.tenant_id, expense_id, data)


@expenses_router.delete(
    "/{expense_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_expense(
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete an expense."""
    await service.delete_expense(db, current_user.tenant_id, expense_id)
