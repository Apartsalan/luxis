"""Follow-up recommendation service — rules-based workflow advisor for incasso cases."""

import logging
import math
import uuid
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.followup_models import (
    ACTION_LABELS,
    URGENCY_LABELS,
    FollowupRecommendation,
    RecommendationStatus,
    RecommendedAction,
)
from app.ai_agent.followup_schemas import (
    FollowupRecommendationList,
    FollowupRecommendationOut,
    FollowupStatsOut,
)
from app.cases.models import Case, CaseActivity
from app.documents.docx_service import render_docx
from app.documents.models import GeneratedDocument
from app.documents.pdf_service import docx_to_pdf
from app.email.send_service import send_with_attachment
from app.incasso.models import IncassoPipelineStep
from app.incasso.service import (
    _auto_complete_tasks,
    _try_auto_advance,
    list_pipeline_steps,
)

logger = logging.getLogger(__name__)


# ── Scan for follow-ups ──────────────────────────────────────────────────


async def scan_for_followups(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> int:
    """Scan all active incasso cases and create recommendations for cases needing action.

    A recommendation is created when:
    - Case is in a pipeline step for >= min_wait_days (deadline_status = orange/red)
    - No PENDING recommendation exists for this case
    - No EXECUTED recommendation exists for this case + same step

    Returns: count of new recommendations created.
    """
    # Get active pipeline steps
    steps = await list_pipeline_steps(db, tenant_id, active_only=True)
    step_by_id: dict[uuid.UUID, IncassoPipelineStep] = {s.id: s for s in steps}

    # Get all active incasso cases with a pipeline step assigned
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.case_type == "incasso",
            Case.is_active.is_(True),
            Case.status.notin_(["betaald", "afgesloten"]),
            Case.incasso_step_id.isnot(None),
        )
    )
    cases = list(result.scalars().all())

    if not cases:
        return 0

    # Get all existing recommendations for this tenant to check for duplicates
    case_ids = [c.id for c in cases]
    existing_result = await db.execute(
        select(FollowupRecommendation).where(
            FollowupRecommendation.tenant_id == tenant_id,
            FollowupRecommendation.case_id.in_(case_ids),
            FollowupRecommendation.status.in_(
                [RecommendationStatus.PENDING, RecommendationStatus.EXECUTED]
            ),
        )
    )
    existing_recs = list(existing_result.scalars().all())

    # Build lookup sets for deduplication
    pending_case_ids = {
        r.case_id for r in existing_recs if r.status == RecommendationStatus.PENDING
    }
    executed_case_step_pairs = {
        (r.case_id, r.incasso_step_id)
        for r in existing_recs
        if r.status == RecommendationStatus.EXECUTED
    }

    created = 0
    today = date.today()

    for case in cases:
        step = step_by_id.get(case.incasso_step_id)
        if not step:
            continue

        # Calculate days in step
        if case.step_entered_at:
            days_in_step = (today - case.step_entered_at.date()).days
        else:
            days_in_step = (today - case.date_opened).days

        # Check if case is ready for action (orange or red)
        min_d = step.min_wait_days
        max_d = step.max_wait_days if step.max_wait_days > 0 else (min_d * 2 if min_d > 0 else 0)

        if days_in_step < min_d:
            continue  # Still green — not ready

        # Skip if already has pending recommendation
        if case.id in pending_case_ids:
            continue

        # Skip if already executed for this same step
        if (case.id, step.id) in executed_case_step_pairs:
            continue

        # Determine urgency
        urgency = "overdue" if (max_d > 0 and days_in_step >= max_d) else "normal"

        # Determine recommended action
        if step.template_type:
            action = RecommendedAction.GENERATE_DOCUMENT
            reasoning = (
                f"Dossier {case.case_number} staat {days_in_step} dagen in stap "
                f"'{step.name}'. Minimale wachttijd ({min_d} dagen) bereikt. "
                f"Document '{step.template_type}' kan gegenereerd en verstuurd worden."
            )
        else:
            action = RecommendedAction.ESCALATE
            reasoning = (
                f"Dossier {case.case_number} staat {days_in_step} dagen in stap "
                f"'{step.name}'. Minimale wachttijd ({min_d} dagen) bereikt. "
                f"Geen briefsjabloon beschikbaar — handmatige beoordeling nodig."
            )

        outstanding = Decimal(str(case.total_principal)) - Decimal(str(case.total_paid))
        outstanding = outstanding.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        rec = FollowupRecommendation(
            tenant_id=tenant_id,
            case_id=case.id,
            incasso_step_id=step.id,
            recommended_action=action,
            reasoning=reasoning,
            days_in_step=days_in_step,
            outstanding_amount=outstanding,
            urgency=urgency,
            status=RecommendationStatus.PENDING,
        )
        db.add(rec)
        created += 1

    if created:
        await db.flush()
        logger.info("Follow-up scan for tenant: %d nieuwe aanbevelingen aangemaakt", created)

    return created


# ── CRUD + review workflow ────────────────────────────────────────────────


def _rec_to_response(rec: FollowupRecommendation) -> FollowupRecommendationOut:
    """Convert a FollowupRecommendation model to response schema."""
    return FollowupRecommendationOut(
        id=rec.id,
        case_id=rec.case_id,
        case_number=rec.case.case_number if rec.case else "?",
        client_name=rec.case.client.name if rec.case and rec.case.client else None,
        opposing_party_name=(
            rec.case.opposing_party.name if rec.case and rec.case.opposing_party else None
        ),
        incasso_step_id=rec.incasso_step_id,
        step_name=rec.incasso_step.name if rec.incasso_step else "?",
        recommended_action=rec.recommended_action,
        action_label=ACTION_LABELS.get(rec.recommended_action, rec.recommended_action),
        reasoning=rec.reasoning,
        days_in_step=rec.days_in_step,
        outstanding_amount=rec.outstanding_amount,
        urgency=rec.urgency,
        urgency_label=URGENCY_LABELS.get(rec.urgency, rec.urgency),
        status=rec.status,
        reviewed_by_name=(
            rec.reviewed_by.full_name
            if rec.reviewed_by and hasattr(rec.reviewed_by, "full_name")
            else (rec.reviewed_by.email if rec.reviewed_by else None)
        ),
        reviewed_at=rec.reviewed_at,
        review_note=rec.review_note,
        executed_at=rec.executed_at,
        execution_result=rec.execution_result,
        generated_document_id=rec.generated_document_id,
        created_at=rec.created_at,
    )


async def list_recommendations(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    status_filter: str | None = None,
    case_id: uuid.UUID | None = None,
    page: int = 1,
    per_page: int = 20,
) -> FollowupRecommendationList:
    """List follow-up recommendations with optional status filter and pagination."""
    query = select(FollowupRecommendation).where(
        FollowupRecommendation.tenant_id == tenant_id,
    )
    count_query = select(func.count(FollowupRecommendation.id)).where(
        FollowupRecommendation.tenant_id == tenant_id,
    )

    if status_filter:
        query = query.where(FollowupRecommendation.status == status_filter)
        count_query = count_query.where(FollowupRecommendation.status == status_filter)

    if case_id:
        query = query.where(FollowupRecommendation.case_id == case_id)
        count_query = count_query.where(FollowupRecommendation.case_id == case_id)

    # Order: pending first (by urgency desc, created_at asc), then by created_at desc
    query = query.order_by(
        FollowupRecommendation.status.asc(),  # pending comes first alphabetically
        FollowupRecommendation.created_at.desc(),
    )

    # Pagination
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    recs = list(result.scalars().all())

    return FollowupRecommendationList(
        items=[_rec_to_response(r) for r in recs],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


async def get_recommendation(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rec_id: uuid.UUID,
) -> FollowupRecommendationOut | None:
    """Get a single recommendation by ID."""
    result = await db.execute(
        select(FollowupRecommendation).where(
            FollowupRecommendation.tenant_id == tenant_id,
            FollowupRecommendation.id == rec_id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        return None
    return _rec_to_response(rec)


async def get_recommendation_stats(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> FollowupStatsOut:
    """Get counts per recommendation status."""
    result = await db.execute(
        select(
            FollowupRecommendation.status,
            func.count(FollowupRecommendation.id),
        )
        .where(FollowupRecommendation.tenant_id == tenant_id)
        .group_by(FollowupRecommendation.status)
    )
    counts = {row[0]: row[1] for row in result.all()}
    return FollowupStatsOut(
        pending=counts.get("pending", 0),
        approved=counts.get("approved", 0),
        rejected=counts.get("rejected", 0),
        executed=counts.get("executed", 0),
    )


async def approve_recommendation(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rec_id: uuid.UUID,
    user_id: uuid.UUID,
) -> FollowupRecommendation | None:
    """Approve a pending recommendation."""
    result = await db.execute(
        select(FollowupRecommendation).where(
            FollowupRecommendation.tenant_id == tenant_id,
            FollowupRecommendation.id == rec_id,
            FollowupRecommendation.status == RecommendationStatus.PENDING,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        return None

    rec.status = RecommendationStatus.APPROVED
    rec.reviewed_by_id = user_id
    rec.reviewed_at = datetime.now(UTC)
    await db.flush()
    return rec


async def reject_recommendation(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rec_id: uuid.UUID,
    user_id: uuid.UUID,
    note: str | None = None,
) -> FollowupRecommendation | None:
    """Reject a pending recommendation."""
    result = await db.execute(
        select(FollowupRecommendation).where(
            FollowupRecommendation.tenant_id == tenant_id,
            FollowupRecommendation.id == rec_id,
            FollowupRecommendation.status == RecommendationStatus.PENDING,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        return None

    rec.status = RecommendationStatus.REJECTED
    rec.reviewed_by_id = user_id
    rec.reviewed_at = datetime.now(UTC)
    rec.review_note = note
    await db.flush()
    return rec


async def execute_recommendation(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rec_id: uuid.UUID,
    user_id: uuid.UUID,
) -> FollowupRecommendation | None:
    """Execute an approved recommendation.

    For GENERATE_DOCUMENT: renders the DOCX, creates a GeneratedDocument,
    sends email with PDF if opposing party has email, auto-completes pipeline
    tasks, and tries auto-advance to next step.

    For ESCALATE: creates a manual review WorkflowTask.
    """
    result = await db.execute(
        select(FollowupRecommendation).where(
            FollowupRecommendation.tenant_id == tenant_id,
            FollowupRecommendation.id == rec_id,
            FollowupRecommendation.status == RecommendationStatus.APPROVED,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        return None

    # Load case with relationships
    case_result = await db.execute(select(Case).where(Case.id == rec.case_id))
    case = case_result.scalar_one_or_none()
    if not case:
        rec.status = RecommendationStatus.EXECUTED
        rec.executed_at = datetime.now(UTC)
        rec.execution_result = "Dossier niet gevonden"
        await db.flush()
        return rec

    # Load the step
    step_result = await db.execute(
        select(IncassoPipelineStep).where(IncassoPipelineStep.id == rec.incasso_step_id)
    )
    step = step_result.scalar_one_or_none()

    execution_parts: list[str] = []

    is_generate = (
        rec.recommended_action == RecommendedAction.GENERATE_DOCUMENT
        and step
        and step.template_type
    )
    if is_generate:
        try:
            # Render the document
            docx_bytes, filename, tpl_type, tpl_snapshot = await render_docx(
                db, tenant_id, case, step.template_type
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

            rec.generated_document_id = doc.id
            execution_parts.append(f"Document '{tpl_type}' gegenereerd")

            # Send email with PDF if possible
            if case.opposing_party and case.opposing_party.email:
                try:
                    pdf_bytes = await docx_to_pdf(docx_bytes)
                    pdf_filename = filename.replace(".docx", ".pdf")

                    # Build email from step templates or use defaults
                    email_subject = (
                        step.email_subject_template or f"{step.name} - {case.case_number}"
                    )
                    email_body = step.email_body_template or (
                        f"Geachte heer/mevrouw,\n\nBijgevoegd treft u de "
                        f"{step.name.lower()} aan inzake dossier {case.case_number}."
                    )

                    # Simple Jinja2-style replacements
                    for old, new in [
                        ("{{ zaak.zaaknummer }}", case.case_number),
                        ("{{ zaak.omschrijving }}", case.description or ""),
                        ("{{ wederpartij.naam }}", case.opposing_party.name or ""),
                    ]:
                        email_subject = email_subject.replace(old, new)
                        email_body = email_body.replace(old, new)

                    email_log = await send_with_attachment(
                        db,
                        user_id,
                        tenant_id,
                        to=case.opposing_party.email,
                        subject=email_subject,
                        body_html=f"<p>{email_body.replace(chr(10), '<br>')}</p>",
                        attachments=[(pdf_filename, pdf_bytes, "pdf")],
                        case_id=case.id,
                        document_id=doc.id,
                        recipient_name=case.opposing_party.name or "",
                    )

                    if email_log.status == "sent":
                        execution_parts.append(f"Email verstuurd naar {case.opposing_party.email}")
                    else:
                        execution_parts.append("Email verzending mislukt")
                except Exception as e:
                    logger.error("Follow-up email failed for %s: %s", case.case_number, e)
                    execution_parts.append(f"Email fout: {e}")
            else:
                execution_parts.append("Geen email verstuurd (geen emailadres wederpartij)")

            # Auto-complete pipeline tasks for this step
            completed = await _auto_complete_tasks(db, tenant_id, case.id, step_id=step.id)
            if completed:
                execution_parts.append(f"{completed} taak/taken afgerond")

            # Try auto-advance to next step
            advanced = await _try_auto_advance(db, tenant_id, case, user_id)
            if advanced:
                execution_parts.append("Doorgeschoven naar volgende stap")

            # Log activity
            activity = CaseActivity(
                tenant_id=tenant_id,
                case_id=case.id,
                user_id=user_id,
                activity_type="automation",
                title=f"Follow-up uitgevoerd: {step.name}",
                description=(
                    "Automatische follow-up aanbeveling uitgevoerd. "
                    + ". ".join(execution_parts)
                    + "."
                ),
            )
            db.add(activity)

        except Exception as e:
            logger.error("Follow-up execution failed for %s: %s", case.case_number, e)
            execution_parts.append(f"Fout: {e}")

    elif rec.recommended_action == RecommendedAction.ESCALATE:
        from app.workflow.models import WorkflowTask

        task = WorkflowTask(
            tenant_id=tenant_id,
            case_id=case.id,
            assigned_to_id=case.assigned_to_id,
            task_type="manual_review",
            title=f"Handmatige beoordeling: {case.case_number}",
            due_date=date.today(),
            status="due",
            auto_execute=False,
            action_config={"source": "followup_advisor"},
        )
        db.add(task)
        execution_parts.append("Handmatige review-taak aangemaakt")

        activity = CaseActivity(
            tenant_id=tenant_id,
            case_id=case.id,
            user_id=user_id,
            activity_type="automation",
            title="Follow-up: handmatige beoordeling",
            description=(
                f"Dossier staat {rec.days_in_step} dagen in stap "
                f"'{step.name if step else '?'}'. Handmatige review-taak aangemaakt."
            ),
        )
        db.add(activity)

    rec.status = RecommendationStatus.EXECUTED
    rec.executed_at = datetime.now(UTC)
    rec.execution_result = ". ".join(execution_parts) if execution_parts else "Uitgevoerd"
    await db.flush()

    return rec


async def approve_and_execute_recommendation(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rec_id: uuid.UUID,
    user_id: uuid.UUID,
) -> FollowupRecommendation | None:
    """Approve and immediately execute a recommendation (1-click flow)."""
    rec = await approve_recommendation(db, tenant_id, rec_id, user_id)
    if not rec:
        return None
    return await execute_recommendation(db, tenant_id, rec_id, user_id)
