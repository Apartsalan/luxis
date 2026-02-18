"""Email module models — EmailLog for tracking sent emails."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class EmailLog(TenantBase):
    """Log entry for every email sent from the system."""

    __tablename__ = "email_logs"

    case_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("generated_documents.id"), nullable=True
    )
    template: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Which email template was used (e.g. 'document_sent', 'deadline_reminder')
    recipient: Mapped[str] = mapped_column(
        String(320), nullable=False
    )  # Recipient email address
    subject: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="sent"
    )  # sent, failed
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    case: Mapped["Case | None"] = relationship(  # noqa: F821
        "Case", lazy="selectin"
    )
    document: Mapped["GeneratedDocument | None"] = relationship(  # noqa: F821
        "GeneratedDocument", lazy="selectin"
    )
