"""Service layer for managed DOCX templates."""

import uuid

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models import ManagedTemplate
from app.documents.template_schemas import ManagedTemplateUpdate
from app.shared.exceptions import BadRequestError, NotFoundError

ALLOWED_EXTENSIONS = {".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# DOCX magic bytes: PK zip header (all .docx files are zip archives)
_DOCX_MAGIC = b"PK\x03\x04"


def _validate_docx_magic(data: bytes) -> None:
    """Verify that file content starts with the DOCX/ZIP magic bytes."""
    if not data.startswith(_DOCX_MAGIC):
        raise BadRequestError(
            "Bestand is geen geldig .docx bestand (ongeldige bestandsinhoud)"
        )


async def list_managed_templates(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    active_only: bool = True,
) -> list[ManagedTemplate]:
    """List all managed templates for a tenant."""
    query = select(ManagedTemplate).where(
        ManagedTemplate.tenant_id == tenant_id,
    )
    if active_only:
        query = query.where(ManagedTemplate.is_active.is_(True))
    query = query.order_by(
        ManagedTemplate.template_key,
        ManagedTemplate.is_builtin.asc(),
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_managed_template(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    template_id: uuid.UUID,
) -> ManagedTemplate:
    """Get a single managed template by ID."""
    result = await db.execute(
        select(ManagedTemplate).where(
            ManagedTemplate.tenant_id == tenant_id,
            ManagedTemplate.id == template_id,
            ManagedTemplate.is_active.is_(True),
        )
    )
    tpl = result.scalar_one_or_none()
    if not tpl:
        raise NotFoundError("Sjabloon niet gevonden")
    return tpl


async def get_template_by_key(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    template_key: str,
) -> ManagedTemplate | None:
    """Find the best template for a given key.

    Priority: custom (non-builtin) > builtin, newest first.
    """
    result = await db.execute(
        select(ManagedTemplate)
        .where(
            ManagedTemplate.tenant_id == tenant_id,
            ManagedTemplate.template_key == template_key,
            ManagedTemplate.is_active.is_(True),
        )
        .order_by(
            ManagedTemplate.is_builtin.asc(),  # custom first
            ManagedTemplate.updated_at.desc(),
        )
    )
    return result.scalars().first()


async def upload_template(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    file: UploadFile,
    name: str,
    template_key: str,
    description: str | None = None,
) -> ManagedTemplate:
    """Upload a new .docx template."""
    # Validate filename
    filename = file.filename or "unknown.docx"
    if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise BadRequestError(
            "Alleen .docx bestanden zijn toegestaan"
        )

    # Read file data
    file_data = await file.read()
    file_size = len(file_data)

    if file_size == 0:
        raise BadRequestError("Leeg bestand")
    if file_size > MAX_FILE_SIZE:
        raise BadRequestError("Bestand te groot (max 10 MB)")

    _validate_docx_magic(file_data)

    tpl = ManagedTemplate(
        tenant_id=tenant_id,
        name=name,
        description=description,
        template_key=template_key,
        file_data=file_data,
        original_filename=filename,
        file_size=file_size,
        is_builtin=False,
        is_active=True,
    )
    db.add(tpl)
    await db.flush()
    await db.refresh(tpl)
    return tpl


async def update_template(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    template_id: uuid.UUID,
    data: ManagedTemplateUpdate,
) -> ManagedTemplate:
    """Update template metadata."""
    tpl = await get_managed_template(db, tenant_id, template_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tpl, field, value)
    await db.flush()
    await db.refresh(tpl)
    return tpl


async def replace_template_file(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    template_id: uuid.UUID,
    file: UploadFile,
) -> ManagedTemplate:
    """Replace the .docx file for an existing template."""
    tpl = await get_managed_template(db, tenant_id, template_id)

    filename = file.filename or "unknown.docx"
    if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise BadRequestError(
            "Alleen .docx bestanden zijn toegestaan"
        )

    file_data = await file.read()
    if len(file_data) == 0:
        raise BadRequestError("Leeg bestand")
    if len(file_data) > MAX_FILE_SIZE:
        raise BadRequestError("Bestand te groot (max 10 MB)")

    _validate_docx_magic(file_data)

    tpl.file_data = file_data
    tpl.original_filename = filename
    tpl.file_size = len(file_data)
    await db.flush()
    await db.refresh(tpl)
    return tpl


async def delete_template(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    template_id: uuid.UUID,
) -> None:
    """Soft-delete a template. Builtin templates cannot be deleted."""
    tpl = await get_managed_template(db, tenant_id, template_id)
    if tpl.is_builtin:
        raise BadRequestError(
            "Standaard-sjablonen kunnen niet worden verwijderd"
        )
    tpl.is_active = False
    await db.flush()
