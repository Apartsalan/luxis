"""Payment matching service — import, match, review, and execute bank payments."""

import hashlib
import logging
import math
import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.csv_parsers import parse_rabobank_csv
from app.ai_agent.payment_matching_algorithm import CaseMatchData, find_matches
from app.ai_agent.payment_matching_models import (
    MATCH_CONFIDENCE,
    MATCH_METHOD_LABELS,
    BankStatementImport,
    BankTransaction,
    ImportStatus,
    MatchMethod,
    MatchStatus,
    PaymentMatch,
)
from app.ai_agent.payment_matching_schemas import (
    BankStatementImportList,
    BankStatementImportOut,
    BankTransactionOut,
    PaymentMatchList,
    PaymentMatchOut,
    PaymentMatchStatsOut,
)
from app.cases.models import Case
from app.collections.models import Claim
from app.collections.schemas import PaymentCreate
from app.collections.service import create_payment_for_case
from app.shared.exceptions import ConflictError
from app.trust_funds.schemas import TrustTransactionCreate
from app.trust_funds.service import create_transaction as create_trust_transaction

logger = logging.getLogger(__name__)

TWO_PLACES = Decimal("0.01")


def _dedup_key(txn) -> str:
    """Stable identity of a bank transaction across imports (H17).

    Primary: own IBAN + Volgnr — the bank guarantees uniqueness per account.
    Fallback (no Volgnr): content hash of date|amount|counterparty|description.
    """
    if txn.account_iban and txn.sequence_number:
        return f"{txn.account_iban}:{txn.sequence_number}"
    raw = (
        f"{txn.transaction_date.isoformat()}|{txn.amount}|"
        f"{txn.counterparty_iban or ''}|{txn.description or ''}"
    )
    return "h:" + hashlib.sha256(raw.encode()).hexdigest()[:64]


# ── Import ───────────────────────────────────────────────────────────────


async def import_bank_statement(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    csv_content: str,
    bank: str = "rabobank",
) -> BankStatementImport:
    """Import a bank statement CSV and create transaction records.

    Only credit (incoming) transactions are stored. Debits are counted
    but skipped since this is a derdengeldrekening.
    """
    # Create import record
    stmt_import = BankStatementImport(
        tenant_id=tenant_id,
        filename=filename,
        bank=bank,
        status=ImportStatus.PROCESSING,
        imported_by_id=user_id,
    )
    db.add(stmt_import)
    await db.flush()

    try:
        # Parse CSV
        if bank == "rabobank":
            result = parse_rabobank_csv(csv_content)
        else:
            stmt_import.status = ImportStatus.FAILED
            stmt_import.error_message = f"Onbekend bankformaat: {bank}"
            await db.flush()
            return stmt_import

        if result.errors and not result.transactions:
            stmt_import.status = ImportStatus.FAILED
            stmt_import.error_message = "; ".join(result.errors[:5])
            await db.flush()
            return stmt_import

        # Update import stats
        stmt_import.account_iban = result.account_iban
        stmt_import.total_rows = result.total_rows
        stmt_import.credit_count = result.credit_count
        stmt_import.debit_count = result.debit_count
        stmt_import.skipped_count = result.skipped_count

        # H17: skip transactions that were already imported (same Volgnr or
        # identical content) — re-uploading the same statement must be a no-op.
        keys = [_dedup_key(txn) for txn in result.transactions]
        existing_keys: set[str] = set()
        if keys:
            existing_result = await db.execute(
                select(BankTransaction.dedup_key).where(
                    BankTransaction.tenant_id == tenant_id,
                    BankTransaction.dedup_key.in_(keys),
                )
            )
            existing_keys = {row[0] for row in existing_result.all()}

        duplicate_count = 0
        seen_in_file: set[str] = set()
        for txn, key in zip(result.transactions, keys, strict=True):
            if key in existing_keys or key in seen_in_file:
                duplicate_count += 1
                continue
            seen_in_file.add(key)
            bank_txn = BankTransaction(
                tenant_id=tenant_id,
                import_id=stmt_import.id,
                transaction_date=txn.transaction_date,
                amount=txn.amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
                counterparty_name=txn.counterparty_name,
                counterparty_iban=txn.counterparty_iban,
                description=txn.description,
                currency=txn.currency,
                entry_date=txn.entry_date,
                sequence_number=txn.sequence_number,
                payment_reference=txn.payment_reference,
                dedup_key=key,
            )
            db.add(bank_txn)

        stmt_import.duplicate_count = duplicate_count
        stmt_import.status = ImportStatus.COMPLETED
        if result.errors:
            stmt_import.error_message = "; ".join(result.errors[:5])

        await db.flush()
        await db.refresh(stmt_import)

    except Exception as e:
        logger.error("Bank statement import failed: %s", e)
        stmt_import.status = ImportStatus.FAILED
        stmt_import.error_message = str(e)[:500]
        await db.flush()

    return stmt_import


# ── Match Generation ─────────────────────────────────────────────────────


async def _load_case_match_data(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[CaseMatchData]:
    """Load all active incasso cases with data needed for matching."""
    # Get active incasso cases
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.case_type == "incasso",
            Case.is_active.is_(True),
            Case.status.notin_(["betaald", "afgesloten"]),
        )
    )
    cases = list(result.scalars().all())

    case_data_list: list[CaseMatchData] = []
    for case in cases:
        # Get invoice numbers from claims
        claims_result = await db.execute(
            select(Claim).where(
                Claim.tenant_id == tenant_id,
                Claim.case_id == case.id,
                Claim.is_active.is_(True),
            )
        )
        claims = list(claims_result.scalars().all())
        invoice_numbers = [c.invoice_number for c in claims if c.invoice_number]

        outstanding = Decimal(str(case.total_principal)) - Decimal(str(case.total_paid))
        outstanding = outstanding.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        case_data_list.append(
            CaseMatchData(
                id=case.id,
                case_number=case.case_number,
                opposing_party_name=(case.opposing_party.name if case.opposing_party else None),
                opposing_party_iban=(case.opposing_party.iban if case.opposing_party else None),
                outstanding_amount=max(Decimal("0"), outstanding),
                invoice_numbers=invoice_numbers,
            )
        )

    return case_data_list


async def generate_matches(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    import_id: uuid.UUID,
) -> int:
    """Generate payment matches for all unmatched transactions in an import.

    Returns the number of matches created.
    """
    # Load unmatched transactions
    txn_result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.tenant_id == tenant_id,
            BankTransaction.import_id == import_id,
            BankTransaction.is_matched.is_(False),
        )
    )
    transactions = list(txn_result.scalars().all())

    if not transactions:
        return 0

    # Load case data for matching
    case_data = await _load_case_match_data(db, tenant_id)

    if not case_data:
        return 0

    matched_count = 0

    for txn in transactions:
        candidates = find_matches(
            transaction_description=txn.description or "",
            transaction_amount=txn.amount,
            counterparty_name=txn.counterparty_name,
            counterparty_iban=txn.counterparty_iban,
            cases=case_data,
        )

        if candidates:
            # Take the best match only
            best = candidates[0]
            match = PaymentMatch(
                tenant_id=tenant_id,
                transaction_id=txn.id,
                case_id=best.case_id,
                match_method=best.match_method,
                confidence=best.confidence,
                match_details=best.details,
                status=MatchStatus.PENDING,
            )
            db.add(match)
            txn.is_matched = True
            matched_count += 1

    # Update import stats
    import_result = await db.execute(
        select(BankStatementImport).where(
            BankStatementImport.id == import_id,
            BankStatementImport.tenant_id == tenant_id,
        )
    )
    stmt_import = import_result.scalar_one_or_none()
    if stmt_import:
        stmt_import.matched_count = matched_count

    await db.flush()
    return matched_count


# ── Match CRUD ───────────────────────────────────────────────────────────


def _match_to_response(match: PaymentMatch) -> PaymentMatchOut:
    """Convert a PaymentMatch model to response schema."""
    txn = match.transaction
    return PaymentMatchOut(
        id=match.id,
        transaction_id=match.transaction_id,
        case_id=match.case_id,
        transaction_date=txn.transaction_date if txn else None,
        amount=txn.amount if txn else Decimal("0"),
        counterparty_name=txn.counterparty_name if txn else None,
        counterparty_iban=txn.counterparty_iban if txn else None,
        description=txn.description if txn else None,
        case_number=match.case.case_number if match.case else "?",
        client_name=(match.case.client.name if match.case and match.case.client else None),
        opposing_party_name=(
            match.case.opposing_party.name if match.case and match.case.opposing_party else None
        ),
        match_method=match.match_method,
        match_method_label=MATCH_METHOD_LABELS.get(match.match_method, match.match_method),
        confidence=match.confidence,
        match_details=match.match_details,
        status=match.status,
        reviewed_by_name=(
            match.reviewed_by.full_name
            if match.reviewed_by and hasattr(match.reviewed_by, "full_name")
            else (match.reviewed_by.email if match.reviewed_by else None)
        ),
        reviewed_at=match.reviewed_at,
        review_note=match.review_note,
        executed_at=match.executed_at,
        payment_id=match.payment_id,
        trust_transaction_id=match.trust_transaction_id,
        created_at=match.created_at,
    )


def _import_to_response(imp: BankStatementImport) -> BankStatementImportOut:
    """Convert a BankStatementImport model to response schema."""
    return BankStatementImportOut(
        id=imp.id,
        filename=imp.filename,
        bank=imp.bank,
        account_iban=imp.account_iban,
        status=imp.status,
        error_message=imp.error_message,
        total_rows=imp.total_rows,
        credit_count=imp.credit_count,
        debit_count=imp.debit_count,
        skipped_count=imp.skipped_count,
        duplicate_count=imp.duplicate_count,
        matched_count=imp.matched_count,
        imported_by_name=(
            imp.imported_by.full_name
            if imp.imported_by and hasattr(imp.imported_by, "full_name")
            else (imp.imported_by.email if imp.imported_by else None)
        ),
        created_at=imp.created_at,
    )


async def list_imports(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    page: int = 1,
    per_page: int = 20,
) -> BankStatementImportList:
    """List bank statement imports."""
    query = select(BankStatementImport).where(
        BankStatementImport.tenant_id == tenant_id,
    )
    count_query = select(func.count(BankStatementImport.id)).where(
        BankStatementImport.tenant_id == tenant_id,
    )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(BankStatementImport.created_at.desc())
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    imports = list(result.scalars().all())

    return BankStatementImportList(
        items=[_import_to_response(i) for i in imports],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


async def get_import(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    import_id: uuid.UUID,
) -> BankStatementImportOut | None:
    """Get a single import by ID."""
    result = await db.execute(
        select(BankStatementImport).where(
            BankStatementImport.id == import_id,
            BankStatementImport.tenant_id == tenant_id,
        )
    )
    imp = result.scalar_one_or_none()
    if not imp:
        return None
    return _import_to_response(imp)


async def list_import_transactions(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    import_id: uuid.UUID,
    *,
    page: int = 1,
    per_page: int = 50,
    unmatched_only: bool = False,
) -> tuple[list[BankTransactionOut], int]:
    """List transactions for an import."""
    query = select(BankTransaction).where(
        BankTransaction.tenant_id == tenant_id,
        BankTransaction.import_id == import_id,
    )
    count_query = select(func.count(BankTransaction.id)).where(
        BankTransaction.tenant_id == tenant_id,
        BankTransaction.import_id == import_id,
    )

    if unmatched_only:
        query = query.where(BankTransaction.is_matched.is_(False))
        count_query = count_query.where(BankTransaction.is_matched.is_(False))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(BankTransaction.transaction_date.desc())
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    txns = list(result.scalars().all())

    items = [
        BankTransactionOut(
            id=t.id,
            import_id=t.import_id,
            transaction_date=t.transaction_date,
            amount=t.amount,
            counterparty_name=t.counterparty_name,
            counterparty_iban=t.counterparty_iban,
            description=t.description,
            currency=t.currency,
            entry_date=t.entry_date,
            is_matched=t.is_matched,
            created_at=t.created_at,
        )
        for t in txns
    ]
    return items, total


async def list_matches(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    status_filter: str | None = None,
    import_id: uuid.UUID | None = None,
    case_id: uuid.UUID | None = None,
    page: int = 1,
    per_page: int = 20,
) -> PaymentMatchList:
    """List payment matches with optional filters."""
    query = select(PaymentMatch).where(
        PaymentMatch.tenant_id == tenant_id,
    )
    count_query = select(func.count(PaymentMatch.id)).where(
        PaymentMatch.tenant_id == tenant_id,
    )

    if status_filter:
        query = query.where(PaymentMatch.status == status_filter)
        count_query = count_query.where(PaymentMatch.status == status_filter)

    if import_id:
        query = query.join(BankTransaction).where(
            BankTransaction.import_id == import_id,
        )
        count_query = count_query.join(BankTransaction).where(
            BankTransaction.import_id == import_id,
        )

    if case_id:
        query = query.where(PaymentMatch.case_id == case_id)
        count_query = count_query.where(PaymentMatch.case_id == case_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(
        PaymentMatch.status.asc(),
        PaymentMatch.confidence.desc(),
        PaymentMatch.created_at.desc(),
    )

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    matches = list(result.scalars().all())

    return PaymentMatchList(
        items=[_match_to_response(m) for m in matches],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


async def get_match(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    match_id: uuid.UUID,
) -> PaymentMatchOut | None:
    """Get a single match by ID."""
    result = await db.execute(
        select(PaymentMatch).where(
            PaymentMatch.id == match_id,
            PaymentMatch.tenant_id == tenant_id,
        )
    )
    match = result.scalar_one_or_none()
    if not match:
        return None
    return _match_to_response(match)


async def get_match_stats(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> PaymentMatchStatsOut:
    """Get match counts per status."""
    result = await db.execute(
        select(
            PaymentMatch.status,
            func.count(PaymentMatch.id),
        )
        .where(PaymentMatch.tenant_id == tenant_id)
        .group_by(PaymentMatch.status)
    )
    counts = {row[0]: row[1] for row in result.all()}

    # Total pending amount
    pending_amount_result = await db.execute(
        select(func.coalesce(func.sum(BankTransaction.amount), Decimal("0.00")))
        .join(PaymentMatch, PaymentMatch.transaction_id == BankTransaction.id)
        .where(
            PaymentMatch.tenant_id == tenant_id,
            PaymentMatch.status == MatchStatus.PENDING,
        )
    )
    total_pending = pending_amount_result.scalar() or Decimal("0.00")

    return PaymentMatchStatsOut(
        pending=counts.get(MatchStatus.PENDING, 0),
        approved=counts.get(MatchStatus.APPROVED, 0),
        rejected=counts.get(MatchStatus.REJECTED, 0),
        executed=counts.get(MatchStatus.EXECUTED, 0),
        total_amount_pending=total_pending,
    )


# ── Review Workflow ──────────────────────────────────────────────────────


async def approve_match(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    match_id: uuid.UUID,
    user_id: uuid.UUID,
) -> PaymentMatch | None:
    """Approve a pending match."""
    result = await db.execute(
        select(PaymentMatch).where(
            PaymentMatch.tenant_id == tenant_id,
            PaymentMatch.id == match_id,
            PaymentMatch.status == MatchStatus.PENDING,
        )
    )
    match = result.scalar_one_or_none()
    if not match:
        return None

    match.status = MatchStatus.APPROVED
    match.reviewed_by_id = user_id
    match.reviewed_at = datetime.now(UTC)
    await db.flush()
    return match


async def reject_match(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    match_id: uuid.UUID,
    user_id: uuid.UUID,
    note: str | None = None,
) -> PaymentMatch | None:
    """Reject a pending match. Unmarks the transaction so it can be re-matched."""
    result = await db.execute(
        select(PaymentMatch).where(
            PaymentMatch.tenant_id == tenant_id,
            PaymentMatch.id == match_id,
            PaymentMatch.status == MatchStatus.PENDING,
        )
    )
    match = result.scalar_one_or_none()
    if not match:
        return None

    match.status = MatchStatus.REJECTED
    match.reviewed_by_id = user_id
    match.reviewed_at = datetime.now(UTC)
    match.review_note = note

    # Unmark transaction so it can be matched again (manually or re-run)
    txn_result = await db.execute(
        select(BankTransaction).where(BankTransaction.id == match.transaction_id)
    )
    txn = txn_result.scalar_one_or_none()
    if txn:
        txn.is_matched = False

    await db.flush()
    return match


async def execute_match(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    match_id: uuid.UUID,
    user_id: uuid.UUID,
) -> PaymentMatch | None:
    """Execute an approved match.

    Creates:
    1. A trust fund deposit (derdengelden — money received on trust account)
    2. A payment record with art. 6:44 BW distribution

    The existing create_payment() handles the art. 6:44 BW distribution
    (costs -> interest -> principal) automatically.
    """
    result = await db.execute(
        select(PaymentMatch).where(
            PaymentMatch.tenant_id == tenant_id,
            PaymentMatch.id == match_id,
            PaymentMatch.status == MatchStatus.APPROVED,
        )
    )
    match = result.scalar_one_or_none()
    if not match:
        return None

    # Load transaction
    txn_result = await db.execute(
        select(BankTransaction).where(BankTransaction.id == match.transaction_id)
    )
    txn = txn_result.scalar_one_or_none()
    if not txn:
        match.status = MatchStatus.EXECUTED
        match.executed_at = datetime.now(UTC)
        await db.flush()
        return match

    # 1. Create trust fund deposit (derdengelden) — with the real bank date
    # and payment reference so the NOvA-administratie matches the bank.
    counterparty = txn.counterparty_name or "Onbekend"
    description = f"Bankimport: {counterparty}"
    if txn.description:
        description = f"{description} - {txn.description}"
    trust_data = TrustTransactionCreate(
        transaction_type="deposit",
        amount=txn.amount,
        transaction_date=txn.transaction_date,
        description=description,
        payment_method="bank",
        reference=txn.payment_reference or txn.sequence_number,
    )
    trust_tx = await create_trust_transaction(
        db, tenant_id, match.case_id, user_id, trust_data
    )
    match.trust_transaction_id = trust_tx.id

    # 2. Create payment with art. 6:44 BW distribution. H18: a debtor can pay
    # more than the outstanding amount — the payment is then capped on the
    # outstanding total and the surplus stays visible as trust balance.
    payment_data = PaymentCreate(
        amount=txn.amount,
        payment_date=txn.transaction_date,
        description=f"Bankimport: {counterparty}",
        payment_method="bank",
    )
    # Use the case's own interest/BIK/BTW/nakosten settings (AUDIT-B3), so a
    # bank-import payment distributes identically to a manually registered one.
    payment = await create_payment_for_case(
        db, tenant_id, match.case_id, payment_data, user_id, cap_to_outstanding=True
    )
    match.payment_id = payment.id

    surplus = txn.amount - payment.amount
    if surplus > Decimal("0"):
        match.match_details = (
            f"{match.match_details or ''} | Overschot €{surplus} blijft als "
            f"derdengeldensaldo staan — terugbetalen aan debiteur."
        ).strip(" |")

    # Mark as executed
    match.status = MatchStatus.EXECUTED
    match.executed_at = datetime.now(UTC)
    await db.flush()

    logger.info(
        "Match executed: txn %s -> case %s (trust_tx=%s, payment=%s)",
        txn.id,
        match.case_id,
        trust_tx.id,
        payment.id,
    )

    return match


async def approve_and_execute_match(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    match_id: uuid.UUID,
    user_id: uuid.UUID,
) -> PaymentMatch | None:
    """Approve and immediately execute a match (1-click flow)."""
    match = await approve_match(db, tenant_id, match_id, user_id)
    if not match:
        return None
    return await execute_match(db, tenant_id, match_id, user_id)


async def approve_all_pending(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    import_id: uuid.UUID | None = None,
    min_confidence: int = 0,
) -> dict[str, int]:
    """Approve and execute all pending matches above a confidence threshold.

    H18: each match runs in its own savepoint — one failing match rolls back
    only its own partial bookings (no orphan trust deposits) and the rest of
    the batch continues.

    Returns {"executed": n, "failed": m}.
    """
    query = select(PaymentMatch).where(
        PaymentMatch.tenant_id == tenant_id,
        PaymentMatch.status == MatchStatus.PENDING,
        PaymentMatch.confidence >= min_confidence,
    )

    if import_id:
        query = query.join(BankTransaction).where(
            BankTransaction.import_id == import_id,
        )

    result = await db.execute(query)
    # Snapshot ids before the loop: after a savepoint rollback the ORM
    # objects are expired and attribute access would trigger sync IO.
    match_ids = [m.id for m in result.scalars().all()]

    executed = 0
    failed = 0
    for match_id in match_ids:
        try:
            async with db.begin_nested():
                outcome = await approve_and_execute_match(db, tenant_id, match_id, user_id)
            if outcome:
                executed += 1
        except Exception as e:
            failed += 1
            logger.error("Failed to execute match %s: %s", match_id, e)

    return {"executed": executed, "failed": failed}


async def manual_match(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    case_id: uuid.UUID,
    note: str | None = None,
) -> PaymentMatch:
    """Manually match a transaction to a case.

    Creates a match with method=MANUAL and confidence=100,
    then immediately approves it.
    """
    # Verify transaction exists and belongs to tenant
    txn_result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.id == transaction_id,
            BankTransaction.tenant_id == tenant_id,
        )
    )
    txn = txn_result.scalar_one_or_none()
    if not txn:
        raise ValueError("Transactie niet gevonden")

    # Verify case exists and belongs to tenant
    case_result = await db.execute(
        select(Case).where(
            Case.id == case_id,
            Case.tenant_id == tenant_id,
        )
    )
    case = case_result.scalar_one_or_none()
    if not case:
        raise ValueError("Dossier niet gevonden")

    # Guard: a transaction may not get a second match while a prior auto-match is
    # still PENDING — approving both double-counts the payment (AUDIT-MEDIUM).
    # Surface a 409 so the user resolves the open match before linking manually.
    existing_pending = await db.execute(
        select(PaymentMatch).where(
            PaymentMatch.tenant_id == tenant_id,
            PaymentMatch.transaction_id == transaction_id,
            PaymentMatch.status == MatchStatus.PENDING,
        )
    )
    if existing_pending.scalars().first() is not None:
        raise ConflictError(
            "Deze transactie heeft al een openstaande match. "
            "Beoordeel die eerst voordat je handmatig koppelt."
        )

    # Create match
    match = PaymentMatch(
        tenant_id=tenant_id,
        transaction_id=transaction_id,
        case_id=case_id,
        match_method=MatchMethod.MANUAL,
        confidence=MATCH_CONFIDENCE[MatchMethod.MANUAL],
        match_details=note or "Handmatig gekoppeld door gebruiker",
        status=MatchStatus.APPROVED,
        reviewed_by_id=user_id,
        reviewed_at=datetime.now(UTC),
    )
    db.add(match)
    txn.is_matched = True

    await db.flush()
    await db.refresh(match)
    return match
