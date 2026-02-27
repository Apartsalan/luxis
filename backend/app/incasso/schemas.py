"""Incasso pipeline schemas — Pydantic models for request/response validation."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ── Pipeline Step ─────────────────────────────────────────────────────────


class PipelineStepCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sort_order: int = 0
    min_wait_days: int = Field(default=0, ge=0)
    max_wait_days: int = Field(default=0, ge=0)
    template_id: uuid.UUID | None = None
    template_type: str | None = None  # docx template key (e.g. "aanmaning")


class PipelineStepUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    sort_order: int | None = None
    min_wait_days: int | None = Field(default=None, ge=0)
    max_wait_days: int | None = Field(default=None, ge=0)
    template_id: uuid.UUID | None = None
    template_type: str | None = None
    is_active: bool | None = None


class PipelineStepResponse(BaseModel):
    id: uuid.UUID
    name: str
    sort_order: int
    min_wait_days: int
    max_wait_days: int = 0
    template_id: uuid.UUID | None
    template_type: str | None = None
    template_name: str | None = None
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
    total_principal: float
    total_paid: float
    outstanding: float
    days_in_step: int
    incasso_step_id: uuid.UUID | None
    status: str
    date_opened: str  # ISO date string
    deadline_status: str = "gray"  # green | orange | red | gray

    model_config = {"from_attributes": True}


class PipelineColumn(BaseModel):
    """A single pipeline step column with its cases."""

    step: PipelineStepResponse
    cases: list[CaseInPipeline]
    count: int


class PipelineOverview(BaseModel):
    """Full pipeline view — all steps with their cases."""

    columns: list[PipelineColumn]
    unassigned: list[CaseInPipeline]  # Incasso cases not yet in a pipeline step
    total_cases: int


# ── Batch Actions ─────────────────────────────────────────────────────────


class BatchPreviewRequest(BaseModel):
    """Request a pre-flight check for a batch action."""

    case_ids: list[uuid.UUID]
    action: str = Field(
        ..., description="advance_step, generate_document, recalculate_interest"
    )
    target_step_id: uuid.UUID | None = None  # For advance_step


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
    needs_step_assignment: list[CaseInPipeline]  # Cases not yet in a step


class BatchActionRequest(BaseModel):
    """Execute a batch action on selected cases."""

    case_ids: list[uuid.UUID]
    action: str = Field(
        ..., description="advance_step, generate_document, recalculate_interest"
    )
    target_step_id: uuid.UUID | None = None
    auto_assign_step: bool = False  # Auto-assign first step to unassigned cases


class BatchActionResult(BaseModel):
    """Result of a batch action execution."""

    action: str
    processed: int
    skipped: int
    errors: list[str]
    generated_document_ids: list[uuid.UUID] = []  # For generate_document action
    tasks_auto_completed: int = 0  # Tasks auto-completed after document generation
    cases_auto_advanced: int = 0  # Cases auto-advanced to next pipeline step


# ── Smart Work Queues ────────────────────────────────────────────────────


class QueueCounts(BaseModel):
    """Badge counts for Smart Work Queue tabs."""

    ready_next_step: int = 0  # Cases where days_in_step >= next step's min_wait_days
    wik_expired: int = 0  # Cases where 14-day WIK deadline has passed
    action_required: int = 0  # Total needing attention (sum/union of above + unassigned)
