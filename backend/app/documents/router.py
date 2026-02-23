"""Documents module router — template management and document generation."""

import logging
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
from app.documents.pdf_service import docx_to_pdf
from app.documents.schemas import (
    DocumentTemplateCreate,
    DocumentTemplateResponse,
    DocumentTemplateSummary,
    DocumentTemplateUpdate,
    DocxTemplateInfo,
    EmailLogResponse,
    GeneratedDocumentDetail,
    GeneratedDocumentResponse,
    GeneratedDocumentSummary,
    GenerateDocumentRequest,
    GenerateDocxRequest,
    MergeFieldCategory,
    SendDocumentRequest,
    SendDocumentResponse,
)
from app.email.models import EmailLog
from app.email.service import send_email
from app.email.templates import _render_base, document_sent
from app.shared.exceptions import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# ── HTML Template Endpoints (DEPRECATED — use /docx/ endpoints instead) ─────


@router.get(
    "/templates",
    response_model=list[DocumentTemplateSummary],
    deprecated=True,
)
async def list_templates(
    template_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """DEPRECATED: List HTML document templates. Use /docx/templates instead."""
    return await service.list_templates(
        db, user.tenant_id, template_type
    )


@router.post(
    "/templates",
    response_model=DocumentTemplateResponse,
    status_code=201,
    deprecated=True,
)
async def create_template(
    data: DocumentTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """DEPRECATED: Create HTML template. Use .docx templates instead."""
    return await service.create_template(db, user.tenant_id, data)


@router.get(
    "/templates/{template_id}",
    response_model=DocumentTemplateResponse,
    deprecated=True,
)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """DEPRECATED: Get HTML template by ID. Use /docx/templates instead."""
    return await service.get_template(
        db, user.tenant_id, template_id
    )


@router.put(
    "/templates/{template_id}",
    response_model=DocumentTemplateResponse,
    deprecated=True,
)
async def update_template(
    template_id: uuid.UUID,
    data: DocumentTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """DEPRECATED: Update HTML template. Use .docx templates instead."""
    return await service.update_template(
        db, user.tenant_id, template_id, data
    )


@router.delete("/templates/{template_id}", status_code=204, deprecated=True)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """DEPRECATED: Delete HTML template. Use .docx templates instead."""
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
    deprecated=True,
)
async def generate_document(
    case_id: uuid.UUID,
    data: GenerateDocumentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """DEPRECATED: Generate HTML document. Use /docx/cases/{case_id}/generate instead."""
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


# ── Document Preview Endpoint (G11) ──────────────────────────────────────


@router.get("/{document_id}/preview")
async def preview_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Preview a generated document as inline PDF.

    Re-renders the DOCX template with current case data and converts to PDF.
    Returns PDF bytes with Content-Disposition: inline for browser preview.
    """
    doc = await service.get_generated_document(
        db, user.tenant_id, document_id
    )

    if not doc.template_type:
        raise BadRequestError(
            "Document heeft geen sjabloontype — preview niet mogelijk"
        )

    # Load the case
    result = await db.execute(
        select(Case).where(
            Case.id == doc.case_id,
            Case.tenant_id == user.tenant_id,
        )
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise NotFoundError("Zaak niet gevonden")

    # Re-render and convert to PDF
    docx_bytes, filename, _, _ = await render_docx(
        db, user.tenant_id, case, doc.template_type
    )
    pdf_bytes = await docx_to_pdf(docx_bytes)
    pdf_filename = filename.replace(".docx", ".pdf")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{pdf_filename}"'},
    )


# ── Send Document Endpoint ────────────────────────────────────────────────


@router.post(
    "/{document_id}/send",
    response_model=SendDocumentResponse,
)
async def send_document(
    document_id: uuid.UUID,
    data: SendDocumentRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate PDF from a document and send it via email.

    Re-renders the DOCX template with current case data, converts to PDF,
    and sends as email attachment. Logs the result in email_logs.
    """
    from app.documents.docx_service import _load_tenant, _tenant_ctx

    # Load the generated document
    doc = await service.get_generated_document(
        db, user.tenant_id, document_id
    )

    if not doc.template_type:
        raise BadRequestError(
            "Document heeft geen sjabloontype — alleen DOCX-documenten kunnen worden verzonden"
        )

    # Load the case
    result = await db.execute(
        select(Case).where(
            Case.id == doc.case_id,
            Case.tenant_id == user.tenant_id,
        )
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise NotFoundError("Zaak niet gevonden")

    # Re-render the DOCX with current case data
    docx_bytes, filename, _, _ = await render_docx(
        db, user.tenant_id, case, doc.template_type
    )

    # Convert to PDF
    pdf_bytes = await docx_to_pdf(docx_bytes)
    pdf_filename = filename.replace(".docx", ".pdf")

    # Build email from template or custom content
    tenant = await _load_tenant(db, user.tenant_id)
    kantoor = _tenant_ctx(tenant)

    if data.custom_subject or data.custom_body:
        # Use custom subject/body from the frontend compose dialog
        subject = data.custom_subject or f"{doc.title} — {case.case_number}"
        if data.custom_body:
            # Wrap custom body text in base HTML layout (convert newlines to <br>)
            body_html = data.custom_body.replace("\n", "<br>")
            html_body = _render_base(kantoor, body_html)
        else:
            _, html_body = document_sent(
                kantoor=kantoor,
                recipient_name=data.recipient_name or "",
                document_title=doc.title,
                case_number=case.case_number,
            )
        template_name = "custom"
    else:
        subject, html_body = document_sent(
            kantoor=kantoor,
            recipient_name=data.recipient_name or "",
            document_title=doc.title,
            case_number=case.case_number,
        )
        template_name = "document_sent"

    # Send email
    email_log = EmailLog(
        tenant_id=user.tenant_id,
        case_id=case.id,
        document_id=doc.id,
        template=template_name,
        recipient=data.recipient_email,
        subject=subject,
        status="sent",
    )

    try:
        await send_email(
            to=data.recipient_email,
            subject=subject,
            html_body=html_body,
            cc=data.cc,
            attachments=[(pdf_filename, pdf_bytes, "pdf")],
        )
    except Exception as e:
        email_log.status = "failed"
        email_log.error_message = str(e)
        logger.error(f"Email verzenden mislukt voor document {document_id}: {e}")

    db.add(email_log)
    await db.flush()
    await db.refresh(email_log)

    if email_log.status == "failed":
        raise BadRequestError(
            f"E-mail verzenden mislukt: {email_log.error_message}"
        )

    return SendDocumentResponse(
        email_log_id=email_log.id,
        recipient=email_log.recipient,
        subject=email_log.subject,
        status=email_log.status,
    )


# ── Email Logs ───────────────────────────────────────────────────────────────


@router.get(
    "/cases/{case_id}/email-logs",
    response_model=list[EmailLogResponse],
)
async def list_email_logs(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all email logs for a case, newest first."""
    result = await db.execute(
        select(EmailLog)
        .where(
            EmailLog.tenant_id == user.tenant_id,
            EmailLog.case_id == case_id,
        )
        .order_by(EmailLog.sent_at.desc())
    )
    return list(result.scalars().all())
