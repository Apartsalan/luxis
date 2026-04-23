"""API endpoints for managed DOCX templates."""

import io
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.cases.models import Case
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.documents import template_service
from app.documents.template_schemas import (
    ManagedTemplateResponse,
    ManagedTemplateUpdate,
)
from app.shared.exceptions import NotFoundError
from app.shared.sanitize import content_disposition

router = APIRouter(
    prefix="/managed-templates",
    tags=["managed-templates"],
)


@router.get("", response_model=list[ManagedTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all active managed templates for the tenant."""
    return await template_service.list_managed_templates(db, user.tenant_id)


@router.post(
    "/upload",
    response_model=ManagedTemplateResponse,
    status_code=201,
)
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    template_key: str = Form(...),
    description: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Upload a new .docx template (admin only)."""
    return await template_service.upload_template(
        db,
        user.tenant_id,
        file=file,
        name=name,
        template_key=template_key,
        description=description,
    )


@router.get(
    "/{template_id}",
    response_model=ManagedTemplateResponse,
)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single managed template."""
    return await template_service.get_managed_template(db, user.tenant_id, template_id)


@router.put(
    "/{template_id}",
    response_model=ManagedTemplateResponse,
)
async def update_template(
    template_id: uuid.UUID,
    data: ManagedTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Update template metadata (admin only)."""
    return await template_service.update_template(db, user.tenant_id, template_id, data)


@router.post(
    "/{template_id}/replace",
    response_model=ManagedTemplateResponse,
)
async def replace_template_file(
    template_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Replace the .docx file for an existing template (admin only)."""
    return await template_service.replace_template_file(db, user.tenant_id, template_id, file)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Soft-delete a custom template (admin only)."""
    await template_service.delete_template(db, user.tenant_id, template_id)


@router.get("/{template_id}/download")
async def download_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download the original .docx template file."""
    tpl = await template_service.get_managed_template(db, user.tenant_id, template_id)
    return Response(
        content=tpl.file_data,
        media_type=("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        headers={"Content-Disposition": (content_disposition("attachment", tpl.original_filename))},
    )


@router.post("/{template_id}/preview/{case_id}")
async def preview_template(
    template_id: uuid.UUID,
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Render a template with real case data and return .docx."""
    from docxtpl import DocxTemplate

    from app.documents.docx_service import (
        _build_base_context,
        _build_renteoverzicht_context,
    )

    tpl = await template_service.get_managed_template(db, user.tenant_id, template_id)

    # Load case
    result = await db.execute(
        select(Case).where(
            Case.id == case_id,
            Case.tenant_id == user.tenant_id,
        )
    )
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError("Zaak niet gevonden")

    # Build context
    if tpl.template_key == "renteoverzicht":
        context = await _build_renteoverzicht_context(db, user.tenant_id, case)
    else:
        context = await _build_base_context(db, user.tenant_id, case)

    render_context = {k: v for k, v in context.items() if not k.startswith("_")}

    # Render
    doc = DocxTemplate(io.BytesIO(tpl.file_data))
    doc.render(render_context)

    buffer = io.BytesIO()
    doc.save(buffer)
    docx_bytes = buffer.getvalue()

    filename = f"preview_{tpl.template_key}_{case.case_number}.docx"

    return Response(
        content=docx_bytes,
        media_type=("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        headers={"Content-Disposition": (content_disposition("attachment", filename))},
    )
