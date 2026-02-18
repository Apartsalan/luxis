"""Time entries module schemas — Pydantic models for time tracking CRUD."""

import uuid
from datetime import date as DateType
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

ACTIVITY_TYPE_LABELS = {
    "correspondence": "Correspondentie",
    "meeting": "Bespreking",
    "phone": "Telefonisch",
    "research": "Onderzoek",
    "court": "Zitting",
    "travel": "Reistijd",
    "drafting": "Opstellen stukken",
    "other": "Overig",
}


# ── Create / Update ──────────────────────────────────────────────────────


class TimeEntryCreate(BaseModel):
    case_id: uuid.UUID
    date: DateType
    duration_minutes: int = Field(..., gt=0, description="Duur in minuten")
    description: Optional[str] = None
    activity_type: str = Field(
        default="other",
        pattern="^(correspondence|meeting|phone|research|court|travel|drafting|other)$",
    )
    billable: bool = True
    hourly_rate: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class TimeEntryUpdate(BaseModel):
    case_id: Optional[uuid.UUID] = None
    date: Optional[DateType] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    activity_type: Optional[str] = Field(
        None,
        pattern="^(correspondence|meeting|phone|research|court|travel|drafting|other)$",
    )
    billable: Optional[bool] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


# ── Response ──────────────────────────────────────────────────────────────


class CaseBrief(BaseModel):
    id: uuid.UUID
    case_number: str

    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    id: uuid.UUID
    full_name: str

    model_config = {"from_attributes": True}


class TimeEntryResponse(BaseModel):
    id: uuid.UUID
    user: UserBrief
    case: CaseBrief
    date: DateType
    duration_minutes: int
    description: Optional[str]
    activity_type: str
    billable: bool
    hourly_rate: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Summary / Aggregation ────────────────────────────────────────────────


class CaseTimeSummary(BaseModel):
    case_id: uuid.UUID
    case_number: str
    total_minutes: int
    billable_minutes: int
    total_amount: Decimal


class TimeEntrySummary(BaseModel):
    total_minutes: int
    billable_minutes: int
    non_billable_minutes: int
    total_amount: Decimal
    per_case: list[CaseTimeSummary]
