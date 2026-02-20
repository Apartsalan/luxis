"""Cases module schemas — Pydantic models for request/response validation."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

# Valid case types and statuses
CASE_TYPES = ("incasso", "insolventie", "advies", "overig")
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
    interest_type: str = Field(
        default="statutory",
        description="statutory, commercial, government, contractual",
    )
    contractual_rate: float | None = None
    contractual_compound: bool = True
    client_id: uuid.UUID
    opposing_party_id: uuid.UUID | None = None
    assigned_to_id: uuid.UUID | None = None
    date_opened: date


class CaseUpdate(BaseModel):
    debtor_type: str | None = None
    description: str | None = None
    reference: str | None = None
    interest_type: str | None = None
    contractual_rate: float | None = None
    contractual_compound: bool | None = None
    opposing_party_id: uuid.UUID | None = None
    assigned_to_id: uuid.UUID | None = None


class CaseStatusUpdate(BaseModel):
    new_status: str
    note: str | None = None


class CasePartyCreate(BaseModel):
    contact_id: uuid.UUID
    role: str = Field(..., min_length=1, max_length=50)


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
    interest_type: str
    contractual_rate: float | None
    contractual_compound: bool
    client: ContactBrief
    opposing_party: ContactBrief | None
    assigned_to: UserBrief | None
    date_opened: date
    date_closed: date | None
    total_principal: float
    total_paid: float
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
    client: ContactBrief
    opposing_party: ContactBrief | None
    date_opened: date
    total_principal: float
    total_paid: float

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
