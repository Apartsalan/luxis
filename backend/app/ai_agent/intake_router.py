"""Intake router — endpoints for dossier intake review and approval."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.intake_models import IntakeStatus
from app.ai_agent.intake_schemas import (
    IntakePendingCountResponse,
    IntakeResponse,
    IntakeReviewRequest,
    IntakeUpdateRequest,
)
from app.ai_agent.intake_service import (
    approve_intake,
    get_intake_by_id,
    get_intake_requests,
    get_pending_intake_count,
    process_intake,
    reject_intake,
)
from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/intake", tags=["intake"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _intake_to_response(intake) -> IntakeResponse:
    """Convert an IntakeRequest model to response schema."""
    email = intake.synced_email
    client = intake.client_contact
    reviewer = intake.reviewed_by
    case = intake.created_case
    contact = intake.created_contact

    return IntakeResponse(
        id=intake.id,
        synced_email_id=intake.synced_email_id,
        email_subject=email.subject if email else "",
        email_from=email.from_email if email else "",
        email_date=email.email_date if email else None,
        client_name=client.name if client else None,
        debtor_name=intake.debtor_name,
        debtor_email=intake.debtor_email,
        debtor_kvk=intake.debtor_kvk,
        debtor_address=intake.debtor_address,
        debtor_city=intake.debtor_city,
        debtor_postcode=intake.debtor_postcode,
        debtor_type=intake.debtor_type,
        invoice_number=intake.invoice_number,
        invoice_date=intake.invoice_date,
        due_date=intake.due_date,
        principal_amount=intake.principal_amount,
        description=intake.description,
        ai_model=intake.ai_model,
        ai_confidence=float(intake.ai_confidence) if intake.ai_confidence is not None else None,
        ai_reasoning=intake.ai_reasoning,
        has_pdf_data=intake.has_pdf_data,
        status=intake.status,
        error_message=intake.error_message,
        reviewed_by_name=reviewer.full_name if reviewer else None,
        reviewed_at=intake.reviewed_at,
        review_note=intake.review_note,
        created_case_id=intake.created_case_id,
        created_case_number=case.case_number if case else None,
        created_contact_id=intake.created_contact_id,
        created_contact_name=contact.name if contact else None,
        created_at=intake.created_at,
    )


# ---------------------------------------------------------------------------
# List / Get endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[IntakeResponse])
async def list_intakes(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List intake requests with optional status filter."""
    intakes, total = await get_intake_requests(
        db,
        current_user.tenant_id,
        status=status_filter,
        page=page,
        per_page=per_page,
    )
    return [_intake_to_response(i) for i in intakes]


@router.get("/pending-count", response_model=IntakePendingCountResponse)
async def pending_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get number of pending review intake requests."""
    count = await get_pending_intake_count(db, current_user.tenant_id)
    return IntakePendingCountResponse(count=count)


@router.get("/{intake_id}", response_model=IntakeResponse)
async def get_intake(
    intake_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single intake request by ID."""
    intake = await get_intake_by_id(db, intake_id, current_user.tenant_id)
    if not intake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake verzoek niet gevonden",
        )
    return _intake_to_response(intake)


# ---------------------------------------------------------------------------
# Action endpoints
# ---------------------------------------------------------------------------


@router.post("/{intake_id}/process", response_model=IntakeResponse)
async def trigger_process(
    intake_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger AI processing for a detected intake."""
    intake = await process_intake(db, intake_id, current_user.tenant_id)
    if not intake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake verzoek niet gevonden of niet in status 'detected'",
        )
    await db.commit()
    refreshed = await get_intake_by_id(db, intake.id, current_user.tenant_id)
    return _intake_to_response(refreshed)


@router.put("/{intake_id}", response_model=IntakeResponse)
async def update_intake(
    intake_id: uuid.UUID,
    data: IntakeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update extracted data before approval (lawyer corrections)."""
    intake = await get_intake_by_id(db, intake_id, current_user.tenant_id)
    if not intake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake verzoek niet gevonden",
        )
    if intake.status != IntakeStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kan alleen intakes in status 'pending_review' wijzigen",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(intake, field, value)

    await db.commit()
    refreshed = await get_intake_by_id(db, intake.id, current_user.tenant_id)
    return _intake_to_response(refreshed)


@router.post("/{intake_id}/approve", response_model=IntakeResponse)
async def approve(
    intake_id: uuid.UUID,
    body: IntakeReviewRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve an intake request — creates debtor contact + incasso case."""
    note = body.note if body else None
    intake = await approve_intake(
        db, intake_id, current_user.tenant_id, current_user.id, note
    )
    if not intake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake verzoek niet gevonden of niet in status 'pending_review'",
        )
    await db.commit()
    refreshed = await get_intake_by_id(db, intake.id, current_user.tenant_id)
    return _intake_to_response(refreshed)


@router.post("/{intake_id}/reject", response_model=IntakeResponse)
async def reject(
    intake_id: uuid.UUID,
    body: IntakeReviewRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject an intake request."""
    note = body.note if body else None
    intake = await reject_intake(
        db, intake_id, current_user.tenant_id, current_user.id, note
    )
    if not intake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake verzoek niet gevonden of niet in status 'pending_review'",
        )
    await db.commit()
    refreshed = await get_intake_by_id(db, intake.id, current_user.tenant_id)
    return _intake_to_response(refreshed)
