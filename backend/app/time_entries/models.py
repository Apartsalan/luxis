"""Time entries module models — TimeEntry for time tracking (tijdschrijven)."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase

ACTIVITY_TYPES = (
    "correspondence",
    "meeting",
    "phone",
    "research",
    "court",
    "travel",
    "drafting",
    "other",
)


class TimeEntry(TenantBase):
    """A time registration entry linked to a case and user."""

    __tablename__ = "time_entries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="other"
    )
    billable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")  # noqa: F821
    case: Mapped["Case"] = relationship("Case", lazy="selectin")  # noqa: F821
