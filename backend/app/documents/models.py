"""Documents module models — DocumentTemplate and GeneratedDocument."""

import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class DocumentTemplate(TenantBase):
    """A document template (e.g. 14-dagenbrief, sommatie, renteberekening).

    Templates use Jinja2 syntax and can be rendered with case/contact data.
    """

    __tablename__ = "document_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 14_dagenbrief, sommatie, renteberekening, dagvaarding, etc.
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # HTML/Jinja2 template content
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    generated_documents: Mapped[list["GeneratedDocument"]] = relationship(
        "GeneratedDocument",
        back_populates="template",
        lazy="selectin",
    )


class GeneratedDocument(TenantBase):
    """A generated document from a template, linked to a case."""

    __tablename__ = "generated_documents"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cases.id"), nullable=False
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("document_templates.id"), nullable=True
    )
    generated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # Same types as template_type
    content_html: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Rendered HTML content
    file_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # Path to generated PDF
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    case: Mapped["Case"] = relationship(  # noqa: F821
        "Case", lazy="selectin"
    )
    template: Mapped["DocumentTemplate | None"] = relationship(
        "DocumentTemplate",
        back_populates="generated_documents",
    )
    generated_by: Mapped["User | None"] = relationship(  # noqa: F821
        "User", lazy="selectin"
    )
