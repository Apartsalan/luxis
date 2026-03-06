"""EmailAttachment model — stores attachments from synced emails.

Files are stored on disk in /app/uploads/email_attachments/{tenant_id}/{email_id}/
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class EmailAttachment(TenantBase):
    """An attachment downloaded from a synced email."""

    __tablename__ = "email_attachments"

    synced_email_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("synced_emails.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Provider attachment ID (Gmail: attachmentId)
    provider_attachment_id: Mapped[str] = mapped_column(
        String(500), nullable=False
    )

    # File metadata
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(200), nullable=False, default="application/octet-stream"
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    synced_email: Mapped["SyncedEmail"] = relationship(  # noqa: F821
        "SyncedEmail", lazy="selectin"
    )
