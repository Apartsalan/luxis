"""Documents module schemas — Pydantic models for document CRUD."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ── Document Template Schemas ────────────────────────────────────────────────


class DocumentTemplateCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    template_type: str = Field(
        ...,
        max_length=50,
        description="Type: 14_dagenbrief, sommatie, renteberekening, etc.",
    )
    content: str = Field(
        ...,
        description="HTML/Jinja2 template content",
    )


class DocumentTemplateUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    template_type: str | None = Field(None, max_length=50)
    content: str | None = None


class DocumentTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    template_type: str
    content: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentTemplateSummary(BaseModel):
    id: uuid.UUID
    name: str
    template_type: str
    is_active: bool

    model_config = {"from_attributes": True}


# ── Generated Document Schemas ───────────────────────────────────────────────


class GenerateDocumentRequest(BaseModel):
    template_id: uuid.UUID
    title: str | None = Field(
        None,
        max_length=255,
        description="Custom title; defaults to template name + case number",
    )
    extra_context: dict | None = Field(
        None,
        description="Extra variables to pass to the template",
    )


class GeneratedDocumentResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    template_id: uuid.UUID | None
    generated_by_id: uuid.UUID | None
    title: str
    document_type: str
    content_html: str | None
    file_path: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GeneratedDocumentSummary(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    title: str
    document_type: str
    file_path: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    id: uuid.UUID
    full_name: str

    model_config = {"from_attributes": True}


class GeneratedDocumentDetail(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    template_id: uuid.UUID | None
    title: str
    document_type: str
    content_html: str | None
    file_path: str | None
    generated_by: UserBrief | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Docx Generation Schemas ─────────────────────────────────────────────────


class GenerateDocxRequest(BaseModel):
    template_type: str = Field(
        ...,
        description="Template type: 14_dagenbrief, sommatie, renteoverzicht",
    )


class DocxTemplateInfo(BaseModel):
    template_type: str
    filename: str
    available: bool


class RenderTemplatePdfRequest(BaseModel):
    template_type: str = Field(
        ...,
        description=(
            "Template key uit TEMPLATE_FILES / managed_templates "
            "(bijv. 'verzoekschrift_faillissement')."
        ),
    )


class RenderedPdfAttachment(BaseModel):
    """PDF-bijlage klaar voor push naar compose inline_attachments."""

    filename: str
    data_base64: str
    content_type: str
    size: int


class LibraryTemplate(BaseModel):
    """Een bibliotheek-template die vanuit compose als PDF-bijlage kan."""

    template_key: str
    name: str
    description: str | None = None


# ── Merge Fields Schemas ──────────────────────────────────────────────────


# ── Send Document Schemas ─────────────────────────────────────────────────


class SendDocumentRequest(BaseModel):
    recipient_email: str = Field(
        ...,
        max_length=320,
        description="E-mailadres van de ontvanger",
    )
    recipient_name: str | None = Field(
        None,
        max_length=255,
        description="Naam van de ontvanger (voor aanhef in e-mail)",
    )
    cc: list[str] | None = Field(
        None,
        description="CC e-mailadressen",
    )
    custom_subject: str | None = Field(
        None,
        max_length=500,
        description="Eigen onderwerp (vervangt standaard template onderwerp)",
    )
    custom_body: str | None = Field(
        None,
        description="Eigen e-mail body tekst (wordt gewrapt in de standaard HTML layout)",
    )


class SendDocumentResponse(BaseModel):
    email_log_id: uuid.UUID
    recipient: str
    subject: str
    status: str


class EmailLogResponse(BaseModel):
    id: uuid.UUID
    recipient: str
    subject: str
    status: str
    error_message: str | None
    sent_at: datetime
    document_id: uuid.UUID | None
    template: str
    case_id: uuid.UUID | None

    model_config = {"from_attributes": True}


# ── Merge Fields Schemas ──────────────────────────────────────────────────


class MergeFieldItem(BaseModel):
    key: str = Field(..., description="Merge field key, e.g. 'kantoor.naam'")
    label: str = Field(..., description="Nederlandse label, e.g. 'Kantoornaam'")


class MergeFieldCategory(BaseModel):
    category: str = Field(..., description="Category key, e.g. 'kantoor'")
    label: str = Field(..., description="Nederlandse categorie label, e.g. 'Kantoor'")
    fields: list[MergeFieldItem]
