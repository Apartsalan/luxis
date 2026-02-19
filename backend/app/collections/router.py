"""Collections module endpoints — Claims, Payments, Interest, BIK, Derdengelden."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.cases.service import get_case
from app.collections import service
from app.collections.schemas import (
    ArrangementCreate,
    ArrangementResponse,
    ArrangementUpdate,
    ClaimCreate,
    ClaimResponse,
    ClaimUpdate,
    DerdengeldenBalance,
    DerdengeldenCreate,
    DerdengeldenResponse,
    InterestRateResponse,
    PaymentCreate,
    PaymentResponse,
    PaymentUpdate,
)
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/cases/{case_id}", tags=["collections"])
rates_router = APIRouter(prefix="/api/interest-rates", tags=["reference"])


# ── Claims ───────────────────────────────────────────────────────────────────


@router.get("/claims", response_model=list[ClaimResponse])
async def list_claims(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all claims for a case."""
    await get_case(db, current_user.tenant_id, case_id)  # Auth check
    claims = await service.list_claims(db, current_user.tenant_id, case_id)
    return claims


@router.post(
    "/claims",
    response_model=ClaimResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_claim(
    case_id: uuid.UUID,
    data: ClaimCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a claim to a case."""
    await get_case(db, current_user.tenant_id, case_id)
    claim = await service.create_claim(
        db, current_user.tenant_id, case_id, data
    )
    return claim


@router.put("/claims/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    case_id: uuid.UUID,
    claim_id: uuid.UUID,
    data: ClaimUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a claim."""
    await get_case(db, current_user.tenant_id, case_id)
    claim = await service.update_claim(
        db, current_user.tenant_id, claim_id, data
    )
    return claim


@router.delete(
    "/claims/{claim_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_claim(
    case_id: uuid.UUID,
    claim_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a claim."""
    await get_case(db, current_user.tenant_id, case_id)
    await service.delete_claim(db, current_user.tenant_id, claim_id)


# ── Interest Calculation ─────────────────────────────────────────────────────


@router.get("/interest")
async def calculate_interest(
    case_id: uuid.UUID,
    as_of: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calculate interest for all claims in a case."""
    from app.collections.interest import calculate_case_interest

    case = await get_case(db, current_user.tenant_id, case_id)
    calc_date = as_of or date.today()

    claims = await service.list_claims(db, current_user.tenant_id, case_id)
    claim_dicts = [
        {
            "id": str(c.id),
            "description": c.description,
            "principal_amount": c.principal_amount,
            "default_date": c.default_date,
        }
        for c in claims
    ]

    result = await calculate_case_interest(
        db,
        str(case_id),
        case.interest_type,
        case.contractual_rate,
        case.contractual_compound,
        claim_dicts,
        calc_date,
    )
    return result


# ── BIK Calculation ──────────────────────────────────────────────────────────


@router.get("/bik")
async def calculate_bik_endpoint(
    case_id: uuid.UUID,
    include_btw: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calculate BIK (buitengerechtelijke incassokosten) for a case."""
    from app.collections.wik import calculate_bik

    await get_case(db, current_user.tenant_id, case_id)
    claims = await service.list_claims(db, current_user.tenant_id, case_id)
    total_principal = sum(c.principal_amount for c in claims)

    return calculate_bik(total_principal, include_btw=include_btw)


# ── Payments ─────────────────────────────────────────────────────────────────


@router.get("/payments", response_model=list[PaymentResponse])
async def list_payments(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all payments for a case."""
    await get_case(db, current_user.tenant_id, case_id)
    return await service.list_payments(db, current_user.tenant_id, case_id)


@router.post(
    "/payments",
    response_model=PaymentResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_payment(
    case_id: uuid.UUID,
    data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a payment for a case (distributed per art. 6:44 BW)."""
    case = await get_case(db, current_user.tenant_id, case_id)
    return await service.create_payment(
        db, current_user.tenant_id, case_id, data, current_user.id,
        interest_type=case.interest_type,
        contractual_rate=case.contractual_rate,
        contractual_compound=case.contractual_compound,
    )


@router.put("/payments/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    case_id: uuid.UUID,
    payment_id: uuid.UUID,
    data: PaymentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a payment."""
    await get_case(db, current_user.tenant_id, case_id)
    return await service.update_payment(
        db, current_user.tenant_id, payment_id, data
    )


@router.delete(
    "/payments/{payment_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
async def delete_payment(
    case_id: uuid.UUID,
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a payment."""
    await get_case(db, current_user.tenant_id, case_id)
    await service.delete_payment(db, current_user.tenant_id, payment_id)


# ── Payment Arrangements ─────────────────────────────────────────────────────


@router.get("/arrangements", response_model=list[ArrangementResponse])
async def list_arrangements(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List payment arrangements for a case."""
    await get_case(db, current_user.tenant_id, case_id)
    return await service.list_arrangements(
        db, current_user.tenant_id, case_id
    )


@router.post(
    "/arrangements",
    response_model=ArrangementResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_arrangement(
    case_id: uuid.UUID,
    data: ArrangementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a payment arrangement."""
    await get_case(db, current_user.tenant_id, case_id)
    return await service.create_arrangement(
        db, current_user.tenant_id, case_id, data
    )


@router.put(
    "/arrangements/{arrangement_id}",
    response_model=ArrangementResponse,
)
async def update_arrangement(
    case_id: uuid.UUID,
    arrangement_id: uuid.UUID,
    data: ArrangementUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a payment arrangement."""
    await get_case(db, current_user.tenant_id, case_id)
    return await service.update_arrangement(
        db, current_user.tenant_id, arrangement_id, data
    )


# ── Derdengelden ─────────────────────────────────────────────────────────────


@router.get("/derdengelden", response_model=list[DerdengeldenResponse])
async def list_derdengelden(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List derdengelden transactions for a case."""
    await get_case(db, current_user.tenant_id, case_id)
    return await service.list_derdengelden(
        db, current_user.tenant_id, case_id
    )


@router.post(
    "/derdengelden",
    response_model=DerdengeldenResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_derdengelden(
    case_id: uuid.UUID,
    data: DerdengeldenCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a derdengelden transaction."""
    await get_case(db, current_user.tenant_id, case_id)
    return await service.create_derdengelden(
        db, current_user.tenant_id, case_id, data, current_user.id
    )


@router.get("/derdengelden/balance", response_model=DerdengeldenBalance)
async def derdengelden_balance(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get derdengelden balance for a case."""
    await get_case(db, current_user.tenant_id, case_id)
    return await service.get_derdengelden_balance(
        db, current_user.tenant_id, case_id
    )


# ── Financial Summary ────────────────────────────────────────────────────────


@router.get("/financial-summary")
async def financial_summary(
    case_id: uuid.UUID,
    as_of: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complete financial summary for a case."""
    case = await get_case(db, current_user.tenant_id, case_id)
    return await service.get_financial_summary(
        db,
        current_user.tenant_id,
        case_id,
        case.interest_type,
        case.contractual_rate,
        case.contractual_compound,
        as_of,
    )


# ── Interest Rates (standalone reference endpoint) ───────────────────────────


@rates_router.get("", response_model=list[InterestRateResponse])
async def list_interest_rates(
    rate_type: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List historical interest rates (reference data)."""
    return await service.list_interest_rates(db, rate_type)
