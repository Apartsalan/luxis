"""Relations module schemas — Pydantic models for request/response validation."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.shared.validators import (
    optional,
    validate_btw,
    validate_email,
    validate_iban,
    validate_kvk,
)

InterestType = Literal["statutory", "commercial", "government", "contractual"]
Salutation = Literal["mr", "mrs", "unknown"]

# ── Request Schemas ──────────────────────────────────────────────────────────


class ContactFieldValidators(BaseModel):
    """Normalise + validate Dutch business identifiers (audit #66).

    Shared by ContactCreate and ContactUpdate. ``check_fields=False`` because
    the validated fields are declared on the subclasses, not on this mixin.
    Empty/blank values are mapped to NULL so the fields stay optional.
    """

    @field_validator("email", "billing_email", check_fields=False)
    @classmethod
    def _validate_email(cls, v: str | None) -> str | None:
        return optional(v, validate_email)

    @field_validator("kvk_number", check_fields=False)
    @classmethod
    def _validate_kvk(cls, v: str | None) -> str | None:
        return optional(v, validate_kvk)

    @field_validator("btw_number", check_fields=False)
    @classmethod
    def _validate_btw(cls, v: str | None) -> str | None:
        return optional(v, validate_btw)

    @field_validator("iban", check_fields=False)
    @classmethod
    def _validate_iban(cls, v: str | None) -> str | None:
        return optional(v, validate_iban)


class ContactCreate(ContactFieldValidators):
    contact_type: str = Field(
        ..., pattern="^(company|person)$", description="'company' or 'person'"
    )
    name: str = Field(..., min_length=1, max_length=255)
    contact_person: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    salutation: Salutation = "unknown"
    date_of_birth: date | None = None
    email: str | None = None
    phone: str | None = None
    kvk_number: str | None = None
    btw_number: str | None = None
    visit_address: str | None = None
    visit_postcode: str | None = None
    visit_city: str | None = None
    visit_country: str | None = None
    postal_address: str | None = None
    postal_postcode: str | None = None
    postal_city: str | None = None
    postal_country: str | None = None
    default_hourly_rate: Decimal | None = None
    payment_term_days: int | None = None
    billing_email: str | None = None
    iban: str | None = None
    default_interest_type: InterestType | None = None
    default_contractual_rate: Decimal | None = None
    default_rate_basis: str | None = Field(default=None, pattern="^(yearly|monthly)$")
    default_bik_override: Decimal | None = None
    default_bik_override_percentage: Decimal | None = None
    default_minimum_fee: Decimal | None = None
    default_bik_minimum_fee: Decimal | None = None
    default_provisie_percentage: Decimal | None = None
    is_btw_plichtig: bool = True
    notes: str | None = None


class ContactUpdate(ContactFieldValidators):
    name: str | None = Field(None, min_length=1, max_length=255)
    contact_person: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    salutation: Salutation | None = None
    date_of_birth: date | None = None
    email: str | None = None
    phone: str | None = None
    kvk_number: str | None = None
    btw_number: str | None = None
    visit_address: str | None = None
    visit_postcode: str | None = None
    visit_city: str | None = None
    visit_country: str | None = None
    postal_address: str | None = None
    postal_postcode: str | None = None
    postal_city: str | None = None
    postal_country: str | None = None
    default_hourly_rate: Decimal | None = None
    payment_term_days: int | None = None
    billing_email: str | None = None
    iban: str | None = None
    default_interest_type: InterestType | None = None
    default_contractual_rate: Decimal | None = None
    default_rate_basis: str | None = Field(default=None, pattern="^(yearly|monthly)$")
    default_bik_override: Decimal | None = None
    default_bik_override_percentage: Decimal | None = None
    default_minimum_fee: Decimal | None = None
    default_bik_minimum_fee: Decimal | None = None
    default_provisie_percentage: Decimal | None = None
    is_btw_plichtig: bool | None = None
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
    contact_person: str | None
    first_name: str | None
    last_name: str | None
    salutation: str = "unknown"
    date_of_birth: date | None
    email: str | None
    phone: str | None
    kvk_number: str | None
    btw_number: str | None
    visit_address: str | None
    visit_postcode: str | None
    visit_city: str | None
    visit_country: str | None = None
    postal_address: str | None
    postal_postcode: str | None
    postal_city: str | None
    postal_country: str | None = None
    default_hourly_rate: float | None
    payment_term_days: int | None
    billing_email: str | None
    iban: str | None
    default_interest_type: str | None = None
    default_contractual_rate: float | None = None
    default_rate_basis: str | None = None
    default_bik_override: float | None = None
    default_bik_override_percentage: float | None = None
    default_minimum_fee: float | None = None
    default_bik_minimum_fee: float | None = None
    default_provisie_percentage: float | None = None
    is_btw_plichtig: bool = True
    terms_file_name: str | None = None
    # S177: rente zoals gelezen uit de AV van de cliënt (read-only, zichtbare herkomst).
    terms_interest_rate: float | None = None
    terms_interest_basis: str | None = None
    terms_interest_compound: bool | None = None
    terms_interest_source: str | None = None
    terms_interest_read_at: datetime | None = None
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
    visit_city: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ContactLinkResponse(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    company_id: uuid.UUID
    role_at_company: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ContactTermsResponse(BaseModel):
    """Versie-row van algemene voorwaarden op een cliënt."""

    id: uuid.UUID
    contact_id: uuid.UUID
    file_name: str
    label: str | None
    valid_from: date | None
    valid_to: date | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ContactTermsCreate(BaseModel):
    """Metadata bij upload van nieuwe AV-versie (file komt via multipart)."""

    label: str | None = Field(default=None, max_length=100)
    valid_from: date | None = None
    valid_to: date | None = None


class ContactTermsUpdate(BaseModel):
    """Bewerk metadata van bestaande AV-versie (file niet wijzigbaar)."""

    label: str | None = Field(default=None, max_length=100)
    valid_from: date | None = None
    valid_to: date | None = None


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
