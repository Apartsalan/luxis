"""AI Agent schemas — request/response models for email classification."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class ClassificationResponse(BaseModel):
    """Response schema for an email classification."""

    id: uuid.UUID
    synced_email_id: uuid.UUID
    case_id: uuid.UUID
    case_number: str
    email_subject: str
    email_from: str
    email_date: datetime

    # Classification
    category: str
    category_label: str
    confidence: float
    reasoning: str
    sentiment: str | None = None

    # Suggested action
    suggested_action: str
    suggested_action_label: str
    suggested_template_key: str | None = None
    suggested_template_name: str | None = None
    suggested_reminder_days: int | None = None

    # Payment promise (AUDIT-18)
    promise_date: date | None = None
    promise_amount: Decimal | None = None

    # Review status
    status: str
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None

    # Execution
    executed_at: datetime | None = None
    execution_result: str | None = None

    created_at: datetime

    model_config = {"from_attributes": True}


class ClassificationApproveRequest(BaseModel):
    """Request body for approving or rejecting a classification."""

    note: str | None = None


class ResponseTemplateResponse(BaseModel):
    """Response schema for a response template."""

    id: uuid.UUID
    key: str
    name: str
    category: str
    subject_template: str
    body_template: str
    is_active: bool
    sort_order: int

    model_config = {"from_attributes": True}


class PendingCountResponse(BaseModel):
    """Response for the pending classification count endpoint."""

    count: int
