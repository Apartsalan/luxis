"""Payment matching schemas — request/response models."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

# ── Bank Transaction ─────────────────────────────────────────────────────


class BankTransactionOut(BaseModel):
    """Response schema for a bank transaction."""

    id: uuid.UUID
    import_id: uuid.UUID
    transaction_date: date
    amount: Decimal
    counterparty_name: str | None = None
    counterparty_iban: str | None = None
    description: str | None = None
    currency: str
    entry_date: date | None = None
    is_matched: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Import ───────────────────────────────────────────────────────────────


class BankStatementImportOut(BaseModel):
    """Response schema for a bank statement import."""

    id: uuid.UUID
    filename: str
    bank: str
    account_iban: str | None = None
    status: str
    error_message: str | None = None
    total_rows: int
    credit_count: int
    debit_count: int
    skipped_count: int
    matched_count: int
    imported_by_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BankStatementImportList(BaseModel):
    """Paginated list of bank statement imports."""

    items: list[BankStatementImportOut]
    total: int
    page: int
    per_page: int


# ── Payment Match ────────────────────────────────────────────────────────


class PaymentMatchOut(BaseModel):
    """Response schema for a payment match."""

    id: uuid.UUID
    transaction_id: uuid.UUID
    case_id: uuid.UUID

    # Transaction info (denormalized for display)
    transaction_date: date
    amount: Decimal
    counterparty_name: str | None = None
    counterparty_iban: str | None = None
    description: str | None = None

    # Case info
    case_number: str
    client_name: str | None = None
    opposing_party_name: str | None = None

    # Match details
    match_method: str
    match_method_label: str
    confidence: int
    match_details: str | None = None

    # Review
    status: str
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None

    # Execution
    executed_at: datetime | None = None
    payment_id: uuid.UUID | None = None
    derdengelden_id: uuid.UUID | None = None

    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentMatchList(BaseModel):
    """Paginated list of payment matches."""

    items: list[PaymentMatchOut]
    total: int
    page: int
    per_page: int


class PaymentMatchStatsOut(BaseModel):
    """Counts per match status."""

    pending: int = 0
    approved: int = 0
    rejected: int = 0
    executed: int = 0
    total_amount_pending: Decimal = Decimal("0.00")


class MatchRejectIn(BaseModel):
    """Request body for rejecting a match."""

    note: str | None = None


class ManualMatchIn(BaseModel):
    """Request body for manually matching a transaction to a case."""

    transaction_id: uuid.UUID
    case_id: uuid.UUID
    note: str | None = None
