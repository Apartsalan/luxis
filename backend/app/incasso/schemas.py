"""Incasso pipeline schemas — Pydantic models for request/response validation."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

# ── Pipeline Step ─────────────────────────────────────────────────────────


class PipelineStepCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sort_order: int = 0
    min_wait_days: int = Field(default=0, ge=0)
    max_wait_days: int = Field(default=0, ge=0)
    template_id: uuid.UUID | None = None
    template_type: str | None = None
    email_subject_template: str | None = None
    email_body_template: str | None = None
    step_category: str = "minnelijk"
    debtor_type: str = "both"
    is_terminal: bool = False
    is_hold_step: bool = False


class PipelineStepUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    sort_order: int | None = None
    min_wait_days: int | None = Field(default=None, ge=0)
    max_wait_days: int | None = Field(default=None, ge=0)
    template_id: uuid.UUID | None = None
    template_type: str | None = None
    is_active: bool | None = None
    email_subject_template: str | None = None
    email_body_template: str | None = None
    step_category: str | None = None
    debtor_type: str | None = None
    is_terminal: bool | None = None
    is_hold_step: bool | None = None


class PipelineStepResponse(BaseModel):
    id: uuid.UUID
    name: str
    sort_order: int
    min_wait_days: int
    max_wait_days: int = 0
    template_id: uuid.UUID | None
    template_type: str | None = None
    template_name: str | None = None
    email_subject_template: str | None = None
    email_body_template: str | None = None
    step_category: str = "minnelijk"
    debtor_type: str = "both"
    is_terminal: bool = False
    is_hold_step: bool = False
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Pipeline Overview (batch workflow) ────────────────────────────────────


class CaseInPipeline(BaseModel):
    """A case shown in the incasso pipeline view."""

    id: uuid.UUID
    case_number: str
    client_name: str
    opposing_party_name: str | None
    total_principal: Decimal
    total_paid: Decimal
    outstanding: Decimal
    days_in_step: int
    incasso_step_id: uuid.UUID | None
    step_name: str | None = None
    debtor_type: str = "b2b"
    has_verweer: bool = False
    status: str
    date_opened: str
    deadline_status: str = "gray"

    model_config = {"from_attributes": True}


class PipelineColumn(BaseModel):
    """A single pipeline step column with its cases."""

    step: PipelineStepResponse
    cases: list[CaseInPipeline]
    count: int


class PipelineOverview(BaseModel):
    """Full pipeline view — all steps with their cases."""

    columns: list[PipelineColumn]
    unassigned: list[CaseInPipeline]
    total_cases: int


# ── Batch Actions ─────────────────────────────────────────────────────────


class BatchPreviewRequest(BaseModel):
    """Request a pre-flight check for a batch action."""

    case_ids: list[uuid.UUID]
    action: str = Field(..., description="advance_step, generate_document, recalculate_interest")
    target_step_id: uuid.UUID | None = None


class BatchBlocker(BaseModel):
    """A blocker preventing a case from being batch-actioned."""

    case_id: uuid.UUID
    case_number: str
    reason: str


class BatchPreviewResponse(BaseModel):
    """Pre-flight check result showing what will happen."""

    action: str
    total_selected: int
    ready: int
    blocked: list[BatchBlocker]
    needs_step_assignment: list[CaseInPipeline] = []
    email_ready: int = 0
    email_blocked: list[BatchBlocker] = []
    verweer_blocked: int = 0


class BatchActionRequest(BaseModel):
    """Execute a batch action on selected cases."""

    case_ids: list[uuid.UUID]
    action: str = Field(..., description="advance_step, generate_document, recalculate_interest")
    target_step_id: uuid.UUID | None = None
    auto_assign_step: bool = False
    send_email: bool = False


class BatchActionResult(BaseModel):
    """Result of a batch action execution."""

    action: str
    processed: int
    skipped: int
    errors: list[str]
    generated_document_ids: list[uuid.UUID] = []
    tasks_auto_completed: int = 0
    cases_auto_advanced: int = 0
    emails_sent: int = 0
    emails_failed: int = 0


# ── Smart Work Queues ────────────────────────────────────────────────────


class QueueCounts(BaseModel):
    """Badge counts for Smart Work Queue tabs."""

    ready_next_step: int = 0
    wik_expired: int = 0
    action_required: int = 0


# ── Step History ─────────────────────────────────────────────────────────


class CaseStepHistoryResponse(BaseModel):
    """A single step history entry for the timeline."""

    id: uuid.UUID
    step_id: uuid.UUID
    step_name: str
    step_category: str
    entered_at: datetime
    exited_at: datetime | None
    triggered_by_name: str | None = None
    trigger_type: str
    template_sent: bool
    email_sent: bool
    document_id: uuid.UUID | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


# ── Move Step / Verweer ──────────────────────────────────────────────────


class MoveToStepRequest(BaseModel):
    """Request to move a case to a specific pipeline step."""

    target_step_id: uuid.UUID
    notes: str | None = None


class SetVerweerRequest(BaseModel):
    """Toggle verweer (objection) on a case."""

    has_verweer: bool
    verweer_note: str | None = None
    verweer_date: date | None = None
