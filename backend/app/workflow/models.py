"""Workflow task model."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class WorkflowTask(TenantBase):
    """Manual and system-generated tasks attached to cases."""

    __tablename__ = "workflow_tasks"

    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("cases.id"), nullable=False)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    auto_execute: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    action_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # G9: recurring task support.
    recurrence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recurrence_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("workflow_tasks.id"), nullable=True
    )

    case: Mapped["Case"] = relationship("Case", lazy="selectin")  # noqa: F821
    assigned_to: Mapped["User | None"] = relationship(  # noqa: F821
        "User", lazy="selectin"
    )
    parent_task: Mapped["WorkflowTask | None"] = relationship(
        "WorkflowTask", remote_side="WorkflowTask.id", lazy="selectin"
    )
