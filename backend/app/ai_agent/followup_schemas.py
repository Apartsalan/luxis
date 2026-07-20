"""Follow-up recommendation schemas — request/response models."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class FollowupRecommendationOut(BaseModel):
    """Response schema for a follow-up recommendation."""

    id: uuid.UUID
    case_id: uuid.UUID
    case_number: str
    client_name: str | None = None
    opposing_party_name: str | None = None

    # Step context
    incasso_step_id: uuid.UUID
    step_name: str

    # Recommendation
    recommended_action: str
    action_label: str
    reasoning: str
    days_in_step: int
    outstanding_amount: Decimal
    urgency: str
    urgency_label: str

    # Review
    status: str
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None

    # Execution
    executed_at: datetime | None = None
    execution_result: str | None = None
    generated_document_id: uuid.UUID | None = None

    created_at: datetime

    model_config = {"from_attributes": True}


class FollowupRecommendationList(BaseModel):
    """Paginated list of follow-up recommendations."""

    items: list[FollowupRecommendationOut]
    total: int
    page: int
    per_page: int
    pages: int


class FollowupStatsOut(BaseModel):
    """Counts per recommendation status."""

    pending: int = 0
    approved: int = 0
    rejected: int = 0
    executed: int = 0


class FollowupRejectIn(BaseModel):
    """Request body for rejecting a recommendation."""

    note: str | None = None


class FollowupAttachmentItem(BaseModel):
    """S231 — een bijlage die meegaat, mét een adres om hem te openen.

    Zelfde vorm als `AutoAttachmentItem` op de compose-route: `template_type`
    voor bijlagen die de server vers rendert (renteoverzicht, concept-
    verzoekschrift, de brief zelf op de DOCX-route), `case_file_id` voor een
    bestaand dossierbestand.
    """

    label: str
    template_type: str | None = None
    case_file_id: uuid.UUID | None = None


class FollowupPreviewOut(BaseModel):
    """B13 — wat er precies uitgaat als je deze aanbeveling uitvoert.

    Toont de gebruiker vóór de één-klik-verzending: onderwerp, afzender (vast
    incasso@), ontvanger en de volledige e-mailtekst. Verzendt niets.
    """

    subject: str
    body_html: str
    sender_email: str
    recipient_email: str | None = None
    recipient_name: str | None = None
    # S231: nodig om een bijlage te kunnen opvragen vanuit de voorvertoning.
    case_id: uuid.UUID | None = None
    has_attachment: bool = False
    # S231: niet alleen "er gaat een bijlage mee", maar ook wélke en waar hij
    # vandaan komt — zodat de gebruiker hem vóór verzending kan openen.
    attachments: list[FollowupAttachmentItem] = []
    can_send: bool = True
    warning: str | None = None
