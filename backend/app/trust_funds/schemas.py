"""Trust funds module schemas — Pydantic models for request/response validation."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

TRANSACTION_TYPES = ("deposit", "disbursement", "offset_to_invoice")
TRANSACTION_STATUSES = ("pending_approval", "approved", "rejected")
CONSENT_METHODS = ("email", "document", "mondeling", "anders")


# ── Request Schemas ──────────────────────────────────────────────────────────


class TrustTransactionCreate(BaseModel):
    transaction_type: str = Field(
        ..., description="deposit, disbursement, or offset_to_invoice"
    )
    amount: Decimal = Field(..., gt=Decimal("0"), decimal_places=2)
    transaction_date: date | None = Field(
        default=None, description="Date the funds moved (defaults to today)"
    )
    description: str = Field(..., min_length=3)
    payment_method: str | None = Field(default=None, description="bank, ideal, cash")
    reference: str | None = None
    beneficiary_name: str | None = None
    beneficiary_iban: str | None = None


class TrustOffsetCreate(BaseModel):
    """Verrekening: offset trust balance against own invoice (Voda art. 6.19 lid 5).

    Requires explicit per-transaction client consent — a general clause in the
    engagement letter is NOT sufficient (tuchtrecht: ECLI:NL:TAHVD:2023:38).
    """

    amount: Decimal = Field(..., gt=Decimal("0"), decimal_places=2)
    transaction_date: date | None = Field(default=None)
    description: str = Field(..., min_length=3)
    target_invoice_id: uuid.UUID
    consent_received_at: date
    consent_method: str = Field(..., description="email, document, mondeling, anders")
    consent_note: str = Field(..., min_length=3, description="Toelichting op de toestemming")
    consent_document_url: str | None = None

    @field_validator("consent_method")
    @classmethod
    def _check_method(cls, v: str) -> str:
        if v not in CONSENT_METHODS:
            raise ValueError(
                f"Ongeldige consent_method: {v}. Kies uit: {', '.join(CONSENT_METHODS)}"
            )
        return v

    @model_validator(mode="after")
    def _evidence_required(self) -> "TrustOffsetCreate":
        if not (self.consent_note and self.consent_note.strip()) and not (
            self.consent_document_url and self.consent_document_url.strip()
        ):
            raise ValueError(
                "Verrekening vereist consent_note of consent_document_url als bewijs"
            )
        return self


class TrustTransactionApprove(BaseModel):
    """Empty body — the approver is derived from the authenticated user."""

    pass


class EligibleInvoice(BaseModel):
    """An open invoice eligible for trust offset."""

    id: uuid.UUID
    invoice_number: str
    invoice_date: date
    due_date: date
    total: Decimal
    paid: Decimal
    outstanding: Decimal
    status: str
    case_id: uuid.UUID | None = None
    case_number: str | None = None


# ── Response Schemas ─────────────────────────────────────────────────────────


class UserBrief(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class ContactBrief(BaseModel):
    id: uuid.UUID
    contact_type: str
    name: str
    email: str | None

    model_config = {"from_attributes": True}


class CaseBrief(BaseModel):
    id: uuid.UUID
    case_number: str
    description: str | None

    model_config = {"from_attributes": True}


class InvoiceBrief(BaseModel):
    id: uuid.UUID
    invoice_number: str
    total: Decimal
    status: str

    model_config = {"from_attributes": True}


class TrustTransactionRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    case_id: uuid.UUID
    contact_id: uuid.UUID
    transaction_type: str
    amount: Decimal
    transaction_date: date
    description: str
    payment_method: str | None
    reference: str | None
    beneficiary_name: str | None
    beneficiary_iban: str | None
    target_invoice_id: uuid.UUID | None
    consent_received_at: date | None
    consent_method: str | None
    consent_document_url: str | None
    consent_note: str | None
    reversed_by_id: uuid.UUID | None
    status: str
    approved_by_1: uuid.UUID | None
    approved_at_1: datetime | None
    approved_by_2: uuid.UUID | None
    approved_at_2: datetime | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Nested relations
    case: CaseBrief
    contact: ContactBrief
    target_invoice: InvoiceBrief | None = None
    creator: UserBrief
    approver_1: UserBrief | None
    approver_2: UserBrief | None

    model_config = {"from_attributes": True}


class TrustBalanceSummary(BaseModel):
    """Balance summary for a case's trust fund account."""

    case_id: uuid.UUID
    total_deposits: Decimal
    total_disbursements: Decimal
    total_balance: Decimal
    pending_disbursements: Decimal
    available: Decimal  # total_balance - pending_disbursements
