"""Workflow hooks — automatic actions triggered by status changes and payments.

These hooks are called from the cases and collections services to automate
workflow actions and maintain an audit trail in CaseActivity.
"""

import logging
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseActivity
from app.workflow.models import WorkflowStatus, WorkflowTask

logger = logging.getLogger(__name__)


async def on_status_change(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    old_status: str,
    new_status: str,
    user_id: uuid.UUID | None = None,
) -> list[WorkflowTask]:
    """Hook called after every status change.

    Creates tasks based on workflow rules and logs automated actions.
    Already called from cases/service.py via evaluate_rules_for_transition.
    This is a higher-level wrapper that also handles auto-execute tasks.
    """
    from app.workflow.service import evaluate_rules_for_transition

    created_tasks = await evaluate_rules_for_transition(
        db, tenant_id, case, new_status
    )

    # Log each auto-created task in the audit trail
    for task in created_tasks:
        activity = CaseActivity(
            tenant_id=tenant_id,
            case_id=case.id,
            user_id=None,  # System-generated
            activity_type="automation",
            title=f"Taak aangemaakt: {task.title}",
            description=(
                f"Automatisch aangemaakt door workflow regel. "
                f"Deadline: {task.due_date.strftime('%d-%m-%Y')}. "
                f"Type: {task.task_type}."
            ),
        )
        db.add(activity)

    if created_tasks:
        await db.flush()
        logger.info(
            f"Workflow hook: {len(created_tasks)} tasks created for case "
            f"{case.case_number} after status change {old_status} → {new_status}"
        )

    return created_tasks


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
    from app.collections.service import get_financial_summary

    # Get the case
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id)
    )
    case = result.scalar_one_or_none()
    if case is None:
        return None

    # Don't auto-close already terminal cases
    to_status = await db.execute(
        select(WorkflowStatus).where(
            WorkflowStatus.tenant_id == tenant_id,
            WorkflowStatus.slug == case.status,
            WorkflowStatus.is_active.is_(True),
        )
    )
    current_status = to_status.scalar_one_or_none()
    if current_status and current_status.is_terminal:
        return None

    # Calculate financial summary to check if fully paid
    try:
        summary = await get_financial_summary(
            db,
            tenant_id,
            case_id,
            case.interest_type,
            case.contractual_rate,
            case.contractual_compound,
        )
    except Exception:
        logger.exception(
            f"Workflow hook: failed to calculate financial summary for case {case.case_number}"
        )
        return None

    total_outstanding = summary.get("total_outstanding", Decimal("1"))

    if total_outstanding <= Decimal("0"):
        # Case is fully paid — transition to 'betaald'
        old_status = case.status

        # Check that 'betaald' transition is allowed
        from app.workflow.service import validate_transition

        validation = await validate_transition(db, tenant_id, case, "betaald")
        if not validation.allowed:
            logger.warning(
                f"Workflow hook: case {case.case_number} is fully paid but "
                f"transition to 'betaald' not allowed: {validation.errors}"
            )
            # Log the warning anyway
            activity = CaseActivity(
                tenant_id=tenant_id,
                case_id=case.id,
                user_id=None,
                activity_type="automation",
                title="Zaak volledig betaald — handmatige statuswijziging nodig",
                description=(
                    f"Totaal openstaand: EUR 0,00. "
                    f"Automatische transitie naar 'betaald' niet mogelijk vanuit status '{old_status}'. "
                    f"Wijzig de status handmatig."
                ),
            )
            db.add(activity)
            await db.flush()
            return None

        # Execute the transition
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
                f"EUR {payment_amount:,.2f}. Totaal openstaand: EUR 0,00."
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

        # Also evaluate rules for the betaald status
        await on_status_change(
            db, tenant_id, case, old_status, "betaald"
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
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id)
    )
    case = result.scalar_one_or_none()
    if case is None:
        return

    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case_id,
        user_id=user_id,
        activity_type="derdengelden",
        title=f"Derdengelden ontvangen: EUR {amount:,.2f}",
        description=f"Storting op derdengeldenrekening voor zaak {case.case_number}.",
    )
    db.add(activity)
    await db.flush()
