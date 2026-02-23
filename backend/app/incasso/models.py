"""Incasso pipeline models — configurable collection workflow steps."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class IncassoPipelineStep(TenantBase):
    """A configurable step in the collections pipeline.

    Default steps: Aanmaning → Sommatie → 2e Sommatie → Ingebrekestelling → Dagvaarding → Executie
    Each step can have a minimum wait period and a linked document template.
    """

    __tablename__ = "incasso_pipeline_steps"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_wait_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # Minimum days before moving to this step
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("document_templates.id"), nullable=True
    )  # Legacy: FK to deprecated HTML template system
    template_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # Modern: docx template key (e.g. "aanmaning", "sommatie")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    template: Mapped["DocumentTemplate | None"] = relationship(  # noqa: F821
        "DocumentTemplate", lazy="selectin"
    )
