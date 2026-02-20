"""Invoices module schemas — Pydantic models for invoices, lines, payments, and expenses."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

# ── Brief models (used in responses) ─────────────────────────────────────────


class ContactBrief(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class CaseBrief(BaseModel):
    id: uuid.UUID
    case_number: str

    model_config = {"from_attributes": True}


# ── Invoice Line Schemas ─────────────────────────────────────────────────────


class InvoiceLineCreate(BaseModel):
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_price: Decimal = Field(..., decimal_places=2)
    time_entry_id: uuid.UUID | None = None
    expense_id: uuid.UUID | None = None


class InvoiceLineResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    line_number: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    time_entry_id: uuid.UUID | None
    expense_id: uuid.UUID | None

    model_config = {"from_attributes": True}


# ── Invoice Schemas ──────────────────────────────────────────────────────────


class InvoiceCreate(BaseModel):
    contact_id: uuid.UUID
    case_id: uuid.UUID | None = None
    invoice_date: date
    due_date: date
    btw_percentage: Decimal = Field(default=Decimal("21.00"), ge=0)
    reference: str | None = None
    notes: str | None = None
    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class CreditNoteCreate(BaseModel):
    """Create a credit note linked to an existing invoice."""

    linked_invoice_id: uuid.UUID
    invoice_date: date
    due_date: date
    btw_percentage: Decimal = Field(default=Decimal("21.00"), ge=0)
    reference: str | None = None
    notes: str | None = None
    lines: list["InvoiceLineCreate"] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    contact_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    btw_percentage: Decimal | None = Field(None, ge=0)
    reference: str | None = None
    notes: str | None = None


class CreditNoteBrief(BaseModel):
    """Lightweight credit note reference."""

    id: uuid.UUID
    invoice_number: str
    status: str
    total: Decimal
    invoice_date: date

    model_config = {"from_attributes": True}


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    invoice_type: str = "invoice"
    status: str
    contact_id: uuid.UUID
    case_id: uuid.UUID | None
    linked_invoice_id: uuid.UUID | None = None
    invoice_date: date
    due_date: date
    paid_date: date | None
    subtotal: Decimal
    btw_percentage: Decimal
    btw_amount: Decimal
    total: Decimal
    reference: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    contact: ContactBrief | None = None
    case: CaseBrief | None = None
    lines: list[InvoiceLineResponse] = []
    credit_notes: list[CreditNoteBrief] = []

    model_config = {"from_attributes": True}


class InvoiceSummary(BaseModel):
    """Lightweight invoice for list views."""

    id: uuid.UUID
    invoice_number: str
    invoice_type: str = "invoice"
    status: str
    contact_id: uuid.UUID
    contact_name: str | None = None
    case_id: uuid.UUID | None
    case_number: str | None = None
    linked_invoice_id: uuid.UUID | None = None
    linked_invoice_number: str | None = None
    invoice_date: date
    due_date: date
    subtotal: Decimal
    btw_amount: Decimal
    total: Decimal
    created_at: datetime


class PaginatedInvoices(BaseModel):
    items: list[InvoiceSummary]
    total: int
    page: int
    per_page: int
    pages: int


# ── Invoice Payment Schemas ───────────────────────────────────────────────────


class UserBrief(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class InvoicePaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0"), decimal_places=2)
    payment_date: date
    payment_method: str = Field(
        ..., description="bank, ideal, cash, verrekening"
    )
    reference: str | None = None
    description: str | None = None


class InvoicePaymentRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    invoice_id: uuid.UUID
    amount: Decimal
    payment_date: date
    payment_method: str
    reference: str | None
    description: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    creator: UserBrief

    model_config = {"from_attributes": True}


class InvoicePaymentSummary(BaseModel):
    """Payment summary for an invoice: total paid, outstanding amount."""

    invoice_id: uuid.UUID
    invoice_total: Decimal
    total_paid: Decimal
    outstanding: Decimal
    payment_count: int
    is_fully_paid: bool


# ── Aging / Receivables Schemas ──────────────────────────────────────────────


class AgingBucket(BaseModel):
    """Outstanding invoices in a single aging bucket."""

    count: int = 0
    total: Decimal = Decimal("0")


class ContactReceivable(BaseModel):
    """Outstanding receivables grouped by contact."""

    contact_id: uuid.UUID
    contact_name: str
    invoice_count: int
    total_outstanding: Decimal
    current: AgingBucket  # 0-30 days
    days_31_60: AgingBucket
    days_61_90: AgingBucket
    days_90_plus: AgingBucket
    oldest_due_date: date


class ReceivablesSummary(BaseModel):
    """Aggregated receivables overview (debiteurenoverzicht)."""

    total_outstanding: Decimal
    total_overdue: Decimal
    current: AgingBucket
    days_31_60: AgingBucket
    days_61_90: AgingBucket
    days_90_plus: AgingBucket
    contacts: list[ContactReceivable]


# ── Expense Schemas ──────────────────────────────────────────────────────────


class ExpenseCreate(BaseModel):
    case_id: uuid.UUID | None = None
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    expense_date: date
    category: str = Field(default="overig")
    billable: bool = True


class ExpenseUpdate(BaseModel):
    description: str | None = Field(None, min_length=1, max_length=500)
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    expense_date: date | None = None
    category: str | None = None
    billable: bool | None = None


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID | None
    description: str
    amount: Decimal
    expense_date: date
    category: str
    billable: bool
    invoiced: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
