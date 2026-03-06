"""Case file upload/download service — handles file storage and CRUD."""

import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import CaseFile
from app.cases.schemas import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    CaseFileResponse,
)

# Base upload directory — inside Docker container
UPLOADS_BASE = Path("/app/uploads")


def _get_storage_path(tenant_id: uuid.UUID, case_id: uuid.UUID) -> Path:
    """Get the storage directory for a tenant/case combination."""
    path = UPLOADS_BASE / str(tenant_id) / str(case_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _validate_file(file: UploadFile) -> tuple[str, str]:
    """Validate file type and extension. Returns (content_type, extension)."""
    if not file.filename:
        raise ValueError("Bestandsnaam is verplicht")

    # Check extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Bestandstype '{ext}' is niet toegestaan. "
            f"Toegestaan: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Use file's content type, fallback to octet-stream
    content_type = file.content_type or "application/octet-stream"

    return content_type, ext


async def upload_case_file(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    user_id: uuid.UUID,
    file: UploadFile,
    description: str | None = None,
    document_direction: str | None = None,
) -> CaseFile:
    """Upload a file and create a CaseFile record."""
    content_type, ext = _validate_file(file)

    # Read file content and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(
            f"Bestand is te groot ({len(content) // (1024*1024)} MB). "
            f"Maximum: {MAX_FILE_SIZE // (1024*1024)} MB."
        )

    # Generate unique stored filename
    stored_filename = f"{uuid.uuid4()}{ext}"
    storage_path = _get_storage_path(tenant_id, case_id)
    file_path = storage_path / stored_filename

    # Write to disk
    file_path.write_bytes(content)

    # Create database record
    case_file = CaseFile(
        tenant_id=tenant_id,
        case_id=case_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_size=len(content),
        content_type=content_type,
        document_direction=document_direction,
        description=description,
        uploaded_by=user_id,
    )
    db.add(case_file)
    await db.commit()
    await db.refresh(case_file)
    return case_file


async def list_case_files(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> list[CaseFile]:
    """List all active files for a case, newest first."""
    result = await db.execute(
        select(CaseFile)
        .where(
            CaseFile.tenant_id == tenant_id,
            CaseFile.case_id == case_id,
            CaseFile.is_active.is_(True),
        )
        .order_by(CaseFile.created_at.desc())
    )
    return list(result.scalars().all())


async def get_case_file(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    file_id: uuid.UUID,
) -> CaseFile | None:
    """Get a single case file by ID."""
    result = await db.execute(
        select(CaseFile).where(
            CaseFile.id == file_id,
            CaseFile.tenant_id == tenant_id,
            CaseFile.case_id == case_id,
            CaseFile.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


def get_file_path(case_file: CaseFile) -> Path:
    """Get the full filesystem path for a CaseFile."""
    return (
        UPLOADS_BASE
        / str(case_file.tenant_id)
        / str(case_file.case_id)
        / case_file.stored_filename
    )


async def delete_case_file(
    db: AsyncSession,
    case_file: CaseFile,
) -> None:
    """Soft-delete a case file (keeps file on disk for recovery)."""
    case_file.is_active = False
    await db.commit()


def to_response(case_file: CaseFile) -> CaseFileResponse:
    """Convert CaseFile model to response schema."""
    uploader_name = None
    if case_file.uploader:
        uploader_name = case_file.uploader.full_name

    return CaseFileResponse(
        id=case_file.id,
        case_id=case_file.case_id,
        original_filename=case_file.original_filename,
        file_size=case_file.file_size,
        content_type=case_file.content_type,
        document_direction=case_file.document_direction,
        description=case_file.description,
        uploaded_by=case_file.uploaded_by,
        uploader_name=uploader_name,
        created_at=case_file.created_at,
    )
