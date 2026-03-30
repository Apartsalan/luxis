"""Follow-up router — endpoints for follow-up recommendation review and execution."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.followup_schemas import (
    FollowupRecommendationList,
    FollowupRecommendationOut,
    FollowupRejectIn,
    FollowupStatsOut,
)
from app.ai_agent.followup_service import (
    approve_and_execute_recommendation,
    approve_recommendation,
    execute_recommendation,
    get_recommendation,
    get_recommendation_stats,
    list_recommendations,
    reject_recommendation,
)
from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/followup", tags=["followup"])


@router.get("", response_model=FollowupRecommendationList)
async def list_followups(
    status_filter: str | None = Query(default=None, alias="status"),
    case_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List follow-up recommendations with optional status filter."""
    return await list_recommendations(
        db,
        current_user.tenant_id,
        status_filter=status_filter,
        case_id=case_id,
        page=page,
        per_page=per_page,
    )


@router.get("/stats", response_model=FollowupStatsOut)
async def followup_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recommendation counts per status."""
    return await get_recommendation_stats(db, current_user.tenant_id)


@router.get("/{rec_id}", response_model=FollowupRecommendationOut)
async def get_followup(
    rec_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single follow-up recommendation."""
    rec = await get_recommendation(db, current_user.tenant_id, rec_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aanbeveling niet gevonden",
        )
    return rec


@router.post("/{rec_id}/approve", response_model=FollowupRecommendationOut)
async def approve_followup(
    rec_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending recommendation."""
    rec = await approve_recommendation(db, current_user.tenant_id, rec_id, current_user.id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aanbeveling niet gevonden of niet in status 'pending'",
        )
    await db.commit()
    result = await get_recommendation(db, current_user.tenant_id, rec_id)
    return result


@router.post("/{rec_id}/reject", response_model=FollowupRecommendationOut)
async def reject_followup(
    rec_id: uuid.UUID,
    body: FollowupRejectIn | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a pending recommendation."""
    note = body.note if body else None
    rec = await reject_recommendation(db, current_user.tenant_id, rec_id, current_user.id, note)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aanbeveling niet gevonden of niet in status 'pending'",
        )
    await db.commit()
    result = await get_recommendation(db, current_user.tenant_id, rec_id)
    return result


@router.post("/{rec_id}/execute", response_model=FollowupRecommendationOut)
async def execute_followup(
    rec_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute an approved recommendation."""
    rec = await execute_recommendation(db, current_user.tenant_id, rec_id, current_user.id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aanbeveling niet gevonden of niet in status 'approved'",
        )
    await db.commit()
    result = await get_recommendation(db, current_user.tenant_id, rec_id)
    return result


@router.post("/{rec_id}/approve-and-execute", response_model=FollowupRecommendationOut)
async def approve_and_execute_followup(
    rec_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve and immediately execute a recommendation (1-click flow)."""
    rec = await approve_and_execute_recommendation(
        db, current_user.tenant_id, rec_id, current_user.id
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aanbeveling niet gevonden of niet in status 'pending'",
        )
    await db.commit()
    result = await get_recommendation(db, current_user.tenant_id, rec_id)
    return result
