"""Trust funds module endpoints — Derdengelden transactions and balance."""

import math
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.shared.pagination import PaginatedResponse
from app.trust_funds import service
from app.trust_funds.schemas import (
    TrustBalanceSummary,
    TrustTransactionCreate,
    TrustTransactionRead,
)

router = APIRouter(prefix="/api/trust-funds", tags=["trust-funds"])


# ── Transactions ─────────────────────────────────────────────────────────────


@router.post(
    "/cases/{case_id}/transactions",
    response_model=TrustTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    case_id: uuid.UUID,
    data: TrustTransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new trust fund transaction (deposit or disbursement)."""
    transaction = await service.create_transaction(
        db, current_user.tenant_id, case_id, current_user.id, data
    )
    return transaction


@router.get(
    "/cases/{case_id}/transactions",
    response_model=PaginatedResponse,
)
async def list_transactions(
    case_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=200),
    transaction_type: str | None = Query(default=None),
    transaction_status: str | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List trust fund transactions for a case."""
    transactions, total = await service.list_transactions(
        db,
        current_user.tenant_id,
        case_id,
        page=page,
        per_page=per_page,
        transaction_type=transaction_type,
        status=transaction_status,
    )

    return PaginatedResponse(
        items=[TrustTransactionRead.model_validate(t) for t in transactions],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


# ── Balance ──────────────────────────────────────────────────────────────────


@router.get(
    "/cases/{case_id}/balance",
    response_model=TrustBalanceSummary,
)
async def get_balance(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the trust fund balance summary for a case."""
    return await service.get_balance(db, current_user.tenant_id, case_id)


# ── Approval ─────────────────────────────────────────────────────────────────


@router.post(
    "/transactions/{transaction_id}/approve",
    response_model=TrustTransactionRead,
)
async def approve_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending trust fund transaction (two-director approval)."""
    transaction = await service.approve_transaction(
        db, current_user.tenant_id, transaction_id, current_user.id
    )
    return transaction


@router.post(
    "/transactions/{transaction_id}/reject",
    response_model=TrustTransactionRead,
)
async def reject_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a pending trust fund transaction."""
    transaction = await service.reject_transaction(
        db, current_user.tenant_id, transaction_id, current_user.id
    )
    return transaction
