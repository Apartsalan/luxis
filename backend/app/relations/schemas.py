"""Relations module schemas — Pydantic models for request/response validation."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

# ── Request Schemas ──────────────────────────────────────────────────────────


class ContactCreate(BaseModel):
    contact_type: str = Field(
        ..., pattern="^(company|person)$", description="'company' or 'person'"
    )
    name: str = Field(..., min_length=1, max_length=255)
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    email: str | None = None
    phone: str | None = None
    kvk_number: str | None = None
    btw_number: str | None = None
    visit_address: str | None = None
    visit_postcode: str | None = None
    visit_city: str | None = None
    postal_address: str | None = None
    postal_postcode: str | None = None
    postal_city: str | None = None
    default_hourly_rate: float | None = None
    payment_term_days: int | None = None
    billing_email: str | None = None
    iban: str | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    email: str | None = None
    phone: str | None = None
    kvk_number: str | None = None
    btw_number: str | None = None
    visit_address: str | None = None
    visit_postcode: str | None = None
    visit_city: str | None = None
    postal_address: str | None = None
    postal_postcode: str | None = None
    postal_city: str | None = None
    default_hourly_rate: float | None = None
    payment_term_days: int | None = None
    billing_email: str | None = None
    iban: str | None = None
    notes: str | None = None


class ContactLinkCreate(BaseModel):
    person_id: uuid.UUID
    company_id: uuid.UUID
    role_at_company: str | None = None


class ConflictCheckRequest(BaseModel):
    search_query: str = Field(..., min_length=1, max_length=500)
    case_id: uuid.UUID | None = None


# ── Response Schemas ─────────────────────────────────────────────────────────


class ContactResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    contact_type: str
    name: str
    first_name: str | None
    last_name: str | None
    date_of_birth: date | None
    email: str | None
    phone: str | None
    kvk_number: str | None
    btw_number: str | None
    visit_address: str | None
    visit_postcode: str | None
    visit_city: str | None
    postal_address: str | None
    postal_postcode: str | None
    postal_city: str | None
    default_hourly_rate: float | None
    payment_term_days: int | None
    billing_email: str | None
    iban: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContactSummary(BaseModel):
    """Lightweight contact for lists and references."""

    id: uuid.UUID
    contact_type: str
    name: str
    email: str | None
    phone: str | None
    kvk_number: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class ContactLinkResponse(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    company_id: uuid.UUID
    role_at_company: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LinkedContactInfo(BaseModel):
    """Contact summary with link metadata (link_id, role)."""

    link_id: uuid.UUID
    role_at_company: str | None
    contact: ContactSummary


class ContactDetailResponse(ContactResponse):
    """Full contact detail, including linked companies/persons."""

    linked_companies: list[LinkedContactInfo] = []
    linked_persons: list[LinkedContactInfo] = []


class ConflictCheckResult(BaseModel):
    search_query: str
    results_found: int
    matches: list[ContactSummary]
