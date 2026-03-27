"""WWFT/KYC endpoints — Client identification and verification per WWFT."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.relations import kyc_service
from app.relations.kyc_schemas import (
    KycComplete,
    KycCreate,
    KycResponse,
    KycUpdate,
)

router = APIRouter(prefix="/api/kyc", tags=["kyc"])


@router.get("/contact/{contact_id}", response_model=KycResponse | None)
async def get_kyc_for_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get KYC verification for a contact. Returns null if not started."""
    kyc = await kyc_service.get_kyc_for_contact(db, current_user.tenant_id, contact_id)
    return kyc


@router.get("/contact/{contact_id}/status")
async def get_kyc_status(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get lightweight KYC status for a contact (for badges/warnings)."""
    return await kyc_service.get_kyc_status_for_contact(db, current_user.tenant_id, contact_id)


@router.post("", response_model=KycResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_kyc(
    data: KycCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update KYC verification for a contact (upsert)."""
    kyc = await kyc_service.create_or_update_kyc(db, current_user.tenant_id, current_user.id, data)
    return kyc


@router.put("/{kyc_id}", response_model=KycResponse)
async def update_kyc(
    kyc_id: uuid.UUID,
    data: KycUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update specific fields of a KYC verification."""
    kyc = await kyc_service.update_kyc(db, current_user.tenant_id, kyc_id, data)
    return kyc


@router.post("/{kyc_id}/complete", response_model=KycResponse)
async def complete_kyc(
    kyc_id: uuid.UUID,
    data: KycComplete | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a KYC verification as complete.

    Validates that all required checks have been performed:
    - Identity document verified
    - PEP check done
    - Sanctions list check done
    - Risk classification assigned
    - UBO registered (for companies)
    """
    kyc = await kyc_service.complete_kyc(db, current_user.tenant_id, kyc_id, current_user.id, data)
    return kyc


@router.get("/dashboard")
async def kyc_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get KYC compliance dashboard data.

    Returns:
    - Clients without KYC (niet_gestart)
    - Incomplete verifications (in_behandeling)
    - Overdue reviews (next_review_date past)
    - Upcoming reviews (within 30 days)
    """
    return await kyc_service.get_kyc_dashboard(db, current_user.tenant_id)
