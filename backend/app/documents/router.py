"""Documents module router — template management and document generation."""

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.cases.models import Case
from app.database import get_db
from app.dependencies import get_current_user
from app.documents import service
from app.documents.docx_service import (
    get_available_templates,
    get_merge_field_definitions,
    render_docx,
)
from app.documents.models import GeneratedDocument
from app.documents.schemas import (
    DocxTemplateInfo,
    DocumentTemplateCreate,
    DocumentTemplateResponse,
    DocumentTemplateSummary,
    DocumentTemplateUpdate,
    GenerateDocumentRequest,
    GenerateDocxRequest,
    GeneratedDocumentDetail,
    GeneratedDocumentResponse,
    GeneratedDocumentSummary,
    MergeFieldCategory,
)
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/documents", tags=["documents"])

# ── Template Endpoints ───────────────────────────────────────────────────────


@router.get("/templates", response_model=list[DocumentTemplateSummary])
async def list_templates(
    template_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all document templates."""
    return await service.list_templates(
        db, user.tenant_id, template_type
    )


@router.post(
    "/templates",
    response_model=DocumentTemplateResponse,
    status_code=201,
)
async def create_template(
    data: DocumentTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new document template."""
    return await service.create_template(db, user.tenant_id, data)


@router.get(
    "/templates/{template_id}",
    response_model=DocumentTemplateResponse,
)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a document template by ID."""
    return await service.get_template(
        db, user.tenant_id, template_id
    )


@router.put(
    "/templates/{template_id}",
    response_model=DocumentTemplateResponse,
)
async def update_template(
    template_id: uuid.UUID,
    data: DocumentTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a document template."""
    return await service.update_template(
        db, user.tenant_id, template_id, data
    )


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a document template."""
    await service.delete_template(db, user.tenant_id, template_id)


# ── Generated Document Endpoints ─────────────────────────────────────────────


@router.get(
    "/cases/{case_id}",
    response_model=list[GeneratedDocumentSummary],
)
async def list_case_documents(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all generated documents for a case."""
    return await service.list_generated_documents(
        db, user.tenant_id, case_id
    )


@router.post(
    "/cases/{case_id}/generate",
    response_model=GeneratedDocumentResponse,
    status_code=201,
)
async def generate_document(
    case_id: uuid.UUID,
    data: GenerateDocumentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate a document from a template for a case."""
    return await service.generate_document(
        db, user.tenant_id, case_id, user.id, data
    )


@router.get(
    "/{document_id}",
    response_model=GeneratedDocumentDetail,
)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a generated document by ID."""
    return await service.get_generated_document(
        db, user.tenant_id, document_id
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a generated document."""
    await service.delete_generated_document(
        db, user.tenant_id, document_id
    )


# ── Merge Fields Endpoint ──────────────────────────────────────────────────


@router.get(
    "/merge-fields",
    response_model=list[MergeFieldCategory],
)
async def list_merge_fields():
    """Return all available merge fields grouped by category with NL labels.

    Used by the template editor to show which fields can be inserted.
    """
    definitions = get_merge_field_definitions()
    return [
        {
            "category": cat_key,
            "label": cat_data["label"],
            "fields": [
                {"key": key, "label": label}
                for key, label in cat_data["fields"]
            ],
        }
        for cat_key, cat_data in definitions.items()
    ]


# ── Docx Template Endpoints ────────────────────────────────────────────────


@router.get(
    "/docx/templates",
    response_model=list[DocxTemplateInfo],
)
async def list_docx_templates():
    """List available .docx template types."""
    return get_available_templates()


@router.post("/docx/cases/{case_id}/generate")
async def generate_docx(
    case_id: uuid.UUID,
    data: GenerateDocxRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate a .docx document from a template for a case.

    Returns the Word document as a downloadable file.
    """
    # Get the case
    result = await db.execute(
        select(Case).where(
            Case.id == case_id,
            Case.tenant_id == user.tenant_id,
        )
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise NotFoundError("Zaak niet gevonden")

    docx_bytes, filename, tpl_type, tpl_snapshot = await render_docx(
        db, user.tenant_id, case, data.template_type
    )

    # Store GeneratedDocument with template_type and snapshot
    doc = GeneratedDocument(
        tenant_id=user.tenant_id,
        case_id=case_id,
        generated_by_id=user.id,
        title=f"{tpl_type} - {case.case_number}",
        document_type=tpl_type,
        template_type=tpl_type,
        template_snapshot=tpl_snapshot,
    )
    db.add(doc)
    await db.flush()

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
