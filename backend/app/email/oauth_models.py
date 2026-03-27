"""Email OAuth models — stores connected email accounts with encrypted tokens."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class EmailAccount(TenantBase):
    """A connected email account (Gmail, Outlook) linked to a Luxis user.

    Stores OAuth tokens encrypted at rest via Fernet (symmetric encryption).
    Each user can have one email account connected per provider.
    """

    __tablename__ = "email_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # 'gmail' or 'outlook'
    email_address: Mapped[str] = mapped_column(
        String(320), nullable=False
    )  # The connected email address (e.g. arsalanseidony@gmail.nl)

    # Encrypted OAuth tokens (Fernet-encrypted bytes)
    access_token_enc: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    refresh_token_enc: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Scopes granted by the user
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Space-separated scopes string

    # Sync state (for M2: inbox sync)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_cursor: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Gmail historyId or Outlook deltaLink

    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")  # noqa: F821
