"""Calendar module models — CalendarEvent for user-created agenda events."""

import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase

# ── Event type constants ─────────────────────────────────────────────────────

EVENT_TYPES = (
    "appointment",  # Afspraak
    "hearing",  # Zitting
    "deadline",  # Deadline
    "reminder",  # Herinnering
    "meeting",  # Vergadering
    "call",  # Telefoongesprek
    "other",  # Overig
)

EVENT_TYPE_COLORS = {
    "appointment": "#3b82f6",  # blue
    "hearing": "#ef4444",  # red
    "deadline": "#f97316",  # orange
    "reminder": "#eab308",  # yellow
    "meeting": "#8b5cf6",  # purple
    "call": "#22c55e",  # green
    "other": "#6b7280",  # gray
}


class CalendarEvent(TenantBase):
    """A user-created calendar event (afspraak, zitting, deadline, etc.)."""

    __tablename__ = "calendar_events"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, default="appointment")

    start_time: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    location: Mapped[str | None] = mapped_column(String(500), nullable=True)

    case_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=True
    )

    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reminder_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=30)

    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Outlook sync fields
    provider_event_id: Mapped[str | None] = mapped_column(
        String(500), nullable=True, index=True
    )
    provider: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "outlook" or None
    outlook_change_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    case = relationship("Case", lazy="selectin")
    contact = relationship("Contact", lazy="selectin")
    creator = relationship("User", lazy="selectin")
