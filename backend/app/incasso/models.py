"""Incasso pipeline models — configurable collection workflow steps and step history."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class IncassoPipelineStep(TenantBase):
    """A configurable step in the collections pipeline.

    Steps follow the 4-phase model: minnelijk → gerechtelijk → executie → afsluiting.
    Cross-phase categories: regeling, administratief.
    """

    __tablename__ = "incasso_pipeline_steps"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_wait_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    max_wait_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("document_templates.id"), nullable=True
    )
    template_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    email_subject_template: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email_body_template: Mapped[str | None] = mapped_column(Text, nullable=True)

    step_category: Mapped[str] = mapped_column(
        String(30), nullable=False, default="minnelijk", server_default="minnelijk"
    )
    debtor_type: Mapped[str] = mapped_column(
        String(10), nullable=False, default="both", server_default="both"
    )
    is_terminal: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    is_hold_step: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )

    # Relationships
    template: Mapped["DocumentTemplate | None"] = relationship(  # noqa: F821
        "DocumentTemplate", lazy="selectin"
    )


class CaseStepHistory(TenantBase):
    """Tracks every step entry/exit for a case — audit trail for the pipeline."""

    __tablename__ = "case_step_history"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=False, index=True
    )
    step_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("incasso_pipeline_steps.id"), nullable=False
    )
    entered_at: Mapped[datetime] = mapped_column(  # noqa: F821
        DateTime(timezone=True), nullable=False
    )
    exited_at: Mapped[datetime | None] = mapped_column(  # noqa: F821
        DateTime(timezone=True), nullable=True
    )
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    trigger_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="manual"
    )
    template_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    email_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("generated_documents.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    step: Mapped["IncassoPipelineStep"] = relationship(
        "IncassoPipelineStep", lazy="selectin"
    )
    triggered_by_user: Mapped["User | None"] = relationship(  # noqa: F821
        "User", lazy="selectin"
    )
