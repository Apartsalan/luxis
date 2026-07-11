"""Cases module schemas — Pydantic models for request/response validation."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

# Valid case types and statuses
CASE_TYPES = ("incasso", "dossier", "advies")
# B3 (S198): status versimpeld tot 4 vaste waarden. De incasso-PIJPLIJN is de
# echte motor (welke stap, welke brief); de status is alleen nog een grove
# fase-indicator. De oude 8-staps-statusketen (14_dagenbrief/sommatie/… ) is
# vervangen — de pijplijn-stap bepaalt nu wat er gebeurt.
#   nieuw          — aangemaakt, nog geen stap / geen actie
#   in_behandeling — op een (niet-terminale) pijplijn-stap, loopt
#   betaald        — volledig voldaan (auto bij €0 openstaand, of handmatig)
#   afgesloten     — dossier gesloten
CASE_STATUSES = ("nieuw", "in_behandeling", "betaald", "afgesloten")
# Terminale statussen: dossier is klaar (uit de actieve wachtrijen/monitoring).
TERMINAL_STATUSES = ("betaald", "afgesloten")
INTEREST_TYPES = ("statutory", "commercial", "government", "contractual")


# ── Request Schemas ──────────────────────────────────────────────────────────


DEBTOR_TYPES = ("b2b", "b2c")


class CaseCreate(BaseModel):
    case_type: str = Field(default="incasso", description="incasso, insolventie, advies, overig")
    debtor_type: str = Field(default="b2b", description="b2b or b2c")
    description: str | None = None
    reference: str | None = None
    court_case_number: str | None = None
    court_name: str | None = None
    judge_name: str | None = None
    chamber: str | None = None
    procedure_type: str | None = None
    procedure_phase: str | None = None
    interest_type: str | None = Field(
        default=None,
        description=(
            "statutory, commercial, government, contractual. "
            "If None, inherits from the client contact's default_interest_type "
            "(falls back to 'statutory' if the client has no default)."
        ),
    )
    contractual_rate: Decimal | None = None
    contractual_compound: bool = True
    client_id: uuid.UUID
    opposing_party_id: uuid.UUID | None = None
    billing_contact_id: uuid.UUID | None = None
    contact_terms_id: uuid.UUID | None = None  # S140: AV-versie keuze (optioneel)
    assigned_to_id: uuid.UUID | None = None
    date_opened: date
    budget: Decimal | None = None  # G13: optional budget (requires "budget" module)
    bik_override: Decimal | None = None  # LF-12: manual BIK override
    bik_override_percentage: Decimal | None = None  # DF117-04: BIK as % of principal
    nakosten_type: str | None = None  # AUD124-03: zonder_betekening / met_betekening
    hourly_rate: Decimal | None = None  # LF-19: per-case hourly rate
    payment_term_days: int | None = None  # LF-22: debtor settings
    collection_strategy: str | None = None
    debtor_notes: str | None = None
    # LF-20/LF-21: Billing settings
    billing_method: str = Field(default="hourly", description="hourly | fixed_price | budget_cap")
    fixed_price_amount: Decimal | None = None
    budget_hours: Decimal | None = None
    provisie_percentage: Decimal | None = None
    fixed_case_costs: Decimal | None = None
    minimum_fee: Decimal | None = None
    bik_minimum_fee: Decimal | None = None
    provisie_base: str = Field(
        default="collected_amount",
        description="collected_amount | total_claim",
    )


class CaseUpdate(BaseModel):
    debtor_type: str | None = None
    description: str | None = None
    reference: str | None = None
    court_case_number: str | None = None
    court_name: str | None = None
    judge_name: str | None = None
    chamber: str | None = None
    procedure_type: str | None = None
    procedure_phase: str | None = None
    interest_type: str | None = None
    contractual_rate: Decimal | None = None
    contractual_compound: bool | None = None
    opposing_party_id: uuid.UUID | None = None
    billing_contact_id: uuid.UUID | None = None
    contact_terms_id: uuid.UUID | None = None  # S140
    assigned_to_id: uuid.UUID | None = None
    budget: Decimal | None = None  # G13
    bik_override: Decimal | None = None  # LF-12
    bik_override_percentage: Decimal | None = None  # DF117-04
    nakosten_type: str | None = None  # AUD124-03
    hourly_rate: Decimal | None = None  # LF-19
    payment_term_days: int | None = None  # LF-22
    collection_strategy: str | None = None
    debtor_notes: str | None = None
    # LF-20/LF-21: Billing settings
    billing_method: str | None = None
    fixed_price_amount: Decimal | None = None
    budget_hours: Decimal | None = None
    provisie_percentage: Decimal | None = None
    fixed_case_costs: Decimal | None = None
    minimum_fee: Decimal | None = None
    bik_minimum_fee: Decimal | None = None
    provisie_base: str | None = None  # "collected_amount" or "total_claim"
    # DF2-09: Pipeline step assignment from case detail. The former
    # incasso_step_entered_at field was not a mapped column (a silent no-op) and
    # was removed; step_entered_at is owned by move_case_to_step (audit #97).
    incasso_step_id: uuid.UUID | None = None
    # Verweer
    has_verweer: bool | None = None
    verweer_note: str | None = None
    verweer_date: date | None = None


class CaseStatusUpdate(BaseModel):
    new_status: str
    note: str | None = None


# ── Afwikkelflow (FIN-2) ────────────────────────────────────────────────────

SETTLEMENT_ROUTES = ("verrekenen", "doorbetalen")


class SettlementRouteUpdate(BaseModel):
    """Kies (of wis) de afwikkelroute voor een dossier."""

    route: str | None = Field(
        default=None, description="'verrekenen', 'doorbetalen' of null om te wissen"
    )

    @field_validator("route")
    @classmethod
    def _check_route(cls, v: str | None) -> str | None:
        if v is not None and v not in SETTLEMENT_ROUTES:
            raise ValueError(
                f"Ongeldige route: {v}. Kies uit: {', '.join(SETTLEMENT_ROUTES)}"
            )
        return v


class SettlementInvoice(BaseModel):
    id: uuid.UUID
    invoice_number: str
    status: str
    total: Decimal
    outstanding: Decimal


class SettlementTransaction(BaseModel):
    """Een geboekte/lopende verrekening of uitbetaling op het dossier."""

    id: uuid.UUID
    transaction_type: str  # disbursement | offset_to_invoice
    amount: Decimal
    status: str  # pending_approval | approved | rejected
    transaction_date: date
    beneficiary_name: str | None = None


class CaseSettlementResponse(BaseModel):
    """Afgeleide afwikkelstaat van een dossier — enkel lezen/rekenen, geen boekingen."""

    case_id: uuid.UUID
    settlement_route: str | None
    total_balance: Decimal
    available: Decimal
    pending_disbursements: Decimal
    suggested_payout: Decimal  # het bedrag dat nu aan de client uitbetaald kan worden
    unsettled_reason: str | None  # waarom afsluiten (nog) geblokkeerd is; null = klaar
    invoices: list[SettlementInvoice] = []
    offsets: list[SettlementTransaction] = []
    disbursements: list[SettlementTransaction] = []


class CasePartyCreate(BaseModel):
    contact_id: uuid.UUID
    role: str = Field(..., min_length=1, max_length=50)
    external_reference: str | None = None


class CaseActivityCreate(BaseModel):
    activity_type: str = Field(
        ..., description="status_change, note, phone_call, email, document, payment"
    )
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


# ── Response Schemas ─────────────────────────────────────────────────────────


class ContactBrief(BaseModel):
    """Minimal contact info for embedding in case responses."""

    id: uuid.UUID
    contact_type: str
    name: str
    email: str | None

    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    """Minimal user info for embedding in case responses."""

    id: uuid.UUID
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class CasePartyResponse(BaseModel):
    id: uuid.UUID
    contact_id: uuid.UUID
    role: str
    external_reference: str | None
    contact: ContactBrief
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseActivityResponse(BaseModel):
    id: uuid.UUID
    activity_type: str
    title: str
    description: str | None
    old_status: str | None
    new_status: str | None
    user: UserBrief | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    case_number: str
    case_type: str
    debtor_type: str
    status: str
    description: str | None
    reference: str | None
    court_case_number: str | None
    court_name: str | None
    judge_name: str | None
    chamber: str | None
    procedure_type: str | None
    procedure_phase: str | None
    interest_type: str
    contractual_rate: Decimal | None
    contractual_compound: bool
    client: ContactBrief
    opposing_party: ContactBrief | None
    billing_contact: ContactBrief | None
    assigned_to: UserBrief | None
    contact_terms_id: uuid.UUID | None = None  # S140
    incasso_step_id: uuid.UUID | None = None
    date_opened: date
    date_closed: date | None
    total_principal: Decimal
    total_paid: Decimal
    budget: Decimal | None = None  # G13
    bik_override: Decimal | None = None  # LF-12
    bik_override_percentage: Decimal | None = None  # DF117-04
    nakosten_type: str | None = None  # AUD124-03
    hourly_rate: Decimal | None = None  # LF-19
    payment_term_days: int | None = None  # LF-22
    collection_strategy: str | None = None
    debtor_notes: str | None = None
    # LF-20/LF-21
    billing_method: str = "hourly"
    fixed_price_amount: Decimal | None = None
    budget_hours: Decimal | None = None
    provisie_percentage: Decimal | None = None
    fixed_case_costs: Decimal | None = None
    minimum_fee: Decimal | None = None
    bik_minimum_fee: Decimal | None = None
    provisie_base: str = "collected_amount"
    has_verweer: bool = False
    verweer_note: str | None = None
    verweer_date: date | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseSummary(BaseModel):
    """Lightweight case for lists."""

    id: uuid.UUID
    case_number: str
    case_type: str
    debtor_type: str
    status: str
    description: str | None
    reference: str | None
    incasso_step_id: uuid.UUID | None = None
    client: ContactBrief
    opposing_party: ContactBrief | None
    date_opened: date
    total_principal: Decimal
    total_paid: Decimal
    budget: Decimal | None = None  # G13
    billing_method: str = "hourly"  # LF-20/LF-21

    model_config = {"from_attributes": True}


class CaseDetailResponse(CaseResponse):
    """Full case detail with parties and recent activities."""

    parties: list[CasePartyResponse] = []
    recent_activities: list[CaseActivityResponse] = []
    # B2 — basisdatum verjaring (verzuimdatum oudste vordering, terugval
    # openingsdatum) + de server-berekende verjaringsdatum zelf. De badge toont
    # de server-datum: JS-jaarrekenwerk wijkt af rond 29 februari
    # (Codex-review portie 2).
    verjaring_basis_date: date | None = None
    verjaring_date: date | None = None


# ── CaseFile Schemas (E4: Document uploads) ─────────────────────────────────

ALLOWED_FILE_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg",
    "image/png",
    "image/gif",
    "text/plain",
    "message/rfc822",  # .eml
    "application/vnd.ms-outlook",  # .msg
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".txt",
    ".eml",
    ".msg",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

DOCUMENT_DIRECTIONS = ("inkomend", "uitgaand")


class CaseFileResponse(BaseModel):
    """Response schema for an uploaded case file."""

    id: uuid.UUID
    case_id: uuid.UUID
    original_filename: str
    file_size: int
    content_type: str
    document_direction: str | None
    description: str | None
    uploaded_by: uuid.UUID
    uploader_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseEmailAttachmentResponse(BaseModel):
    """Email attachment linked to a case via synced email."""

    id: uuid.UUID
    filename: str
    file_size: int
    content_type: str
    email_subject: str | None = None
    email_date: str | None = None
    email_from: str | None = None
    synced_email_id: uuid.UUID
