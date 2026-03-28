"""Exact Online models — connection + sync tracking."""

import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin
from app.shared.models import TenantBase


class ExactOnlineConnection(TenantBase):
    """OAuth connection to Exact Online for a tenant (one per kantoor)."""

    __tablename__ = "exact_online_connections"

    # Division (required for every Exact API call)
    division_id: Mapped[int] = mapped_column(Integer, nullable=False)
    division_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    # OAuth tokens (Fernet-encrypted)
    access_token_enc: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    refresh_token_enc: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    token_expiry: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Connected user info
    connected_email: Mapped[str] = mapped_column(String(320), nullable=False, default="")
    connected_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )

    # Exact Online settings — journal and GL account mappings
    sales_journal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    bank_journal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    default_revenue_gl: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_expense_gl: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Sync state
    last_sync_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ExactSyncLog(TenantBase):
    """Tracks which Luxis entities have been synced to Exact Online."""

    __tablename__ = "exact_sync_log"

    # What was synced
    entity_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # contact, invoice, payment
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)

    # Exact Online reference
    exact_id: Mapped[str] = mapped_column(String(50), nullable=False)
    exact_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Sync status
    sync_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="synced"
    )  # synced, error, pending
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
