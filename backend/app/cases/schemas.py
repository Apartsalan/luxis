"""Cases module schemas — Pydantic models for request/response validation."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

# Valid case types and statuses
CASE_TYPES = ("incasso", "dossier", "advies")
CASE_STATUSES = (
    "nieuw",
    "14_dagenbrief",
    "sommatie",
    "dagvaarding",
    "vonnis",
    "executie",
    "betaald",
    "afgesloten",
)
INTEREST_TYPES = ("statutory", "commercial", "government", "contractual")

# Status workflow — defines allowed transitions
STATUS_TRANSITIONS: dict[str, list[str]] = {
    "nieuw": ["14_dagenbrief", "sommatie", "afgesloten"],
    "14_dagenbrief": ["sommatie", "betaald", "afgesloten"],
    "sommatie": ["dagvaarding", "betaald", "afgesloten"],
    "dagvaarding": ["vonnis", "betaald", "afgesloten"],
    "vonnis": ["executie", "betaald", "afgesloten"],
    "executie": ["betaald", "afgesloten"],
    "betaald": ["afgesloten"],
    "afgesloten": [],  # Terminal state
}


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
    interest_type: str = Field(
        default="statutory",
        description="statutory, commercial, government, contractual",
    )
    contractual_rate: Decimal | None = None
    contractual_compound: bool = True
    client_id: uuid.UUID
    opposing_party_id: uuid.UUID | None = None
    billing_contact_id: uuid.UUID | None = None
    assigned_to_id: uuid.UUID | None = None
    date_opened: date
    budget: Decimal | None = None  # G13: optional budget (requires "budget" module)
    bik_override: Decimal | None = None  # LF-12: manual BIK override
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
    provisie_base: str = Field(default="collected_amount", description="collected_amount | total_claim")


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
    assigned_to_id: uuid.UUID | None = None
    budget: Decimal | None = None  # G13
    bik_override: Decimal | None = None  # LF-12
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
    provisie_base: str | None = None  # "collected_amount" or "total_claim"


class CaseStatusUpdate(BaseModel):
    new_status: str
    note: str | None = None


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
    incasso_step_id: uuid.UUID | None = None
    date_opened: date
    date_closed: date | None
    total_principal: Decimal
    total_paid: Decimal
    budget: Decimal | None = None  # G13
    bik_override: Decimal | None = None  # LF-12
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
    provisie_base: str = "collected_amount"
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
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".jpg", ".jpeg", ".png", ".gif",
    ".txt", ".eml", ".msg",
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
