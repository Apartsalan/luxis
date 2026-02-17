"""Cases module endpoints — CRUD for cases, parties, and activities."""

import math
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.cases import service
from app.cases.schemas import (
    CaseActivityCreate,
    CaseActivityResponse,
    CaseCreate,
    CaseDetailResponse,
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
    per_page: int = Query(default=20, ge=1, le=100),
    case_type: str | None = Query(default=None),
    case_status: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
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
        is_active=is_active,
    )

    return PaginatedResponse(
        items=[CaseSummary.model_validate(c) for c in cases],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


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
    return case


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full case detail with parties and recent activities."""
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
