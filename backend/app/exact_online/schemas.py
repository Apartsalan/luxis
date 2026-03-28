"""Exact Online Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


# ── OAuth / Connection ───────────────────────────────────────────────────────


class ExactAuthorizeResponse(BaseModel):
    authorize_url: str


class ExactConnectionStatus(BaseModel):
    connected: bool
    division_name: str | None = None
    connected_email: str | None = None
    connected_at: str | None = None
    last_sync_at: str | None = None
    sales_journal_code: str | None = None
    bank_journal_code: str | None = None
    default_revenue_gl: str | None = None
    default_expense_gl: str | None = None


class ExactDisconnectResponse(BaseModel):
    success: bool
    message: str


# ── Settings ─────────────────────────────────────────────────────────────────


class ExactSettingsUpdate(BaseModel):
    sales_journal_code: str | None = None
    bank_journal_code: str | None = None
    default_revenue_gl: str | None = None
    default_expense_gl: str | None = None


class ExactSettingsResponse(BaseModel):
    success: bool
    message: str


# ── Setup data (journals, GL accounts, VAT codes) ───────────────────────────


class ExactJournal(BaseModel):
    code: str
    description: str


class ExactGLAccount(BaseModel):
    id: str
    code: str
    description: str


class ExactVATCode(BaseModel):
    code: str
    description: str
    percentage: float


class ExactSetupData(BaseModel):
    journals: list[ExactJournal]
    gl_accounts: list[ExactGLAccount]
    vat_codes: list[ExactVATCode]


# ── Sync ─────────────────────────────────────────────────────────────────────


class SyncResult(BaseModel):
    success: bool
    message: str
    synced_contacts: int = 0
    synced_invoices: int = 0
    synced_payments: int = 0
    errors: list[str] = []


class InvoiceSyncResult(BaseModel):
    success: bool
    message: str
    exact_id: str | None = None


class SyncLogEntry(BaseModel):
    entity_type: str
    entity_id: str
    exact_id: str
    exact_number: str | None = None
    sync_status: str
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
