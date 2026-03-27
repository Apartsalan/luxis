"""Workflow module schemas — Pydantic models for statuses, transitions, tasks, rules."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

# ── Legal constraints (hardcoded, not configurable) ─────────────────────────

LEGAL_CONSTRAINTS = {
    "14_dagenbrief_min_wait": 14,  # Art. 6:96 lid 6 BW: min 14 dagen wachttijd
    "14_dagenbrief_required_b2c": True,  # 14-dagenbrief is verplicht voor B2C
    "verjaring_years": 5,  # Art. 3:307 BW: 5 jaar verjaring
}

WORKFLOW_PHASES = ("minnelijk", "regeling", "gerechtelijk", "executie", "afgerond")
TASK_TYPES = (
    "generate_document",
    "send_letter",
    "send_email",
    "check_payment",
    "escalate_status",
    "manual_review",
    "set_deadline",
    "custom",
)
TASK_STATUSES = ("pending", "due", "completed", "skipped", "overdue")


# ── WorkflowStatus ─────────────────────────────────────────────────────────


class WorkflowStatusCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=50)
    label: str = Field(..., min_length=1, max_length=100)
    phase: str = Field(..., description="minnelijk, regeling, gerechtelijk, executie, afgerond")
    sort_order: int = 0
    color: str = "gray"
    is_terminal: bool = False
    is_initial: bool = False


class WorkflowStatusUpdate(BaseModel):
    label: str | None = None
    phase: str | None = None
    sort_order: int | None = None
    color: str | None = None
    is_terminal: bool | None = None
    is_initial: bool | None = None


class WorkflowStatusResponse(BaseModel):
    id: uuid.UUID
    slug: str
    label: str
    phase: str
    sort_order: int
    color: str
    is_terminal: bool
    is_initial: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── WorkflowTransition ─────────────────────────────────────────────────────


class WorkflowTransitionCreate(BaseModel):
    from_status_id: uuid.UUID
    to_status_id: uuid.UUID
    debtor_type: str = Field(default="both", description="b2b, b2c, or both")
    requires_note: bool = False


class WorkflowTransitionResponse(BaseModel):
    id: uuid.UUID
    from_status_id: uuid.UUID
    to_status_id: uuid.UUID
    from_status: WorkflowStatusResponse
    to_status: WorkflowStatusResponse
    debtor_type: str
    requires_note: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AllowedTransitionResponse(BaseModel):
    """Lightweight response for 'what transitions are allowed from current status'."""

    to_status_id: uuid.UUID
    to_slug: str
    to_label: str
    to_phase: str
    to_color: str
    debtor_type: str
    requires_note: bool


# ── WorkflowTask ───────────────────────────────────────────────────────────


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
    created_by_rule_id: uuid.UUID | None
    recurrence: str | None = None  # G9
    recurrence_end_date: date | None = None  # G9
    parent_task_id: uuid.UUID | None = None  # G9
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── WorkflowRule ───────────────────────────────────────────────────────────


class WorkflowRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    trigger_status_id: uuid.UUID
    debtor_type: str = Field(default="both", description="b2b, b2c, or both")
    days_delay: int = 0
    action_type: str
    action_config: dict | None = None
    auto_execute: bool = False
    assign_to_case_owner: bool = True
    sort_order: int = 0


class WorkflowRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_status_id: uuid.UUID | None = None
    debtor_type: str | None = None
    days_delay: int | None = None
    action_type: str | None = None
    action_config: dict | None = None
    auto_execute: bool | None = None
    assign_to_case_owner: bool | None = None
    sort_order: int | None = None


class WorkflowRuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    trigger_status_id: uuid.UUID
    trigger_status: WorkflowStatusResponse
    debtor_type: str
    days_delay: int
    action_type: str
    action_config: dict | None
    auto_execute: bool
    assign_to_case_owner: bool
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Validation warnings ────────────────────────────────────────────────────


class TransitionValidationResult(BaseModel):
    allowed: bool
    warnings: list[str] = []
    errors: list[str] = []


# ── Calendar ──────────────────────────────────────────────────────────────


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
