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


# ── Merge Fields Schemas ──────────────────────────────────────────────────


class MergeFieldItem(BaseModel):
    key: str = Field(..., description="Merge field key, e.g. 'kantoor.naam'")
    label: str = Field(..., description="Nederlandse label, e.g. 'Kantoornaam'")


class MergeFieldCategory(BaseModel):
    category: str = Field(..., description="Category key, e.g. 'kantoor'")
    label: str = Field(..., description="Nederlandse categorie label, e.g. 'Kantoor'")
    fields: list[MergeFieldItem]
