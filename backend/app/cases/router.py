"""Cases module endpoints — CRUD for cases, parties, activities, and file uploads."""

import math
import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.cases import files_service, service
from app.cases.schemas import (
    CaseActivityCreate,
    CaseActivityResponse,
    CaseCreate,
    CaseDetailResponse,
    CaseEmailAttachmentResponse,
    CaseFileResponse,
    CasePartyCreate,
    CasePartyResponse,
    CaseResponse,
    CaseStatusUpdate,
    CaseSummary,
    CaseUpdate,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/api/cases", tags=["cases"])


# ── Case CRUD ────────────────────────────────────────────────────────────────


@router.get("", response_model=PaginatedResponse)
async def list_cases(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=200),
    case_type: str | None = Query(default=None),
    case_status: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    client_id: uuid.UUID | None = Query(default=None),
    assigned_to_id: uuid.UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    min_amount: float | None = Query(default=None, ge=0),
    max_amount: float | None = Query(default=None, ge=0),
    is_active: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List cases with pagination and filtering."""
    cases, total = await service.list_cases(
        db,
        current_user.tenant_id,
        page=page,
        per_page=per_page,
        case_type=case_type,
        status=case_status,
        search=search,
        client_id=client_id,
        assigned_to_id=assigned_to_id,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        is_active=is_active,
    )

    return PaginatedResponse(
        items=[CaseSummary.model_validate(c) for c in cases],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get("/conflict-check")
async def conflict_check(
    contact_id: uuid.UUID = Query(...),
    role: str = Query(..., description="client or opposing_party"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if a contact has conflicting roles in existing cases."""
    conflicts = await service.conflict_check(
        db, current_user.tenant_id, contact_id, role
    )
    return {"conflicts": conflicts, "has_conflict": len(conflicts) > 0}


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    data: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new case."""
    case = await service.create_case(
        db, current_user.tenant_id, current_user.id, data
    )
    await db.commit()
    await db.refresh(case)
    return case


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full case detail with parties and recent activities."""
    # Refresh cached financials to ensure accuracy
    from app.collections.service import _refresh_case_financials
    await _refresh_case_financials(db, current_user.tenant_id, case_id)
    await db.commit()

    case = await service.get_case(db, current_user.tenant_id, case_id)

    # Get recent activities (last 10)
    activities, _ = await service.list_activities(
        db, current_user.tenant_id, case_id, per_page=10
    )

    response = CaseDetailResponse.model_validate(case)
    response.parties = [CasePartyResponse.model_validate(p) for p in case.parties]
    response.recent_activities = [
        CaseActivityResponse.model_validate(a) for a in activities
    ]
    return response


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: uuid.UUID,
    data: CaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update case details (not status)."""
    case = await service.update_case(db, current_user.tenant_id, case_id, data)
    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a case."""
    await service.delete_case(db, current_user.tenant_id, case_id)


# ── Status Updates ───────────────────────────────────────────────────────────


@router.post("/{case_id}/status", response_model=CaseResponse)
async def update_status(
    case_id: uuid.UUID,
    data: CaseStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update case status (follows workflow transitions)."""
    case = await service.update_case_status(
        db, current_user.tenant_id, case_id, current_user.id, data
    )
    return case


# ── Case Parties ─────────────────────────────────────────────────────────────


@router.post(
    "/{case_id}/parties",
    response_model=CasePartyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_party(
    case_id: uuid.UUID,
    data: CasePartyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a party to a case (deurwaarder, rechtbank, etc.)."""
    party = await service.add_case_party(
        db, current_user.tenant_id, case_id, data
    )
    await db.commit()
    await db.refresh(party)
    return party


@router.delete("/{case_id}/parties/{party_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_party(
    case_id: uuid.UUID,
    party_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a party from a case."""
    await service.remove_case_party(db, current_user.tenant_id, party_id)


# ── Case Activities ──────────────────────────────────────────────────────────


@router.get("/{case_id}/activities", response_model=PaginatedResponse)
async def list_activities(
    case_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List activities for a case (newest first)."""
    activities, total = await service.list_activities(
        db, current_user.tenant_id, case_id, page=page, per_page=per_page
    )

    return PaginatedResponse(
        items=[CaseActivityResponse.model_validate(a) for a in activities],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.post(
    "/{case_id}/activities",
    response_model=CaseActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_activity(
    case_id: uuid.UUID,
    data: CaseActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a note/activity to a case."""
    activity = await service.add_activity(
        db, current_user.tenant_id, case_id, current_user.id, data
    )
    return activity


# ── Email Attachments (LF-17) ───────────────────────────────────────────────


@router.get(
    "/{case_id}/email-attachments",
    response_model=list[CaseEmailAttachmentResponse],
)
async def list_email_attachments(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List email attachments linked to this case via synced emails."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.email.attachment_models import EmailAttachment
    from app.email.synced_email_models import SyncedEmail

    stmt = (
        select(EmailAttachment)
        .join(SyncedEmail, EmailAttachment.synced_email_id == SyncedEmail.id)
        .where(
            SyncedEmail.case_id == case_id,
            SyncedEmail.tenant_id == current_user.tenant_id,
        )
        .options(selectinload(EmailAttachment.synced_email))
        .order_by(SyncedEmail.email_date.desc())
    )
    result = await db.execute(stmt)
    attachments = result.scalars().all()

    return [
        CaseEmailAttachmentResponse(
            id=att.id,
            filename=att.filename,
            file_size=att.file_size,
            content_type=att.content_type,
            email_subject=att.synced_email.subject if att.synced_email else None,
            email_date=(
                att.synced_email.email_date.isoformat()
                if att.synced_email and att.synced_email.email_date
                else None
            ),
            email_from=att.synced_email.from_email if att.synced_email else None,
            synced_email_id=att.synced_email_id,
        )
        for att in attachments
    ]


# ── Case Files (E4: Document uploads) ───────────────────────────────────────


@router.get("/{case_id}/files", response_model=list[CaseFileResponse])
async def list_files(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all uploaded files for a case."""
    case_files = await files_service.list_case_files(
        db, current_user.tenant_id, case_id
    )
    return [files_service.to_response(f) for f in case_files]


@router.post(
    "/{case_id}/files",
    response_model=CaseFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    case_id: uuid.UUID,
    file: UploadFile = File(...),
    description: str | None = Form(default=None),
    document_direction: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file to a case."""
    try:
        case_file = await files_service.upload_case_file(
            db,
            tenant_id=current_user.tenant_id,
            case_id=case_id,
            user_id=current_user.id,
            file=file,
            description=description,
            document_direction=document_direction,
        )
        return files_service.to_response(case_file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{case_id}/files/{file_id}/download")
async def download_file(
    case_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a case file."""
    case_file = await files_service.get_case_file(
        db, current_user.tenant_id, case_id, file_id
    )
    if not case_file:
        raise HTTPException(status_code=404, detail="Bestand niet gevonden")

    file_path = files_service.get_file_path(case_file)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Bestand niet gevonden op schijf")

    return FileResponse(
        path=str(file_path),
        filename=case_file.original_filename,
        media_type=case_file.content_type,
    )


# G11: Inline file preview
PREVIEWABLE_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.get("/{case_id}/files/{file_id}/preview")
async def preview_file(
    case_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview a case file inline in the browser.

    - PDF/images: served directly with Content-Disposition: inline
    - DOCX: converted to PDF on-the-fly via LibreOffice
    - Other types: returns 415 Unsupported Media Type
    """
    case_file = await files_service.get_case_file(
        db, current_user.tenant_id, case_id, file_id
    )
    if not case_file:
        raise HTTPException(status_code=404, detail="Bestand niet gevonden")

    if case_file.content_type not in PREVIEWABLE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Preview niet beschikbaar voor bestandstype: {case_file.content_type}",
        )

    file_path = files_service.get_file_path(case_file)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Bestand niet gevonden op schijf")

    # PDF and images: serve directly
    if case_file.content_type in ("application/pdf", "image/jpeg", "image/png", "image/gif"):
        return FileResponse(
            path=str(file_path),
            filename=case_file.original_filename,
            media_type=case_file.content_type,
            headers={"Content-Disposition": f'inline; filename="{case_file.original_filename}"'},
        )

    # DOCX: convert to PDF
    docx_mime = (
        "application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document"
    )
    if case_file.content_type == docx_mime:
        from app.documents.pdf_service import docx_to_pdf

        docx_bytes = file_path.read_bytes()
        pdf_bytes = await docx_to_pdf(docx_bytes)
        pdf_name = case_file.original_filename.rsplit(".", 1)[0] + ".pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{pdf_name}"'},
        )

    raise HTTPException(status_code=415, detail="Preview niet ondersteund")


@router.delete("/{case_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    case_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a case file."""
    case_file = await files_service.get_case_file(
        db, current_user.tenant_id, case_id, file_id
    )
    if not case_file:
        raise HTTPException(status_code=404, detail="Bestand niet gevonden")

    await files_service.delete_case_file(db, case_file)
