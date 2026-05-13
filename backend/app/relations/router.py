"""Relations module endpoints — CRUD for contacts and contact links."""

import math
import os
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile, status
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
    ContactTermsCreate,
    ContactTermsResponse,
    ContactTermsUpdate,
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
    sort_by: str = Query(
        default="name",
        pattern="^(name|contact_type|visit_city|email|created_at)$",
    ),
    sort_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List contacts with pagination, filtering and sorting."""
    contacts, total = await service.list_contacts(
        db,
        current_user.tenant_id,
        page=page,
        per_page=per_page,
        contact_type=contact_type,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_dir=sort_dir,
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


# ── Algemene Voorwaarden — versie-aware (S140) ──────────────────────────────

TERMS_BASE = Path("/app/uploads/terms")
ALLOWED_TERMS_EXT = {".pdf", ".docx", ".doc"}
MAX_TERMS_SIZE = 10 * 1024 * 1024  # 10 MB


@router.get("/{contact_id}/terms", response_model=list[ContactTermsResponse])
async def list_terms(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lijst van alle AV-versies van een cliënt."""
    versions = await service.list_contact_terms(db, current_user.tenant_id, contact_id)
    return [ContactTermsResponse.model_validate(v) for v in versions]


@router.post(
    "/{contact_id}/terms",
    response_model=ContactTermsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_terms(
    contact_id: uuid.UUID,
    file: UploadFile,
    label: str | None = Form(default=None),
    valid_from: date | None = Form(default=None),
    valid_to: date | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload nieuwe AV-versie. Metadata via form-fields naast multipart file."""
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

    # Store file met unieke naam per versie (UUID-prefix), zodat oudere
    # versies naast nieuwe op disk kunnen bestaan.
    tenant_dir = TERMS_BASE / str(current_user.tenant_id)
    tenant_dir.mkdir(parents=True, exist_ok=True)
    version_id = uuid.uuid4()
    storage_name = f"{contact_id}_{version_id}{ext}"
    file_path = tenant_dir / storage_name
    file_path.write_bytes(content)

    metadata = ContactTermsCreate(label=label, valid_from=valid_from, valid_to=valid_to)
    try:
        terms = await service.create_contact_terms(
            db,
            current_user.tenant_id,
            contact_id,
            file_path=str(file_path),
            file_name=file.filename,
            metadata=metadata,
            uploaded_by_id=current_user.id,
        )
        await db.commit()
    except Exception:
        if file_path.exists():
            file_path.unlink()
        raise

    return ContactTermsResponse.model_validate(terms)


@router.get("/{contact_id}/terms/{terms_id}/file")
async def download_terms_version(
    contact_id: uuid.UUID,
    terms_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download bestand van specifieke AV-versie."""
    terms = await service.get_contact_terms(db, current_user.tenant_id, terms_id)
    if terms.contact_id != contact_id:
        raise HTTPException(status_code=404, detail="AV-versie hoort niet bij deze cliënt")

    file_path = Path(terms.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Bestand niet gevonden")

    return FileResponse(
        path=str(file_path),
        filename=terms.file_name,
        media_type="application/octet-stream",
    )


@router.put(
    "/{contact_id}/terms/{terms_id}",
    response_model=ContactTermsResponse,
)
async def update_terms_version(
    contact_id: uuid.UUID,
    terms_id: uuid.UUID,
    data: ContactTermsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update metadata (label, valid_from, valid_to) van AV-versie."""
    terms = await service.get_contact_terms(db, current_user.tenant_id, terms_id)
    if terms.contact_id != contact_id:
        raise HTTPException(status_code=404, detail="AV-versie hoort niet bij deze cliënt")
    updated = await service.update_contact_terms(db, current_user.tenant_id, terms_id, data)
    await db.commit()
    return ContactTermsResponse.model_validate(updated)


@router.delete(
    "/{contact_id}/terms/{terms_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_terms_version(
    contact_id: uuid.UUID,
    terms_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verwijder AV-versie. Dossiers die hiernaar wezen krijgen contact_terms_id=NULL."""
    terms = await service.get_contact_terms(db, current_user.tenant_id, terms_id)
    if terms.contact_id != contact_id:
        raise HTTPException(status_code=404, detail="AV-versie hoort niet bij deze cliënt")

    file_path_str = await service.delete_contact_terms(db, current_user.tenant_id, terms_id)
    await db.commit()

    # File pas verwijderen na succesvolle DB-commit
    if file_path_str:
        file_path = Path(file_path_str)
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                # Bestand kan al weg zijn, geen probleem
                pass

    return {"message": "AV-versie verwijderd"}
