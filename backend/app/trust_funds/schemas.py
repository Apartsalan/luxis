"""Trust funds module schemas — Pydantic models for request/response validation."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

TRANSACTION_TYPES = ("deposit", "disbursement")
TRANSACTION_STATUSES = ("pending_approval", "approved", "rejected")


# ── Request Schemas ──────────────────────────────────────────────────────────


class TrustTransactionCreate(BaseModel):
    transaction_type: str = Field(..., description="deposit or disbursement")
    amount: Decimal = Field(..., gt=Decimal("0"), decimal_places=2)
    description: str = Field(..., min_length=3)
    payment_method: str | None = Field(default=None, description="bank, ideal, cash")
    reference: str | None = None
    beneficiary_name: str | None = None
    beneficiary_iban: str | None = None


class TrustTransactionApprove(BaseModel):
    """Empty body — the approver is derived from the authenticated user."""

    pass


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


class TrustTransactionRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    case_id: uuid.UUID
    contact_id: uuid.UUID
    transaction_type: str
    amount: Decimal
    description: str
    payment_method: str | None
    reference: str | None
    beneficiary_name: str | None
    beneficiary_iban: str | None
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
