"""Calendar module schemas — Pydantic models for calendar events."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ── Event type labels ────────────────────────────────────────────────────────

EVENT_TYPE_LABELS = {
    "appointment": "Afspraak",
    "hearing": "Zitting",
    "deadline": "Deadline",
    "reminder": "Herinnering",
    "meeting": "Vergadering",
    "call": "Telefoongesprek",
    "other": "Overig",
}


# ── Brief models ─────────────────────────────────────────────────────────────


class CaseBrief(BaseModel):
    id: uuid.UUID
    case_number: str
    model_config = {"from_attributes": True}


class ContactBrief(BaseModel):
    id: uuid.UUID
    name: str
    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    id: uuid.UUID
    full_name: str
    model_config = {"from_attributes": True}


# ── Create / Update ──────────────────────────────────────────────────────────


class CalendarEventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    event_type: str = Field(default="appointment")
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    location: str | None = Field(None, max_length=500)
    case_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    color: str | None = Field(None, max_length=20)
    reminder_minutes: int | None = 30


class CalendarEventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    event_type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    all_day: bool | None = None
    location: str | None = Field(None, max_length=500)
    case_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    color: str | None = Field(None, max_length=20)
    reminder_minutes: int | None = None


# ── Response ─────────────────────────────────────────────────────────────────


class CalendarEventResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    event_type: str
    start_time: datetime
    end_time: datetime
    all_day: bool
    location: str | None
    case_id: uuid.UUID | None
    contact_id: uuid.UUID | None
    color: str | None
    reminder_minutes: int | None
    created_by: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    case: CaseBrief | None = None
    contact: ContactBrief | None = None
    creator: UserBrief | None = None

    model_config = {"from_attributes": True}
