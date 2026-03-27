"""Documents module models — templates and generated documents."""

import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBase


class ManagedTemplate(TenantBase):
    """A managed DOCX document template stored in the database.

    Replaces the hardcoded disk-file template system. Each tenant gets
    builtin templates seeded from disk, and can upload custom ones.
    Custom templates with the same template_key override builtins.
    """

    __tablename__ = "managed_templates"
    __table_args__ = (
        Index(
            "ix_managed_templates_tenant_key",
            "tenant_id",
            "template_key",
        ),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_key: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g. "sommatie", "aanmaning", "14_dagenbrief"
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DocumentTemplate(TenantBase):
    """DEPRECATED: HTML/Jinja2 document template.

    This model is retained for backwards compatibility and existing data.
    New document generation uses the DOCX template system in docx_service.py.
    Do NOT create new HTML templates — use .docx templates instead.
    """

    __tablename__ = "document_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 14_dagenbrief, sommatie, renteberekening, dagvaarding, etc.
    content: Mapped[str] = mapped_column(Text, nullable=False)  # HTML/Jinja2 template content
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

    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("cases.id"), nullable=False)
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

    # DOCX system fields
    template_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # Which docx template was used (e.g. '14_dagenbrief', 'sommatie')
    template_snapshot: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )  # Copy of the .docx template at time of generation

    # Legacy HTML system (deprecated — use docx templates instead)
    content_html: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Rendered HTML content (deprecated)
    file_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # Path to generated file
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
