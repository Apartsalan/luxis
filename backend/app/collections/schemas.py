"""Collections module schemas — Pydantic models for claims, payments, etc."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

# ── Claim Schemas ────────────────────────────────────────────────────────────


RATE_BASES = ("monthly", "yearly")


class ClaimCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    principal_amount: Decimal = Field(..., gt=0, decimal_places=2)
    default_date: date
    invoice_number: str | None = None
    invoice_date: date | None = None
    rate_basis: str = Field(default="yearly", description="monthly or yearly")


class ClaimUpdate(BaseModel):
    description: str | None = Field(None, min_length=1, max_length=500)
    principal_amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    default_date: date | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    rate_basis: str | None = None


class ClaimResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    description: str
    principal_amount: Decimal
    default_date: date
    invoice_number: str | None
    invoice_date: date | None
    rate_basis: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Payment Schemas ──────────────────────────────────────────────────────────


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_date: date
    description: str | None = None
    payment_method: str | None = None


class PaymentUpdate(BaseModel):
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    payment_date: date | None = None
    description: str | None = None
    payment_method: str | None = None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    amount: Decimal
    payment_date: date
    description: str | None
    payment_method: str | None
    allocated_to_costs: Decimal
    allocated_to_interest: Decimal
    allocated_to_principal: Decimal
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Payment Arrangement Schemas ──────────────────────────────────────────────


class ArrangementCreate(BaseModel):
    total_amount: Decimal = Field(..., gt=0, decimal_places=2)
    installment_amount: Decimal = Field(..., gt=0, decimal_places=2)
    frequency: str = Field(default="monthly", pattern="^(weekly|monthly|quarterly)$")
    start_date: date
    notes: str | None = None


class ArrangementUpdate(BaseModel):
    status: str | None = Field(None, pattern="^(active|completed|defaulted)$")
    notes: str | None = None


class ArrangementResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    total_amount: Decimal
    installment_amount: Decimal
    frequency: str
    start_date: date
    end_date: date | None
    status: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Derdengelden Schemas ─────────────────────────────────────────────────────


class DerdengeldenCreate(BaseModel):
    transaction_type: str = Field(..., pattern="^(deposit|withdrawal)$")
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    transaction_date: date
    description: str | None = None
    counterparty: str | None = None


class DerdengeldenResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    transaction_type: str
    amount: Decimal
    transaction_date: date
    description: str | None
    counterparty: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DerdengeldenBalance(BaseModel):
    total_deposits: Decimal
    total_withdrawals: Decimal
    balance: Decimal


# ── Interest Rate Schemas ────────────────────────────────────────────────────


class InterestRateResponse(BaseModel):
    id: uuid.UUID
    rate_type: str
    effective_from: date
    rate: Decimal
    source: str | None

    model_config = {"from_attributes": True}


# ── Interest Calculation Schemas ─────────────────────────────────────────────


class InterestPeriod(BaseModel):
    """A single period in an interest calculation."""

    start_date: date
    end_date: date
    days: int
    rate: Decimal
    principal: Decimal  # Principal at the start of this period
    interest: Decimal  # Interest accrued in this period


class ClaimInterest(BaseModel):
    """Interest calculation result for a single claim."""

    claim_id: uuid.UUID
    description: str
    principal_amount: Decimal
    default_date: date
    total_interest: Decimal
    periods: list[InterestPeriod]


class CaseInterestSummary(BaseModel):
    """Full interest calculation for a case."""

    case_id: uuid.UUID
    calculation_date: date
    interest_type: str
    total_principal: Decimal
    total_interest: Decimal
    total_outstanding: Decimal  # principal + interest - payments
    claims: list[ClaimInterest]


# ── Financial Summary ────────────────────────────────────────────────────────


class FinancialSummary(BaseModel):
    """Complete financial overview for a case."""

    case_id: uuid.UUID
    calculation_date: date

    # Principal
    total_principal: Decimal
    total_paid_principal: Decimal
    remaining_principal: Decimal

    # Interest
    total_interest: Decimal
    total_paid_interest: Decimal
    remaining_interest: Decimal

    # Costs (BIK)
    bik_amount: Decimal
    bik_btw: Decimal
    total_bik: Decimal
    total_paid_costs: Decimal
    remaining_costs: Decimal

    # Totals
    grand_total: Decimal  # principal + interest + costs
    total_paid: Decimal
    total_outstanding: Decimal  # grand_total - total_paid

    # Derdengelden
    derdengelden_balance: Decimal
