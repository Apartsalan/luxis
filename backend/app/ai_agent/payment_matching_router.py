"""Payment matching router — endpoints for bank statement import and match review."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.payment_matching_schemas import (
    BankStatementImportList,
    BankStatementImportOut,
    ManualMatchIn,
    MatchRejectIn,
    PaymentMatchList,
    PaymentMatchOut,
    PaymentMatchStatsOut,
)
from app.ai_agent.payment_matching_service import (
    approve_all_pending,
    approve_and_execute_match,
    approve_match,
    execute_match,
    generate_matches,
    get_import,
    get_match,
    get_match_stats,
    import_bank_statement,
    list_import_transactions,
    list_imports,
    list_matches,
    manual_match,
    reject_match,
)
from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/payment-matching", tags=["payment-matching"])


# ── Import Endpoints ─────────────────────────────────────────────────────


@router.post("/import", response_model=BankStatementImportOut, status_code=status.HTTP_201_CREATED)
async def upload_bank_statement(
    file: UploadFile,
    bank: str = Query(default="rabobank"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a bank statement CSV file and import transactions."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alleen CSV-bestanden worden ondersteund",
        )

    content = await file.read()
    try:
        csv_content = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            csv_content = content.decode("latin-1")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bestand kan niet gelezen worden. Gebruik UTF-8 of Latin-1 encoding.",
            )

    stmt_import = await import_bank_statement(
        db,
        current_user.tenant_id,
        current_user.id,
        file.filename,
        csv_content,
        bank=bank,
    )

    # Auto-generate matches
    if stmt_import.status == "completed":
        await generate_matches(db, current_user.tenant_id, stmt_import.id)

    await db.commit()

    result = await get_import(db, current_user.tenant_id, stmt_import.id)
    return result


@router.get("/imports", response_model=BankStatementImportList)
async def list_bank_imports(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all bank statement imports."""
    return await list_imports(db, current_user.tenant_id, page=page, per_page=per_page)


@router.get("/imports/{import_id}", response_model=BankStatementImportOut)
async def get_bank_import(
    import_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific import."""
    result = await get_import(db, current_user.tenant_id, import_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import niet gevonden",
        )
    return result


@router.get("/imports/{import_id}/transactions")
async def list_transactions(
    import_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    unmatched_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List transactions for a specific import."""
    items, total = await list_import_transactions(
        db, current_user.tenant_id, import_id,
        page=page, per_page=per_page, unmatched_only=unmatched_only,
    )
    import math
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 0,
    }


@router.post("/imports/{import_id}/rematch")
async def rematch_import(
    import_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-run matching for unmatched transactions in an import."""
    count = await generate_matches(db, current_user.tenant_id, import_id)
    await db.commit()
    return {"matched": count}


# ── Match Endpoints ──────────────────────────────────────────────────────


@router.get("/matches", response_model=PaymentMatchList)
async def list_payment_matches(
    status_filter: str | None = Query(default=None, alias="status"),
    import_id: uuid.UUID | None = Query(default=None),
    case_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List payment matches with optional filters."""
    return await list_matches(
        db, current_user.tenant_id,
        status_filter=status_filter,
        import_id=import_id,
        case_id=case_id,
        page=page,
        per_page=per_page,
    )


@router.get("/matches/stats", response_model=PaymentMatchStatsOut)
async def match_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get match counts per status."""
    return await get_match_stats(db, current_user.tenant_id)


@router.get("/matches/{match_id}", response_model=PaymentMatchOut)
async def get_payment_match(
    match_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single payment match."""
    result = await get_match(db, current_user.tenant_id, match_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match niet gevonden",
        )
    return result


@router.post("/matches/{match_id}/approve", response_model=PaymentMatchOut)
async def approve_payment_match(
    match_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending match."""
    match = await approve_match(
        db, current_user.tenant_id, match_id, current_user.id
    )
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match niet gevonden of niet in status 'pending'",
        )
    await db.commit()
    result = await get_match(db, current_user.tenant_id, match_id)
    return result


@router.post("/matches/{match_id}/reject", response_model=PaymentMatchOut)
async def reject_payment_match(
    match_id: uuid.UUID,
    body: MatchRejectIn | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a pending match."""
    note = body.note if body else None
    match = await reject_match(
        db, current_user.tenant_id, match_id, current_user.id, note
    )
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match niet gevonden of niet in status 'pending'",
        )
    await db.commit()
    result = await get_match(db, current_user.tenant_id, match_id)
    return result


@router.post("/matches/{match_id}/execute", response_model=PaymentMatchOut)
async def execute_payment_match(
    match_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute an approved match (create derdengelden + payment)."""
    match = await execute_match(
        db, current_user.tenant_id, match_id, current_user.id
    )
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match niet gevonden of niet in status 'approved'",
        )
    await db.commit()
    result = await get_match(db, current_user.tenant_id, match_id)
    return result


@router.post(
    "/matches/{match_id}/approve-and-execute",
    response_model=PaymentMatchOut,
)
async def approve_and_execute_payment_match(
    match_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve and immediately execute a match (1-click flow)."""
    match = await approve_and_execute_match(
        db, current_user.tenant_id, match_id, current_user.id
    )
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match niet gevonden of niet in status 'pending'",
        )
    await db.commit()
    result = await get_match(db, current_user.tenant_id, match_id)
    return result


@router.post("/matches/approve-all")
async def approve_all_matches(
    import_id: uuid.UUID | None = Query(default=None),
    min_confidence: int = Query(default=85, ge=0, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve and execute all pending matches above a confidence threshold."""
    count = await approve_all_pending(
        db, current_user.tenant_id, current_user.id,
        import_id=import_id, min_confidence=min_confidence,
    )
    await db.commit()
    return {"executed": count}


@router.post("/matches/manual", response_model=PaymentMatchOut)
async def create_manual_match(
    body: ManualMatchIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually match a transaction to a case."""
    try:
        match = await manual_match(
            db, current_user.tenant_id, current_user.id,
            body.transaction_id, body.case_id, body.note,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    await db.commit()
    result = await get_match(db, current_user.tenant_id, match.id)
    return result
