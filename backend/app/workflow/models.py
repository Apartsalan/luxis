"""Workflow module models — WorkflowStatus, WorkflowTransition, WorkflowTask, WorkflowRule."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class WorkflowStatus(TenantBase):
    """Configurable case status — replaces the hardcoded CASE_STATUSES tuple.

    Each tenant gets default statuses on creation, which can be customized.
    """

    __tablename__ = "workflow_statuses"

    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    phase: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # minnelijk, regeling, gerechtelijk, executie, afgerond
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="gray")
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_initial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WorkflowTransition(TenantBase):
    """Allowed status transitions — replaces the hardcoded STATUS_TRANSITIONS dict."""

    __tablename__ = "workflow_transitions"

    from_status_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workflow_statuses.id"), nullable=False
    )
    to_status_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workflow_statuses.id"), nullable=False
    )
    debtor_type: Mapped[str] = mapped_column(
        String(10), nullable=False, default="both"
    )  # b2b, b2c, both
    requires_note: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    from_status: Mapped["WorkflowStatus"] = relationship(
        "WorkflowStatus", foreign_keys=[from_status_id], lazy="selectin"
    )
    to_status: Mapped["WorkflowStatus"] = relationship(
        "WorkflowStatus", foreign_keys=[to_status_id], lazy="selectin"
    )


class WorkflowTask(TenantBase):
    """Tasks generated automatically by workflow rules or manually by users."""

    __tablename__ = "workflow_tasks"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=False
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )

    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # generate_document, send_letter, check_payment,
    # escalate_status, manual_review, set_deadline, custom

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, due, completed, skipped, overdue

    auto_execute: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    action_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_by_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("workflow_rules.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # G9: Recurring task support
    recurrence: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # daily, weekly, monthly, quarterly, yearly
    recurrence_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("workflow_tasks.id"), nullable=True
    )

    # Relationships
    case: Mapped["Case"] = relationship("Case", lazy="selectin")  # noqa: F821
    assigned_to: Mapped["User | None"] = relationship(  # noqa: F821
        "User", lazy="selectin"
    )
    created_by_rule: Mapped["WorkflowRule | None"] = relationship(
        "WorkflowRule", lazy="selectin"
    )
    parent_task: Mapped["WorkflowTask | None"] = relationship(
        "WorkflowTask", remote_side="WorkflowTask.id", lazy="selectin"
    )


class WorkflowRule(TenantBase):
    """Configurable automation rules — when a status is reached, create tasks."""

    __tablename__ = "workflow_rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    trigger_status_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workflow_statuses.id"), nullable=False
    )
    debtor_type: Mapped[str] = mapped_column(
        String(10), nullable=False, default="both"
    )  # b2b, b2c, both

    days_delay: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    action_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # generate_document, send_letter, check_payment,
    # escalate_status, manual_review, set_deadline, custom

    action_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    auto_execute: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assign_to_case_owner: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    trigger_status: Mapped["WorkflowStatus"] = relationship(
        "WorkflowStatus", lazy="selectin"
    )
