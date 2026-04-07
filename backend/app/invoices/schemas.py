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
    btw_percentage: Decimal | None = Field(default=None, ge=0)
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
    btw_percentage: Decimal
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
    lines: list[InvoiceLineCreate] = Field(default_factory=list, min_length=1)


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
    settlement_type: str | None = None  # DF-13: tussentijds | bij_sluiting
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
    payment_method: str = Field(..., description="bank, ideal, cash, verrekening")
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


# ── LF-20/LF-21: Voorschotnota, Budget, Provisie Schemas ────────────────────


BILLING_METHODS = ("hourly", "fixed_price", "budget_cap")


class VoorschotnotaCreate(BaseModel):
    """Create a voorschotnota (advance invoice)."""

    case_id: uuid.UUID
    contact_id: uuid.UUID
    amount: Decimal = Field(..., gt=Decimal("0"), decimal_places=2)
    description: str | None = None
    invoice_date: date
    due_date: date
    btw_percentage: Decimal = Field(default=Decimal("21.00"), ge=0)
    # DF-13: When is the advance offset against invoices?
    settlement_type: str = Field(
        default="tussentijds",
        description="tussentijds (per invoice) or bij_sluiting (at case closure)",
    )


class AdvanceBalanceResponse(BaseModel):
    """Voorschot saldo for a case."""

    case_id: uuid.UUID
    total_advance: Decimal  # Total paid voorschotnota's
    total_offset: Decimal  # Verrekende bedragen
    available_balance: Decimal  # Beschikbaar saldo


class BudgetStatusResponse(BaseModel):
    """Budget voortgang for a case."""

    used_amount: Decimal  # Totaal besteed (uren * tarief + onkosten)
    used_hours: Decimal  # Totaal geschreven uren
    budget_amount: Decimal | None  # Budget limiet in euro's
    budget_hours: Decimal | None  # Budget limiet in uren
    percentage_amount: Decimal | None  # % verbruikt van budget bedrag
    percentage_hours: Decimal | None  # % verbruikt van budget uren
    status: str  # green | orange | red


class ProvisieCalculationResponse(BaseModel):
    """Succesprovisie berekening for an incasso case."""

    collected_amount: Decimal  # Totaal geïnd
    provisie_percentage: Decimal  # Afgesproken percentage
    provisie_amount: Decimal  # Berekende provisie
    fixed_case_costs: Decimal  # Vaste dossierkosten
    minimum_fee: Decimal  # Minimumkosten
    total_fee: Decimal  # Uiteindelijk honorarium (max van provisie, minimum)


class IncassoBIKPreview(BaseModel):
    amount: Decimal
    is_override: bool
    source: str


class IncassoInterestPreview(BaseModel):
    amount: Decimal
    calc_date: str
    source: str


class IncassoProvisieOption(BaseModel):
    base_amount: Decimal
    amount: Decimal  # Final amount including fixed_costs and minimum_fee
    raw_amount: Decimal | None = None  # base_amount * percentage (before costs/min)
    is_minimum_applied: bool = False  # True if minimum_fee forced this amount higher


class IncassoProvisiePreview(BaseModel):
    percentage: Decimal
    base: str  # "collected_amount" or "total_claim"
    over_collected: IncassoProvisieOption
    over_claim: IncassoProvisieOption
    fixed_costs: Decimal
    minimum_fee: Decimal


class AlreadyInvoicedInfo(BaseModel):
    has_bik_line: bool
    has_provisie_line: bool
    has_rente_line: bool
    invoices: list[str]  # invoice numbers


class IncassoInvoicePreviewResponse(BaseModel):
    bik: IncassoBIKPreview
    interest: IncassoInterestPreview
    principal: Decimal
    collected_amount: Decimal
    provisie: IncassoProvisiePreview
    already_invoiced: AlreadyInvoicedInfo


class ExpenseCreate(BaseModel):
    case_id: uuid.UUID | None = None
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    expense_date: date
    category: str = Field(default="overig")
    billable: bool = True
    tax_type: str = Field(default="belast", description="belast, onbelast, vrijgesteld")
    file_id: uuid.UUID | None = None


class ExpenseUpdate(BaseModel):
    description: str | None = Field(None, min_length=1, max_length=500)
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    expense_date: date | None = None
    category: str | None = None
    billable: bool | None = None
    tax_type: str | None = None
    file_id: uuid.UUID | None = None


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID | None
    description: str
    amount: Decimal
    expense_date: date
    category: str
    billable: bool
    invoiced: bool
    tax_type: str
    file_id: uuid.UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
