"""Follow-up router — endpoints for follow-up recommendation review and execution."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.followup_schemas import (
    FollowupPreviewOut,
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
    preview_recommendation,
    reject_recommendation,
)
from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/followup", tags=["followup"])


class FollowupScheduleIn(BaseModel):
    """S246-nacht — gepland uitvoermoment (ISO-tijd mét zone, van de voorkant)."""

    scheduled_at: datetime


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


@router.get("/{rec_id}/preview", response_model=FollowupPreviewOut)
async def preview_followup(
    rec_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """B13 — toon wat er uitgaat vóór de verzending (verstuurt niets)."""
    preview = await preview_recommendation(
        db, current_user.tenant_id, rec_id, current_user.id
    )
    if preview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aanbeveling niet gevonden",
        )
    return preview


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


@router.post("/{rec_id}/schedule-execute")
async def schedule_execute_followup(
    rec_id: uuid.UUID,
    data: FollowupScheduleIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """S246-nacht — 'Verstuur later' op de follow-up-knop.

    Goedkeuren gebeurt NU (Lisannes besluit van vanavond); alleen de uitvoering
    (brief maken, versturen, doorschuiven) wacht tot het gekozen moment via de
    verzend-wachtrij. Stap gewisseld intussen → aanbeveling wordt 'verouderd'
    en de bezorger voert niets uit.
    """
    from app.email.scheduled_service import schedule_followup_execute

    row = await schedule_followup_execute(db, current_user, rec_id, data.scheduled_at)
    await db.commit()
    return {
        "scheduled": True,
        "scheduled_email_id": str(row.id),
        "scheduled_at": row.scheduled_at.isoformat(),
    }


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
