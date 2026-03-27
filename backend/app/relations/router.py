"""Relations module endpoints — CRUD for contacts and contact links."""

import math
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.relations import service
from app.relations.schemas import (
    ConflictCheckRequest,
    ConflictCheckResult,
    ContactCreate,
    ContactDetailResponse,
    ContactLinkCreate,
    ContactLinkResponse,
    ContactResponse,
    ContactSummary,
    ContactUpdate,
    LinkedContactInfo,
)
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/api/relations", tags=["relations"])


# ── Contact CRUD ─────────────────────────────────────────────────────────────


@router.get("", response_model=PaginatedResponse)
async def list_contacts(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=200),
    contact_type: str | None = Query(default=None, pattern="^(company|person)$"),
    search: str | None = Query(default=None),
    is_active: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List contacts with pagination and filtering."""
    contacts, total = await service.list_contacts(
        db,
        current_user.tenant_id,
        page=page,
        per_page=per_page,
        contact_type=contact_type,
        search=search,
        is_active=is_active,
    )

    return PaginatedResponse(
        items=[ContactSummary.model_validate(c) for c in contacts],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new contact (company or person)."""
    contact = await service.create_contact(db, current_user.tenant_id, data)
    return contact


@router.get("/{contact_id}", response_model=ContactDetailResponse)
async def get_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full contact detail including linked companies/persons."""
    contact = await service.get_contact(db, current_user.tenant_id, contact_id)

    # Build linked companies/persons from the loaded relationships
    linked_companies = []
    linked_persons = []

    if contact.contact_type == "person":
        for link in contact.company_links:
            if link.is_active and link.company:
                linked_companies.append(
                    LinkedContactInfo(
                        link_id=link.id,
                        role_at_company=link.role_at_company,
                        contact=ContactSummary.model_validate(link.company),
                    )
                )
    elif contact.contact_type == "company":
        for link in contact.person_links:
            if link.is_active and link.person:
                linked_persons.append(
                    LinkedContactInfo(
                        link_id=link.id,
                        role_at_company=link.role_at_company,
                        contact=ContactSummary.model_validate(link.person),
                    )
                )

    response = ContactDetailResponse.model_validate(contact)
    response.linked_companies = linked_companies
    response.linked_persons = linked_persons
    return response


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: uuid.UUID,
    data: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing contact."""
    contact = await service.update_contact(db, current_user.tenant_id, contact_id, data)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a contact (set is_active=false)."""
    await service.delete_contact(db, current_user.tenant_id, contact_id)


# ── Contact Links ────────────────────────────────────────────────────────────


@router.post("/links", response_model=ContactLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_contact_link(
    data: ContactLinkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a person to a company."""
    link = await service.create_contact_link(db, current_user.tenant_id, data)
    return link


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact_link(
    link_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a person-company link."""
    await service.delete_contact_link(db, current_user.tenant_id, link_id)


# ── Conflict Check ───────────────────────────────────────────────────────────


@router.post("/conflict-check", response_model=ConflictCheckResult)
async def conflict_check(
    data: ConflictCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run a conflict check by searching contacts by name, KvK, or email."""
    matches = await service.conflict_check(db, current_user.tenant_id, data.search_query)

    return ConflictCheckResult(
        search_query=data.search_query,
        results_found=len(matches),
        matches=[ContactSummary.model_validate(c) for c in matches],
    )


# ── Algemene Voorwaarden (AI-UX-11) ─────────────────────────────────────────

TERMS_BASE = Path("/app/uploads/terms")
ALLOWED_TERMS_EXT = {".pdf", ".docx", ".doc"}
MAX_TERMS_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/{contact_id}/terms", status_code=status.HTTP_200_OK)
async def upload_terms(
    contact_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload algemene voorwaarden (AV) for a contact."""
    contact = await service.get_contact(db, current_user.tenant_id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Relatie niet gevonden")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Bestandsnaam is verplicht")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_TERMS_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Bestandstype '{ext}' niet toegestaan. Gebruik: {', '.join(ALLOWED_TERMS_EXT)}",
        )

    content = await file.read()
    if len(content) > MAX_TERMS_SIZE:
        raise HTTPException(status_code=400, detail="Bestand te groot (max 10 MB)")

    # Store file
    tenant_dir = TERMS_BASE / str(current_user.tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    storage_name = f"{contact_id}{ext}"
    file_path = tenant_dir / storage_name
    file_path.write_bytes(content)

    # Update contact
    contact.terms_file_path = str(file_path)
    contact.terms_file_name = file.filename
    await db.commit()

    return {
        "terms_file_name": file.filename,
        "message": "Algemene voorwaarden geüpload",
    }


@router.get("/{contact_id}/terms")
async def download_terms(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download algemene voorwaarden (AV) for a contact."""
    contact = await service.get_contact(db, current_user.tenant_id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Relatie niet gevonden")

    if not contact.terms_file_path:
        raise HTTPException(status_code=404, detail="Geen algemene voorwaarden geüpload")

    file_path = Path(contact.terms_file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Bestand niet gevonden")

    return FileResponse(
        path=str(file_path),
        filename=contact.terms_file_name or "voorwaarden.pdf",
        media_type="application/octet-stream",
    )


@router.delete("/{contact_id}/terms", status_code=status.HTTP_200_OK)
async def delete_terms(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete algemene voorwaarden (AV) for a contact."""
    contact = await service.get_contact(db, current_user.tenant_id, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Relatie niet gevonden")

    if contact.terms_file_path:
        file_path = Path(contact.terms_file_path)
        if file_path.exists():
            file_path.unlink()

    contact.terms_file_path = None
    contact.terms_file_name = None
    await db.commit()

    return {"message": "Algemene voorwaarden verwijderd"}
