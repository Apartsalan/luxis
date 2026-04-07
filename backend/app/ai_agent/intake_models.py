"""Intake models — AI-powered dossier intake from client emails with invoices."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class IntakeStatus(StrEnum):
    """Status of an intake request through the processing pipeline."""

    DETECTED = "detected"  # Email detected as potential intake
    PROCESSING = "processing"  # AI is extracting data
    PENDING_REVIEW = "pending_review"  # Extraction done, waiting for review
    APPROVED = "approved"  # Lawyer approved, case created
    REJECTED = "rejected"  # Lawyer rejected
    FAILED = "failed"  # AI extraction failed


class IntakeRequest(TenantBase):
    """An AI-detected dossier intake request from a client email.

    Flow:
    1. Client sends email with invoice/debtor info → detected
    2. AI extracts debtor name, invoice number, amount, etc. → pending_review
    3. Lawyer reviews extracted data → approved/rejected
    4. On approval: contact + case created automatically
    """

    __tablename__ = "intake_requests"

    # Source email
    synced_email_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("synced_emails.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Extracted debtor info
    debtor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    debtor_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    debtor_kvk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    debtor_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    debtor_city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    debtor_postcode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    debtor_postal_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    debtor_postal_postcode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    debtor_postal_city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    debtor_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="company"
    )  # 'company' or 'person'

    # Extracted invoice/claim info
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    principal_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Client reference (from sender email → known client contact)
    client_contact_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=True
    )

    # AI metadata
    ai_model: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    ai_confidence: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    ai_reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_extraction: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # PDF extraction flag
    has_pdf_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=IntakeStatus.DETECTED)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Review
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Result — references to created entities
    created_case_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=True
    )
    created_contact_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=True
    )

    # Relationships
    synced_email: Mapped["SyncedEmail"] = relationship(  # noqa: F821
        "SyncedEmail", lazy="selectin"
    )
    client_contact: Mapped["Contact | None"] = relationship(  # noqa: F821
        "Contact", foreign_keys=[client_contact_id], lazy="selectin"
    )
    reviewed_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User", lazy="selectin"
    )
    created_case: Mapped["Case | None"] = relationship(  # noqa: F821
        "Case", lazy="selectin"
    )
    created_contact: Mapped["Contact | None"] = relationship(  # noqa: F821
        "Contact", foreign_keys=[created_contact_id], lazy="selectin"
    )
