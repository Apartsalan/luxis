"""SyncedEmail model — stores emails fetched from providers, linked to dossiers.

Each synced email is matched to a case (dossier) via:
  sender/recipient email → Contact → Case (as client, opposing party, or case party)
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class SyncedEmail(TenantBase):
    """An email fetched from Gmail/Outlook, optionally linked to a case."""

    __tablename__ = "synced_emails"

    email_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=True, index=True
    )

    # Provider IDs (for dedup and threading)
    provider_message_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    provider_thread_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    # Email metadata
    subject: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    from_email: Mapped[str] = mapped_column(String(320), nullable=False)
    from_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    to_emails: Mapped[str] = mapped_column(Text, nullable=False, default="")  # JSON array
    cc_emails: Mapped[str] = mapped_column(Text, nullable=False, default="")  # JSON array
    snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_html: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Direction: did we send it or receive it?
    direction: Mapped[str] = mapped_column(
        String(10), nullable=False, default="inbound"
    )  # 'inbound' or 'outbound'

    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    has_attachments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    email_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    email_account: Mapped["EmailAccount"] = relationship(  # noqa: F821
        "EmailAccount", lazy="selectin"
    )
    case: Mapped["Case | None"] = relationship("Case", lazy="selectin")  # noqa: F821
    attachments: Mapped[list["EmailAttachment"]] = relationship(  # noqa: F821
        "EmailAttachment", back_populates="synced_email", lazy="selectin"
    )
