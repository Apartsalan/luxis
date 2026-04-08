"""Trust funds module endpoints — Derdengelden transactions and balance."""

import math
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.shared.pagination import PaginatedResponse
from app.trust_funds import service
from app.trust_funds.schemas import (
    EligibleInvoice,
    SepaExportRequest,
    SepaPendingTransaction,
    TrustBalanceSummary,
    TrustOffsetCreate,
    TrustOverviewResponse,
    TrustTransactionCreate,
    TrustTransactionRead,
)

router = APIRouter(prefix="/api/trust-funds", tags=["trust-funds"])


# ── Cross-client Overview ────────────────────────────────────────────────────


@router.get("/overview", response_model=TrustOverviewResponse)
async def get_overview(
    only_nonzero: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cross-client trust balance overview grouped per client."""
    return await service.list_overview_by_client(
        db, current_user.tenant_id, only_nonzero=only_nonzero
    )


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


# ── SEPA Export ──────────────────────────────────────────────────────────────


@router.get("/sepa/pending", response_model=list[SepaPendingTransaction])
async def list_sepa_pending(
    include_exported: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List approved disbursements that can be exported as SEPA batch."""
    return await service.list_sepa_pending(
        db, current_user.tenant_id, include_exported=include_exported
    )


@router.post("/sepa/export")
async def export_sepa_batch(
    payload: SepaExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a SEPA pain.001.001.03 XML batch and download as file.

    Marks all included transactions as exported. The XML can be uploaded
    to the bank portal (Rabobank zakelijk for Kesting Legal).
    """
    xml_bytes, batch_id = await service.export_sepa_batch(
        db,
        current_user.tenant_id,
        payload.transaction_ids,
        payload.execution_date,
    )
    filename = f"sepa-derdengelden-{payload.execution_date.isoformat()}.xml"
    return Response(
        content=xml_bytes,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Sepa-Batch-Id": str(batch_id),
        },
    )


# ── NOvA Reports (CSV) ───────────────────────────────────────────────────────


@router.get("/reports/mutaties.csv")
async def download_mutaties_csv(
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a NOvA mutatieoverzicht as CSV (semicolon-delimited, UTF-8 BOM)."""
    csv_text = await service.generate_mutaties_csv(
        db, current_user.tenant_id, date_from=date_from, date_to=date_to
    )
    parts = ["derdengelden-mutaties"]
    if date_from is not None:
        parts.append(date_from.isoformat())
    if date_to is not None:
        parts.append(date_to.isoformat())
    filename = "_".join(parts) + ".csv"
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/reports/saldolijst.csv")
async def download_saldolijst_csv(
    peildatum: date = Query(..., alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a NOvA saldolijst per cliënt at a peildatum, as CSV."""
    csv_text = await service.generate_saldolijst_csv(
        db, current_user.tenant_id, peildatum=peildatum
    )
    filename = f"derdengelden-saldolijst_{peildatum.isoformat()}.csv"
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Verrekening (Offset to invoice) ──────────────────────────────────────────


@router.get(
    "/cases/{case_id}/eligible-invoices",
    response_model=list[EligibleInvoice],
)
async def list_eligible_invoices(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List open invoices of the case's client that can be offset against
    the trust balance (verrekening). Cross-case query within the same client.
    """
    return await service.list_eligible_invoices_for_offset(
        db, current_user.tenant_id, case_id
    )


@router.post(
    "/cases/{case_id}/offsets",
    response_model=TrustTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_offset(
    case_id: uuid.UUID,
    data: TrustOffsetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a verrekening (offset) of trust balance against an own invoice.

    Voda art. 6.19 lid 5: requires explicit per-transaction client consent.
    The actual invoice payment is booked when the offset is fully approved.
    """
    transaction = await service.create_offset_to_invoice(
        db, current_user.tenant_id, case_id, current_user.id, data
    )
    return transaction
