"""Intake schemas — request/response models for dossier intake."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class IntakeResponse(BaseModel):
    """Response schema for an intake request."""

    id: uuid.UUID
    synced_email_id: uuid.UUID

    # Source email info
    email_subject: str = ""
    email_from: str = ""
    email_date: datetime | None = None
    client_name: str | None = None

    # Extracted debtor info
    debtor_name: str | None = None
    debtor_email: str | None = None
    debtor_kvk: str | None = None
    debtor_address: str | None = None
    debtor_city: str | None = None
    debtor_postcode: str | None = None
    debtor_type: str = "company"

    # Extracted invoice info
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    principal_amount: Decimal | None = None
    description: str | None = None

    # AI metadata
    ai_model: str = ""
    ai_confidence: float | None = None
    ai_reasoning: str = ""
    has_pdf_data: bool = False

    # Status
    status: str
    error_message: str | None = None

    # Review
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None

    # Created entities
    created_case_id: uuid.UUID | None = None
    created_case_number: str | None = None
    created_contact_id: uuid.UUID | None = None
    created_contact_name: str | None = None

    created_at: datetime

    model_config = {"from_attributes": True}


class IntakeReviewRequest(BaseModel):
    """Request body for approving or rejecting an intake."""

    note: str | None = None


class IntakeUpdateRequest(BaseModel):
    """Request body for updating extracted data before approval."""

    debtor_name: str | None = None
    debtor_email: str | None = None
    debtor_kvk: str | None = None
    debtor_address: str | None = None
    debtor_city: str | None = None
    debtor_postcode: str | None = None
    debtor_type: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    principal_amount: Decimal | None = None
    description: str | None = None


class IntakePendingCountResponse(BaseModel):
    """Response for the pending intake count endpoint."""

    count: int
