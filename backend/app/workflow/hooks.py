"""Workflow hooks for payments and trust-fund deposits."""

import logging
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseActivity
from app.cases.schemas import TERMINAL_STATUSES

logger = logging.getLogger(__name__)


def _fmt_eur(value: Decimal | int | float) -> str:
    """Format Decimal/float as Dutch currency: € 1.234,56."""
    d = Decimal(str(value))
    formatted = f"{d:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {formatted}"


async def on_payment_received(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    payment_amount: Decimal,
    user_id: uuid.UUID | None = None,
) -> Case | None:
    """Hook called after a payment is registered.

    Checks if the case is fully paid and automatically transitions to 'betaald'.
    Returns the case if status was changed, None otherwise.
    """
    from app.collections.service import get_case_outstanding

    # Get the case
    result = await db.execute(select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id))
    case = result.scalar_one_or_none()
    if case is None:
        return None

    # Don't auto-close already terminal cases (B3, S198: 4 vaste statussen).
    if case.status in TERMINAL_STATUSES:
        return None

    # Openstaand saldo mét alle zaakinstellingen (BIK-override etc. — Codex #3).
    try:
        total_outstanding = await get_case_outstanding(db, tenant_id, case)
    except Exception:
        logger.exception(
            f"Workflow hook: failed to calculate outstanding for case {case.case_number}"
        )
        return None

    if total_outstanding <= Decimal("0"):
        # B3 (S198): bij €0 openstaand direct op 'betaald' + date_closed. De vroegere
        # workflow-transitievalidatie leunde op de lege workflow_statuses-tabel en
        # vuurde dus nóóit — vervangen door deze directe zet. De €0-guard hierboven
        # blijft: 'betaald' betekent letterlijk volledig voldaan.
        old_status = case.status

        case.status = "betaald"
        case.date_closed = date.today()
        await db.flush()

        # Log the auto-transition
        activity = CaseActivity(
            tenant_id=tenant_id,
            case_id=case.id,
            user_id=None,  # System-generated
            activity_type="status_change",
            title=f"Status automatisch gewijzigd: {old_status} \u2192 betaald",
            description=(
                f"Zaak automatisch op 'betaald' gezet na ontvangst betaling van "
                f"{_fmt_eur(payment_amount)}. Totaal openstaand: € 0,00."
            ),
            old_status=old_status,
            new_status="betaald",
        )
        db.add(activity)
        await db.flush()

        logger.info(
            f"Workflow hook: case {case.case_number} auto-transitioned to 'betaald' "
            f"after payment of EUR {payment_amount}"
        )

        await db.refresh(case)
        return case

    return None


async def on_derdengelden_deposit(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    amount: Decimal,
    user_id: uuid.UUID | None = None,
) -> None:
    """Hook called after a derdengelden deposit.

    Logs the deposit in the case audit trail.
    """
    result = await db.execute(select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id))
    case = result.scalar_one_or_none()
    if case is None:
        return

    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case_id,
        user_id=user_id,
        activity_type="derdengelden",
        title=f"Derdengelden ontvangen: {_fmt_eur(amount)}",
        description=f"Storting op derdengeldenrekening voor zaak {case.case_number}.",
    )
    db.add(activity)
    await db.flush()
