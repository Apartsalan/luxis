"""AI Agent models — email classification and response templates."""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class ClassificationCategory(StrEnum):
    """Categories for debtor email classification."""

    BELOFTE_TOT_BETALING = "belofte_tot_betaling"
    BETWISTING = "betwisting"
    BETALINGSREGELING_VERZOEK = "betalingsregeling_verzoek"
    BEWEERT_BETAALD = "beweert_betaald"
    ONVERMOGEN = "onvermogen"
    JURIDISCH_VERWEER = "juridisch_verweer"
    ONTVANGSTBEVESTIGING = "ontvangstbevestiging"
    NIET_GERELATEERD = "niet_gerelateerd"


class SuggestedAction(StrEnum):
    """Actions the AI can suggest after classifying an email."""

    WAIT_AND_REMIND = "wait_and_remind"
    ESCALATE = "escalate"
    SEND_TEMPLATE = "send_template"
    DISMISS = "dismiss"
    REQUEST_PROOF = "request_proof"
    NO_ACTION = "no_action"


class ClassificationStatus(StrEnum):
    """Status of an email classification through the review workflow."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


# Default mapping: category → suggested action
CATEGORY_ACTION_MAP: dict[ClassificationCategory, SuggestedAction] = {
    ClassificationCategory.BELOFTE_TOT_BETALING: SuggestedAction.WAIT_AND_REMIND,
    ClassificationCategory.BETWISTING: SuggestedAction.ESCALATE,
    ClassificationCategory.BETALINGSREGELING_VERZOEK: SuggestedAction.ESCALATE,
    ClassificationCategory.BEWEERT_BETAALD: SuggestedAction.REQUEST_PROOF,
    ClassificationCategory.ONVERMOGEN: SuggestedAction.ESCALATE,
    ClassificationCategory.JURIDISCH_VERWEER: SuggestedAction.ESCALATE,
    ClassificationCategory.ONTVANGSTBEVESTIGING: SuggestedAction.NO_ACTION,
    ClassificationCategory.NIET_GERELATEERD: SuggestedAction.DISMISS,
}

# Default mapping: category → response template key (None = no template)
CATEGORY_TEMPLATE_MAP: dict[ClassificationCategory, str | None] = {
    ClassificationCategory.BELOFTE_TOT_BETALING: "bevestiging_betaalbelofte",
    ClassificationCategory.BETWISTING: "ontvangst_betwisting",
    ClassificationCategory.BETALINGSREGELING_VERZOEK: "ontvangst_regeling_verzoek",
    ClassificationCategory.BEWEERT_BETAALD: "verzoek_betalingsbewijs",
    ClassificationCategory.ONVERMOGEN: "ontvangst_onvermogen",
    ClassificationCategory.JURIDISCH_VERWEER: "doorverwijzing_advocaat",
    ClassificationCategory.ONTVANGSTBEVESTIGING: None,
    ClassificationCategory.NIET_GERELATEERD: None,
}

# Dutch display labels for categories
CATEGORY_LABELS: dict[str, str] = {
    "belofte_tot_betaling": "Belofte tot betaling",
    "betwisting": "Betwisting",
    "betalingsregeling_verzoek": "Betalingsregeling verzoek",
    "beweert_betaald": "Beweert betaald",
    "onvermogen": "Onvermogen",
    "juridisch_verweer": "Juridisch verweer",
    "ontvangstbevestiging": "Ontvangstbevestiging",
    "niet_gerelateerd": "Niet gerelateerd",
}

# Dutch display labels for actions
ACTION_LABELS: dict[str, str] = {
    "wait_and_remind": "Wacht af + herinnering",
    "escalate": "Escaleer naar advocaat",
    "send_template": "Stuur antwoord",
    "dismiss": "Wegzetten",
    "request_proof": "Vraag betalingsbewijs",
    "no_action": "Geen actie nodig",
}


class EmailClassification(TenantBase):
    """AI classification of an inbound debtor email on an incasso case."""

    __tablename__ = "email_classifications"

    synced_email_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("synced_emails.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Classification result
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Sentiment (AUDIT-28)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Suggested action
    suggested_action: Mapped[str] = mapped_column(String(50), nullable=False)
    suggested_template_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    suggested_reminder_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Human review
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ClassificationStatus.PENDING
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Execution tracking
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_result: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    synced_email: Mapped["SyncedEmail"] = relationship(  # noqa: F821
        "SyncedEmail", lazy="selectin"
    )
    case: Mapped["Case"] = relationship("Case", lazy="selectin")  # noqa: F821
    reviewed_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User", lazy="selectin"
    )


class ResponseTemplate(TenantBase):
    """Reusable email response template selected by the AI agent."""

    __tablename__ = "response_templates"

    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_template: Mapped[str] = mapped_column(String(500), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        # Each tenant can have one template per key
        {"comment": "AI response templates per tenant"},
    )
