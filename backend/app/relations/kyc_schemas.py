"""WWFT/KYC schemas — Request and response models for KYC verification."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

# ── Request Schemas ──────────────────────────────────────────────────────────


class KycCreate(BaseModel):
    """Create or update a KYC verification for a contact."""

    contact_id: uuid.UUID

    # Risk
    risk_level: str | None = Field(
        None, pattern="^(laag|midden|hoog)$"
    )
    risk_notes: str | None = None

    # ID document
    id_type: str | None = Field(
        None,
        pattern="^(paspoort|id_kaart|rijbewijs|verblijfsdocument|kvk_uittreksel|anders)$",
    )
    id_number: str | None = None
    id_expiry_date: date | None = None
    id_verified_at: date | None = None

    # UBO (for companies)
    ubo_name: str | None = None
    ubo_dob: date | None = None
    ubo_nationality: str | None = None
    ubo_percentage: str | None = None
    ubo_verified_at: date | None = None

    # PEP
    pep_checked: bool = False
    pep_is_pep: bool = False
    pep_notes: str | None = None

    # Sanctions
    sanctions_checked: bool = False
    sanctions_hit: bool = False
    sanctions_notes: str | None = None

    # Source of funds
    source_of_funds: str | None = None
    source_of_funds_verified: bool = False

    # Review
    next_review_date: date | None = None

    # Notes
    notes: str | None = None


class KycUpdate(BaseModel):
    """Partial update of a KYC verification."""

    risk_level: str | None = Field(
        None, pattern="^(laag|midden|hoog)$"
    )
    risk_notes: str | None = None

    id_type: str | None = Field(
        None,
        pattern="^(paspoort|id_kaart|rijbewijs|verblijfsdocument|kvk_uittreksel|anders)$",
    )
    id_number: str | None = None
    id_expiry_date: date | None = None
    id_verified_at: date | None = None

    ubo_name: str | None = None
    ubo_dob: date | None = None
    ubo_nationality: str | None = None
    ubo_percentage: str | None = None
    ubo_verified_at: date | None = None

    pep_checked: bool | None = None
    pep_is_pep: bool | None = None
    pep_notes: str | None = None

    sanctions_checked: bool | None = None
    sanctions_hit: bool | None = None
    sanctions_notes: str | None = None

    source_of_funds: str | None = None
    source_of_funds_verified: bool | None = None

    next_review_date: date | None = None
    notes: str | None = None


class KycComplete(BaseModel):
    """Mark a KYC verification as complete."""

    notes: str | None = None


# ── Response Schemas ─────────────────────────────────────────────────────────


class VerifiedByBrief(BaseModel):
    """Brief user reference for verified_by."""

    id: uuid.UUID
    full_name: str

    model_config = {"from_attributes": True}


class KycResponse(BaseModel):
    """Full KYC verification record."""

    id: uuid.UUID
    contact_id: uuid.UUID
    status: str
    risk_level: str | None
    risk_notes: str | None

    # ID
    id_type: str | None
    id_number: str | None
    id_expiry_date: date | None
    id_verified_at: date | None

    # UBO
    ubo_name: str | None
    ubo_dob: date | None
    ubo_nationality: str | None
    ubo_percentage: str | None
    ubo_verified_at: date | None

    # PEP
    pep_checked: bool
    pep_is_pep: bool
    pep_notes: str | None

    # Sanctions
    sanctions_checked: bool
    sanctions_hit: bool
    sanctions_notes: str | None

    # Source of funds
    source_of_funds: str | None
    source_of_funds_verified: bool

    # Metadata
    verified_by: VerifiedByBrief | None = None
    verification_date: date | None
    next_review_date: date | None
    notes: str | None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KycSummary(BaseModel):
    """Lightweight KYC status for lists and badges."""

    id: uuid.UUID
    contact_id: uuid.UUID
    status: str
    risk_level: str | None
    verification_date: date | None
    next_review_date: date | None

    model_config = {"from_attributes": True}


class KycDashboardItem(BaseModel):
    """Dashboard item for KYC warnings."""

    contact_id: uuid.UUID
    contact_name: str
    contact_type: str
    kyc_status: str
    risk_level: str | None
    next_review_date: date | None
    days_until_review: int | None
    is_overdue: bool
