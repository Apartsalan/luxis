"""Workflow hooks — automatic actions triggered by status changes and payments.

These hooks are called from the cases and collections services to automate
workflow actions and maintain an audit trail in CaseActivity.

Supports auto-execution of send_email tasks: generates a PDF from a DOCX
template and sends it to the opposing party's email address.
"""

import logging
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseActivity
from app.workflow.models import WorkflowTask

logger = logging.getLogger(__name__)


def _fmt_eur(value: Decimal | int | float) -> str:
    """Format Decimal/float as Dutch currency: € 1.234,56."""
    d = Decimal(str(value))
    formatted = f"{d:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {formatted}"


async def _auto_execute_send_email(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    task: WorkflowTask,
) -> None:
    """Auto-execute a send_email task: render DOCX → PDF → send email.

    action_config should contain:
        template_type: str  — which DOCX template to render
        recipient_field: str — "wederpartij" or "client" (default: "wederpartij")
    """
    from app.documents.docx_service import _tenant_ctx, load_tenant, render_docx
    from app.documents.models import GeneratedDocument
    from app.documents.pdf_service import docx_to_pdf
    from app.email.models import EmailLog
    from app.email.service import is_configured as smtp_is_configured
    from app.email.service import send_email
    from app.email.templates import document_sent

    config = task.action_config or {}
    template_type = config.get("template_type")
    if not template_type:
        logger.warning(f"send_email task {task.id}: geen template_type in action_config")
        return

    if not smtp_is_configured():
        logger.warning(f"send_email task {task.id}: SMTP niet geconfigureerd, taak overgeslagen")
        return

    # Determine recipient
    recipient_field = config.get("recipient_field", "wederpartij")
    contact = case.opposing_party if recipient_field == "wederpartij" else case.client
    if not contact or not contact.email:
        logger.warning(f"send_email task {task.id}: geen e-mailadres voor {recipient_field}")
        return

    # Render DOCX
    docx_bytes, filename, tpl_type, tpl_snapshot = await render_docx(
        db, tenant_id, case, template_type
    )

    # Store GeneratedDocument
    doc = GeneratedDocument(
        tenant_id=tenant_id,
        case_id=case.id,
        generated_by_id=None,  # System-generated
        title=f"{tpl_type} - {case.case_number}",
        document_type=tpl_type,
        template_type=tpl_type,
        template_snapshot=tpl_snapshot,
    )
    db.add(doc)
    await db.flush()

    # Convert to PDF
    pdf_bytes = await docx_to_pdf(docx_bytes)
    pdf_filename = filename.replace(".docx", ".pdf")

    # Build email
    tenant = await load_tenant(db, tenant_id)
    kantoor = _tenant_ctx(tenant)
    subject, html_body = document_sent(
        kantoor=kantoor,
        recipient_name=contact.name or "",
        document_title=doc.title,
        case_number=case.case_number,
    )

    # Send and log
    email_log = EmailLog(
        tenant_id=tenant_id,
        case_id=case.id,
        document_id=doc.id,
        template="document_sent",
        recipient=contact.email,
        subject=subject,
        status="sent",
    )

    try:
        await send_email(
            to=contact.email,
            subject=subject,
            html_body=html_body,
            attachments=[(pdf_filename, pdf_bytes, "pdf")],
        )
    except Exception as e:
        email_log.status = "failed"
        email_log.error_message = str(e)
        logger.error(f"send_email task {task.id}: verzenden mislukt: {e}")

    db.add(email_log)
    await db.flush()

    # Mark task as completed
    task.status = "completed"
    task.completed_at = datetime.now(UTC)
    await db.flush()

    logger.info(
        f"send_email task {task.id}: {email_log.status} — "
        f"{template_type} naar {contact.email} voor zaak {case.case_number}"
    )


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
    Auto-executes send_email tasks if configured.
    """
    from app.workflow.service import evaluate_rules_for_transition

    created_tasks = await evaluate_rules_for_transition(db, tenant_id, case, new_status)

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

    # Auto-execute send_email tasks that are due immediately
    for task in created_tasks:
        if task.auto_execute and task.task_type == "send_email" and task.status == "due":
            try:
                await _auto_execute_send_email(db, tenant_id, case, task)
            except Exception:
                logger.exception(f"Auto-execute send_email failed for task {task.id}")

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
    result = await db.execute(select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id))
    case = result.scalar_one_or_none()
    if case is None:
        return None

    # Don't auto-close already terminal cases (B3, S198: 4 vaste statussen).
    if case.status in ("betaald", "afgesloten"):
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
            include_btw_on_bik=not case.client.is_btw_plichtig if case.client else False,
        )
    except Exception:
        logger.exception(
            f"Workflow hook: failed to calculate financial summary for case {case.case_number}"
        )
        return None

    total_outstanding = summary.get("total_outstanding", Decimal("1"))

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
