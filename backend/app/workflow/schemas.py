"""Workflow schemas for tasks and calendar events."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

LEGAL_CONSTRAINTS = {
    "verjaring_years": 5,  # Art. 3:307 BW: 5 jaar verjaring
}
TASK_TYPES = (
    "generate_document",
    "send_letter",
    "send_email",
    "check_payment",
    "escalate_status",
    "manual_review",
    "set_deadline",
    "custom",
    "verjaring_warning",
    "review_ai_draft",
)
TASK_STATUSES = ("pending", "due", "completed", "skipped", "overdue")
_TERMINAL_TASK_STATUSES = ("completed", "skipped")


def effective_task_status(status: str, due_date: date, today: date | None = None) -> str:
    """Derive an open task's current status from its due date."""
    if status in _TERMINAL_TASK_STATUSES:
        return status
    today = today or date.today()
    if due_date < today:
        return "overdue"
    if due_date == today:
        return "due"
    return "pending"


RECURRENCE_OPTIONS = ("daily", "weekly", "monthly", "quarterly", "yearly")


class WorkflowTaskCreate(BaseModel):
    case_id: uuid.UUID
    assigned_to_id: uuid.UUID | None = None
    task_type: str = Field(..., description="generate_document, send_letter, check_payment, etc.")
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    due_date: date
    auto_execute: bool = False
    action_config: dict | None = None
    recurrence: str | None = None  # G9: daily, weekly, monthly, quarterly, yearly
    recurrence_end_date: date | None = None  # G9


class WorkflowTaskUpdate(BaseModel):
    assigned_to_id: uuid.UUID | None = None
    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    status: str | None = None
    recurrence: str | None = None  # G9
    recurrence_end_date: date | None = None  # G9


class WorkflowTaskResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    assigned_to_id: uuid.UUID | None
    task_type: str
    title: str
    description: str | None
    due_date: date
    completed_at: datetime | None
    status: str
    auto_execute: bool
    action_config: dict | None
    recurrence: str | None = None  # G9
    recurrence_end_date: date | None = None  # G9
    parent_task_id: uuid.UUID | None = None  # G9
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def _derive_effective_status(self) -> "WorkflowTaskResponse":
        """Recompute status from due_date so the takenlijst/agenda never read
        the stale batch-materialized value (AUDIT-H22)."""
        self.status = effective_task_status(self.status, self.due_date)
        return self


class CalendarEvent(BaseModel):
    """A single calendar event — workflow task or KYC review deadline."""

    id: str
    title: str
    date: date
    event_type: str  # "task", "kyc_review"
    status: str  # "pending", "due", "overdue", "completed"
    case_id: str | None = None
    case_number: str | None = None
    contact_id: str | None = None
    contact_name: str | None = None
    assigned_to_name: str | None = None
    task_type: str | None = None
    color: str  # hex color for calendar display

    model_config = {"from_attributes": True}
