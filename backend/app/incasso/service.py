"""Incasso pipeline service — business logic for pipeline steps and batch actions."""

import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseActivity
from app.documents.docx_service import build_base_context, render_docx
from app.documents.models import GeneratedDocument
from app.documents.pdf_service import docx_to_pdf
from app.email.incasso_templates import render_incasso_email
from app.email.send_service import send_with_attachment
from app.email.templates import _render_base, document_sent
from app.incasso.models import IncassoPipelineStep
from app.incasso.schemas import (
    BatchActionResult,
    BatchBlocker,
    BatchPreviewResponse,
    CaseInPipeline,
    PipelineColumn,
    PipelineOverview,
    PipelineStepCreate,
    PipelineStepResponse,
    PipelineStepUpdate,
    QueueCounts,
)
from app.shared.exceptions import BadRequestError, NotFoundError
from app.workflow.models import WorkflowTask

logger = logging.getLogger(__name__)

# ── Pipeline Step CRUD ────────────────────────────────────────────────────


async def list_pipeline_steps(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    active_only: bool = True,
) -> list[IncassoPipelineStep]:
    """List all pipeline steps for a tenant, ordered by sort_order."""
    query = select(IncassoPipelineStep).where(
        IncassoPipelineStep.tenant_id == tenant_id,
    )
    if active_only:
        query = query.where(IncassoPipelineStep.is_active.is_(True))
    query = query.order_by(IncassoPipelineStep.sort_order)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_pipeline_step_by_id(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    step_id: uuid.UUID,
) -> IncassoPipelineStep:
    """Get a single pipeline step by ID."""
    result = await db.execute(
        select(IncassoPipelineStep).where(
            IncassoPipelineStep.tenant_id == tenant_id,
            IncassoPipelineStep.id == step_id,
        )
    )
    step = result.scalar_one_or_none()
    if not step:
        raise NotFoundError("Pipeline stap niet gevonden")
    return step


async def create_pipeline_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: PipelineStepCreate,
) -> IncassoPipelineStep:
    """Create a new pipeline step."""
    step = IncassoPipelineStep(
        tenant_id=tenant_id,
        **data.model_dump(),
    )
    db.add(step)
    await db.flush()
    await db.refresh(step)
    return step


async def update_pipeline_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    step_id: uuid.UUID,
    data: PipelineStepUpdate,
) -> IncassoPipelineStep:
    """Update an existing pipeline step."""
    step = await get_pipeline_step_by_id(db, tenant_id, step_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(step, field, value)
    await db.flush()
    await db.refresh(step)
    return step


async def delete_pipeline_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    step_id: uuid.UUID,
) -> None:
    """Soft-delete a pipeline step. Unassign cases first."""
    step = await get_pipeline_step_by_id(db, tenant_id, step_id)

    # Unassign any cases from this step
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.incasso_step_id == step_id,
        )
    )
    for case in result.scalars().all():
        case.incasso_step_id = None

    step.is_active = False
    await db.flush()


async def seed_default_steps(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[IncassoPipelineStep]:
    """Seed default incasso pipeline steps for a tenant (if no active ones exist)."""
    existing = await list_pipeline_steps(db, tenant_id, active_only=True)
    if existing:
        return existing

    defaults = [
        {
            "name": "Eerste sommatie",
            "sort_order": 1,
            "min_wait_days": 0,
            "max_wait_days": 3,
            "template_type": "sommatie_drukte",
        },
        {
            "name": "Tweede sommatie",
            "sort_order": 2,
            "min_wait_days": 7,
            "max_wait_days": 14,
            "template_type": "wederom_sommatie_kort",
        },
        {
            "name": "Aankondiging faillissement",
            "sort_order": 3,
            "min_wait_days": 7,
            "max_wait_days": 14,
            "template_type": "sommatie_laatste_voor_fai",
        },
        {
            "name": "Faillissement",
            "sort_order": 4,
            "min_wait_days": 3,
            "max_wait_days": 7,
            "template_type": "faillissement_dreigbrief",
        },
    ]

    steps = []
    for d in defaults:
        step = IncassoPipelineStep(tenant_id=tenant_id, **d)
        db.add(step)
        steps.append(step)

    await db.flush()
    for step in steps:
        await db.refresh(step)
    return steps


# ── Pipeline Step Response Helper ─────────────────────────────────────────


def step_to_response(step: IncassoPipelineStep) -> PipelineStepResponse:
    """Convert a pipeline step model to response schema."""
    return PipelineStepResponse(
        id=step.id,
        name=step.name,
        sort_order=step.sort_order,
        min_wait_days=step.min_wait_days,
        max_wait_days=step.max_wait_days,
        template_id=step.template_id,
        template_type=step.template_type,
        template_name=step.template.name if step.template else None,
        email_subject_template=step.email_subject_template,
        email_body_template=step.email_body_template,
        is_active=step.is_active,
        created_at=step.created_at,
        updated_at=step.updated_at,
    )


# ── Pipeline Overview ─────────────────────────────────────────────────────


def _compute_deadline_status(
    days_in_step: int,
    step: IncassoPipelineStep | None,
) -> str:
    """Compute deadline color: green (waiting), orange (ready), red (overdue), gray (no step)."""
    if not step:
        return "gray"
    min_d = step.min_wait_days
    max_d = step.max_wait_days if step.max_wait_days > 0 else (min_d * 2 if min_d > 0 else 0)

    if max_d > 0 and days_in_step >= max_d:
        return "red"
    if days_in_step >= min_d:
        return "orange"
    return "green"


def _case_to_pipeline_item(
    case: Case,
    step: IncassoPipelineStep | None = None,
) -> CaseInPipeline:
    """Convert a Case model to CaseInPipeline schema."""
    outstanding = Decimal(str(case.total_principal)) - Decimal(str(case.total_paid))

    # Use step_entered_at if available, otherwise fallback to date_opened
    if case.step_entered_at:
        step_entered_date = case.step_entered_at.date()
        days_in_step = (date.today() - step_entered_date).days
    else:
        days_in_step = (date.today() - case.date_opened).days

    return CaseInPipeline(
        id=case.id,
        case_number=case.case_number,
        client_name=case.client.name if case.client else "Onbekend",
        opposing_party_name=case.opposing_party.name if case.opposing_party else None,
        total_principal=Decimal(str(case.total_principal)),
        total_paid=Decimal(str(case.total_paid)),
        outstanding=outstanding.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        days_in_step=days_in_step,
        incasso_step_id=case.incasso_step_id,
        status=case.status,
        date_opened=case.date_opened.isoformat(),
        deadline_status=_compute_deadline_status(days_in_step, step),
    )


async def get_pipeline_overview(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> PipelineOverview:
    """Get all incasso cases grouped by pipeline step."""
    # Get active steps
    steps = await list_pipeline_steps(db, tenant_id, active_only=True)

    # Get all active incasso cases
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.case_type == "incasso",
            Case.is_active.is_(True),
            Case.status.notin_(["betaald", "afgesloten"]),
        )
    )
    all_cases = list(result.scalars().all())

    # Group cases by step
    step_by_id: dict[uuid.UUID, IncassoPipelineStep] = {s.id: s for s in steps}
    case_map: dict[uuid.UUID, list[CaseInPipeline]] = {s.id: [] for s in steps}
    unassigned: list[CaseInPipeline] = []

    for case in all_cases:
        step = step_by_id.get(case.incasso_step_id) if case.incasso_step_id else None
        item = _case_to_pipeline_item(case, step)
        if case.incasso_step_id and case.incasso_step_id in case_map:
            case_map[case.incasso_step_id].append(item)
        else:
            unassigned.append(item)

    # Build columns
    columns = []
    for step in steps:
        cases_in_step = case_map.get(step.id, [])
        columns.append(
            PipelineColumn(
                step=step_to_response(step),
                cases=cases_in_step,
                count=len(cases_in_step),
            )
        )

    return PipelineOverview(
        columns=columns,
        unassigned=unassigned,
        total_cases=len(all_cases),
    )


# ── Batch Preview ─────────────────────────────────────────────────────────


async def batch_preview(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_ids: list[uuid.UUID],
    action: str,
    target_step_id: uuid.UUID | None = None,
) -> BatchPreviewResponse:
    """Pre-flight check for a batch action."""
    if not case_ids:
        raise BadRequestError("Geen dossiers geselecteerd")

    # Fetch the selected cases
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.id.in_(case_ids),
            Case.case_type == "incasso",
            Case.is_active.is_(True),
        )
    )
    cases = list(result.scalars().all())

    blocked: list[BatchBlocker] = []
    needs_step: list[CaseInPipeline] = []
    email_blocked: list[BatchBlocker] = []
    ready = 0
    email_ready = 0

    if action == "advance_step":
        if not target_step_id:
            raise BadRequestError("Geen doelstap opgegeven voor statuswijziging")

        # Verify target step exists (raises NotFoundError if not)
        await get_pipeline_step_by_id(db, tenant_id, target_step_id)

        for case in cases:
            # Check blockers
            if case.status in ("betaald", "afgesloten"):
                blocked.append(
                    BatchBlocker(
                        case_id=case.id,
                        case_number=case.case_number,
                        reason=f"Dossier heeft status '{case.status}'",
                    )
                )
                continue

            # All non-blocked cases are ready for advance_step
            # (unassigned cases will be moved directly to the target step)
            ready += 1

    elif action == "generate_document":
        # Load all pipeline steps for checking template_type
        steps = await list_pipeline_steps(db, tenant_id, active_only=True)
        step_map = {s.id: s for s in steps}

        for case in cases:
            if not case.incasso_step_id:
                needs_step.append(_case_to_pipeline_item(case))
                continue

            step = step_map.get(case.incasso_step_id)
            if step and not step.template_type:
                blocked.append(
                    BatchBlocker(
                        case_id=case.id,
                        case_number=case.case_number,
                        reason=f"Stap '{step.name}' heeft geen briefsjabloon",
                    )
                )
                continue

            ready += 1

            # Check email readiness (opposing party has email address)
            if case.opposing_party and case.opposing_party.email:
                email_ready += 1
            else:
                email_blocked.append(
                    BatchBlocker(
                        case_id=case.id,
                        case_number=case.case_number,
                        reason="Geen e-mailadres wederpartij",
                    )
                )

    elif action == "recalculate_interest":
        for case in cases:
            ready += 1

    else:
        raise BadRequestError(f"Onbekende actie: {action}")

    return BatchPreviewResponse(
        action=action,
        total_selected=len(cases),
        ready=ready,
        blocked=blocked,
        needs_step_assignment=needs_step,
        email_ready=email_ready,
        email_blocked=email_blocked,
    )


# ── Pipeline Automation Helpers ───────────────────────────────────────────


async def _create_tasks_for_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    step: IncassoPipelineStep,
) -> list[WorkflowTask]:
    """Create workflow task(s) for a case entering a pipeline step.

    - Steps with template_type: create a 'generate_document' task
    - Steps without template_type: create a 'manual_review' task
    Due date = today + step.min_wait_days
    """
    due_date = date.today() + timedelta(days=step.min_wait_days)

    if step.template_type:
        task_type = "generate_document"
        title = f"{step.name} genereren voor zaak {case.case_number}"
    else:
        task_type = "manual_review"
        title = f"{step.name} controleren voor zaak {case.case_number}"

    task = WorkflowTask(
        tenant_id=tenant_id,
        case_id=case.id,
        assigned_to_id=case.assigned_to_id,
        task_type=task_type,
        title=title,
        due_date=due_date,
        status="pending" if step.min_wait_days > 0 else "due",
        auto_execute=False,
        action_config={"source": "pipeline", "step_id": str(step.id)},
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case.id,
        user_id=None,
        activity_type="automation",
        title=f"Taak aangemaakt: {title}",
        description=(
            f"Automatisch aangemaakt bij instap in '{step.name}'. "
            f"Deadline: {due_date.strftime('%d-%m-%Y')}. Type: {task_type}."
        ),
    )
    db.add(activity)
    await db.flush()

    return [task]


async def _auto_complete_tasks(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    step_id: uuid.UUID | None = None,
) -> int:
    """Auto-complete matching open tasks after document generation.

    Matches: task_type in (generate_document, send_letter),
             status in (pending, due, overdue), is_active=True
    When step_id is provided, only completes pipeline tasks for that step.
    Returns: count of tasks completed.
    """
    query = select(WorkflowTask).where(
        WorkflowTask.tenant_id == tenant_id,
        WorkflowTask.case_id == case_id,
        WorkflowTask.task_type.in_(["generate_document", "send_letter"]),
        WorkflowTask.status.in_(["pending", "due", "overdue"]),
        WorkflowTask.is_active.is_(True),
    )

    if step_id:
        query = query.where(
            WorkflowTask.action_config["source"].astext == "pipeline",
            WorkflowTask.action_config["step_id"].astext == str(step_id),
        )

    result = await db.execute(query)
    tasks = list(result.scalars().all())

    now = datetime.now(UTC)
    for task in tasks:
        task.status = "completed"
        task.completed_at = now

    if tasks:
        await db.flush()

    return len(tasks)


async def _try_auto_advance(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    user_id: uuid.UUID,
    step_list: list[IncassoPipelineStep] | None = None,
) -> bool:
    """Check if all tasks are done for a case; if so, advance to next pipeline step.

    Args:
        step_list: Pre-fetched sorted pipeline steps to avoid N+1 queries.
                   If None, fetches from DB.

    Returns True if the case was advanced, False otherwise.
    """
    if not case.incasso_step_id:
        return False

    if case.status in ("betaald", "afgesloten"):
        return False

    # Check for remaining open pipeline tasks for the current step only.
    # We scope to action_config.source == "pipeline" to avoid blocking
    # on initial case tasks or manually created tasks.
    result = await db.execute(
        select(WorkflowTask)
        .where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.case_id == case.id,
            WorkflowTask.status.in_(["pending", "due", "overdue"]),
            WorkflowTask.is_active.is_(True),
            WorkflowTask.action_config["source"].astext == "pipeline",
            WorkflowTask.action_config["step_id"].astext == str(case.incasso_step_id),
        )
        .limit(1)
    )
    if result.scalar_one_or_none():
        return False  # Still has open pipeline tasks for this step

    # Find current and next step
    if step_list is None:
        steps = await list_pipeline_steps(db, tenant_id, active_only=True)
        step_list = sorted(steps, key=lambda s: s.sort_order)

    current_idx = None
    for i, step in enumerate(step_list):
        if step.id == case.incasso_step_id:
            current_idx = i
            break

    if current_idx is None:
        return False

    if current_idx + 1 >= len(step_list):
        logger.debug(
            "Case %s is on last step '%s' — no auto-advance possible",
            case.case_number,
            step_list[current_idx].name,
        )
        return False

    next_step = step_list[current_idx + 1]
    old_step_name = step_list[current_idx].name
    now = datetime.now(UTC)

    case.incasso_step_id = next_step.id
    case.step_entered_at = now
    await db.flush()

    await _create_tasks_for_step(db, tenant_id, case, next_step)

    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case.id,
        user_id=None,
        activity_type="pipeline_advance",
        title=f"Pipeline: {old_step_name} \u2192 {next_step.name}",
        description=(
            f"Automatisch doorgeschoven na voltooiing van alle taken. "
            f"Vorige stap: {old_step_name}. Nieuwe stap: {next_step.name}."
        ),
    )
    db.add(activity)
    await db.flush()

    logger.info(
        "Auto-advanced case %s from '%s' to '%s'",
        case.case_number,
        old_step_name,
        next_step.name,
    )

    return True


# ── Batch Execute ─────────────────────────────────────────────────────────


async def batch_execute(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_ids: list[uuid.UUID],
    action: str,
    target_step_id: uuid.UUID | None = None,
    auto_assign_step: bool = False,
    send_email: bool = False,
) -> BatchActionResult:
    """Execute a batch action on selected cases."""
    if not case_ids:
        raise BadRequestError("Geen dossiers geselecteerd")

    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.id.in_(case_ids),
            Case.case_type == "incasso",
            Case.is_active.is_(True),
        )
    )
    cases = list(result.scalars().all())

    processed = 0
    skipped = 0
    errors: list[str] = []
    generated_doc_ids: list[uuid.UUID] = []
    tasks_auto_completed = 0
    cases_auto_advanced = 0
    emails_sent = 0
    emails_failed = 0

    now = datetime.now(UTC)

    if action == "advance_step":
        if not target_step_id:
            raise BadRequestError("Geen doelstap opgegeven")

        target_step = await get_pipeline_step_by_id(db, tenant_id, target_step_id)

        for case in cases:
            if case.status in ("betaald", "afgesloten"):
                skipped += 1
                errors.append(f"{case.case_number}: status '{case.status}' — overgeslagen")
                continue

            case.incasso_step_id = target_step.id
            case.step_entered_at = now
            processed += 1

            # Audit trail for step assignment
            activity = CaseActivity(
                tenant_id=tenant_id,
                case_id=case.id,
                user_id=user_id,
                activity_type="pipeline_change",
                title=f"Pipeline stap: {target_step.name}",
                description=f"Dossier verplaatst naar stap '{target_step.name}'.",
            )
            db.add(activity)

            # Create tasks for the new step
            await _create_tasks_for_step(db, tenant_id, case, target_step)

    elif action == "generate_document":
        # Load steps to get template_type
        steps = await list_pipeline_steps(db, tenant_id, active_only=True)
        step_map = {s.id: s for s in steps}

        for case in cases:
            if not case.incasso_step_id:
                skipped += 1
                errors.append(f"{case.case_number}: geen pipeline stap — overgeslagen")
                continue

            step = step_map.get(case.incasso_step_id)
            if not step or not step.template_type:
                skipped += 1
                step_name = step.name if step else "onbekend"
                errors.append(
                    f"{case.case_number}: stap '{step_name}' heeft geen "
                    f"briefsjabloon — overgeslagen"
                )
                continue

            try:
                # Build context once — reused for DOCX archive + HTML email
                base_context = await build_base_context(db, tenant_id, case)

                docx_bytes, filename, tpl_type, tpl_snapshot = await render_docx(
                    db,
                    tenant_id,
                    case,
                    step.template_type,
                    pre_built_context=base_context,
                )

                doc = GeneratedDocument(
                    tenant_id=tenant_id,
                    case_id=case.id,
                    generated_by_id=user_id,
                    title=f"{tpl_type} - {case.case_number}",
                    document_type=tpl_type,
                    template_type=tpl_type,
                    template_snapshot=tpl_snapshot,
                )
                db.add(doc)
                await db.flush()
                await db.refresh(doc)
                generated_doc_ids.append(doc.id)
                processed += 1

                # Send email if requested
                if send_email and case.opposing_party and case.opposing_party.email:
                    try:
                        # Try HTML body (brief as email content, no attachment)
                        inline_html = render_incasso_email(step.template_type, base_context)

                        if inline_html:
                            # Brief IS the email body — no PDF attachment
                            email_subject = f"{step.name} inzake dossier {case.case_number}"
                            email_log = await send_with_attachment(
                                db,
                                user_id,
                                tenant_id,
                                to=case.opposing_party.email,
                                subject=email_subject,
                                body_html=inline_html,
                                attachments=[],
                                case_id=case.id,
                                document_id=doc.id,
                                recipient_name=(case.opposing_party.name or ""),
                            )
                        else:
                            # Fallback: PDF as attachment (dagvaarding, etc.)
                            pdf_bytes = await docx_to_pdf(docx_bytes)
                            pdf_filename = filename.replace(".docx", ".pdf")

                            email_subject, email_body = _build_step_email(step, case, db, tenant_id)

                            email_log = await send_with_attachment(
                                db,
                                user_id,
                                tenant_id,
                                to=case.opposing_party.email,
                                subject=email_subject,
                                body_html=email_body,
                                attachments=[
                                    (pdf_filename, pdf_bytes, "pdf"),
                                ],
                                case_id=case.id,
                                document_id=doc.id,
                                recipient_name=(case.opposing_party.name or ""),
                            )

                        if email_log.status == "sent":
                            emails_sent += 1
                        else:
                            emails_failed += 1
                            errors.append(
                                f"{case.case_number}: e-mail mislukt — {email_log.error_message}"
                            )
                    except Exception as email_exc:
                        emails_failed += 1
                        errors.append(f"{case.case_number}: e-mail fout — {email_exc}")
                        logger.error(
                            "Batch email failed for %s: %s",
                            case.case_number,
                            email_exc,
                        )

                # Auto-complete matching pipeline tasks for this step
                completed_count = await _auto_complete_tasks(
                    db, tenant_id, case.id, case.incasso_step_id
                )
                tasks_auto_completed += completed_count

                # Try auto-advance (always, even if no tasks were
                # completed — case may already have all tasks done)
                advanced = await _try_auto_advance(
                    db,
                    tenant_id,
                    case,
                    user_id,
                    step_list=steps,
                )
                if advanced:
                    cases_auto_advanced += 1
            except Exception as exc:
                logger.error(
                    "Batch document generation failed for %s: %s",
                    case.case_number,
                    exc,
                )
                skipped += 1
                errors.append(f"{case.case_number}: fout bij genereren — {exc}")

    elif action == "recalculate_interest":
        from app.collections.interest import calculate_case_interest
        from app.collections.models import Claim

        for case in cases:
            try:
                # Fetch active claims for this case
                claims_result = await db.execute(
                    select(Claim).where(
                        Claim.case_id == case.id,
                        Claim.is_active.is_(True),
                    )
                )
                claims = claims_result.scalars().all()

                if not claims:
                    skipped += 1
                    continue

                claim_dicts = [
                    {
                        "id": str(c.id),
                        "description": c.description,
                        "principal_amount": c.principal_amount,
                        "default_date": c.default_date,
                        "rate_basis": c.rate_basis,
                    }
                    for c in claims
                ]

                result = await calculate_case_interest(
                    db=db,
                    case_id=str(case.id),
                    interest_type=case.interest_type,
                    contractual_rate=case.contractual_rate,
                    contractual_compound=case.contractual_compound,
                    claims=claim_dicts,
                    calc_date=date.today(),
                )

                # Update case financial totals
                case.total_principal = result["total_principal"]
                processed += 1
            except Exception as exc:
                logger.error(
                    "Interest recalculation failed for %s: %s",
                    case.case_number,
                    exc,
                )
                skipped += 1
                errors.append(f"{case.case_number}: renteberekening mislukt — {exc}")

    else:
        raise BadRequestError(f"Onbekende actie: {action}")

    await db.flush()

    return BatchActionResult(
        action=action,
        processed=processed,
        skipped=skipped,
        errors=errors,
        generated_document_ids=generated_doc_ids,
        tasks_auto_completed=tasks_auto_completed,
        cases_auto_advanced=cases_auto_advanced,
        emails_sent=emails_sent,
        emails_failed=emails_failed,
    )


# ── Email Template Helper ─────────────────────────────────────────────────


def _build_step_email(
    step: IncassoPipelineStep,
    case: Case,
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> tuple[str, str]:
    """Build email subject + HTML body for a pipeline step.

    Uses the step's custom email templates if set, otherwise falls back
    to the generic document_sent() template.

    Returns:
        (subject, html_body)
    """
    if step.email_subject_template and step.email_body_template:
        from jinja2 import Environment

        env = Environment(autoescape=False)

        # Build a simple context for email templates (lighter than full docx context)
        context = {
            "zaak": {
                "zaaknummer": case.case_number,
                "omschrijving": case.description or "",
            },
            "wederpartij": {
                "naam": (case.opposing_party.name if case.opposing_party else ""),
            },
            "client": {
                "naam": case.client.name if case.client else "",
            },
            "kantoor": {
                "naam": "",  # Will be filled from tenant if available
            },
            "stap": step.name,
        }

        # Try to get kantoor naam from tenant
        if hasattr(case, "tenant") and case.tenant:
            context["kantoor"]["naam"] = case.tenant.name or ""

        subject = env.from_string(step.email_subject_template).render(context)
        body_text = env.from_string(step.email_body_template).render(context)
        body_html = body_text.replace("\n", "<br>")

        # Wrap in the standard email layout
        kantoor = context["kantoor"]
        body_html = _render_base(kantoor, body_html)
        return subject, body_html

    # Fallback: use the generic document_sent template
    kantoor_dict = {"naam": "", "adres": "", "postcode_stad": ""}
    recipient_name = case.opposing_party.name if case.opposing_party else ""
    return document_sent(
        kantoor=kantoor_dict,
        recipient_name=recipient_name,
        document_title=step.name,
        case_number=case.case_number,
    )


# ── Smart Work Queues ────────────────────────────────────────────────────


async def get_queue_counts(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> QueueCounts:
    """Calculate badge counts for Smart Work Queue tabs."""
    # Get active steps ordered by sort_order
    steps = await list_pipeline_steps(db, tenant_id, active_only=True)
    if not steps:
        return QueueCounts()

    # Build a lookup: step_id -> step, and step_id -> next step
    step_list = sorted(steps, key=lambda s: s.sort_order)
    next_step_map: dict[uuid.UUID, IncassoPipelineStep] = {}
    for i, step in enumerate(step_list):
        if i + 1 < len(step_list):
            next_step_map[step.id] = step_list[i + 1]

    # Get all active incasso cases (not closed/paid)
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.case_type == "incasso",
            Case.is_active.is_(True),
            Case.status.notin_(["betaald", "afgesloten"]),
        )
    )
    all_cases = list(result.scalars().all())

    ready_next_step = 0
    wik_expired = 0
    unassigned = 0

    for case in all_cases:
        if not case.incasso_step_id:
            unassigned += 1
            continue

        # Calculate days in current step
        if case.step_entered_at:
            days_in_step = (date.today() - case.step_entered_at.date()).days
        else:
            days_in_step = (date.today() - case.date_opened).days

        # Check if ready for next step
        next_step = next_step_map.get(case.incasso_step_id)
        if next_step and days_in_step >= next_step.min_wait_days:
            ready_next_step += 1

        # Check WIK 14-day expiry: cases in first step (Aanmaning) for >= 14 days
        if case.incasso_step_id == step_list[0].id and days_in_step >= 14:
            wik_expired += 1

    action_required = ready_next_step + unassigned

    return QueueCounts(
        ready_next_step=ready_next_step,
        wik_expired=wik_expired,
        action_required=action_required,
    )
