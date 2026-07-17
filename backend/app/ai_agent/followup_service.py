"""Follow-up recommendation service — rules-based workflow advisor for incasso cases."""

import html
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
    FollowupPreviewOut,
    FollowupRecommendationList,
    FollowupRecommendationOut,
    FollowupStatsOut,
)
from app.cases.models import Case, CaseActivity
from app.documents.docx_service import build_base_context, render_docx
from app.documents.models import GeneratedDocument
from app.documents.pdf_service import docx_to_pdf
from app.documents.rente_bijlage import build_rente_bijlage, wants_rente_bijlage
from app.email.incasso_templates import render_incasso_email
from app.email.oauth_service import get_tenant_send_account
from app.email.send_service import send_with_attachment
from app.email.subject import build_email_subject
from app.incasso.models import IncassoPipelineStep
from app.incasso.service import (
    _auto_complete_tasks,
    _try_auto_advance,
    list_pipeline_steps,
    mark_current_step_communication_sent,
)
from app.shared.exceptions import BadRequestError

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

        # Hold-stappen (Bijhouden regeling / On hold / Verweer beantwoorden) en
        # terminale stappen krijgen geen kalender-gedreven aanbeveling: hold-zaken
        # wachten bewust en verweer-zaken krijgen hun concept al via de e-mail-
        # trigger. Zonder deze guard zou elke zaak op zo'n stap (~100+ bij de
        # heropening) elke 30 min een ruis-aanbeveling opleveren.
        if step.is_hold_step or step.is_terminal:
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


def _live_days_in_step(rec: FollowupRecommendation) -> int:
    """Actuele dagen-in-stap i.p.v. de bevroren waarde van toen de aanbeveling
    werd aangemaakt.

    De opgeslagen `days_in_step` is een momentopname bij aanmaak; bij de
    BaseNet-import kregen alle zaken step_entered_at = importtijd, dus de eerste
    scan stempelde overal 0 en dat bleef staan (S217-gat). Zolang de zaak nog op
    de stap van de aanbeveling staat, rekenen we live; is de zaak doorgeschoven,
    dan is de bevroren waarde de juiste historische stand.
    """
    case = rec.case
    if case is None or case.incasso_step_id != rec.incasso_step_id:
        return rec.days_in_step
    anchor = case.step_entered_at.date() if case.step_entered_at else case.date_opened
    if anchor is None:
        return rec.days_in_step
    return max((date.today() - anchor).days, 0)


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
        days_in_step=_live_days_in_step(rec),
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

    # Load case with relationships (tenant-scoped — Codex-review portie 1)
    case_result = await db.execute(
        select(Case).where(Case.id == rec.case_id, Case.tenant_id == tenant_id)
    )
    case = case_result.scalar_one_or_none()
    if not case:
        # Dossier weg tussen scan en uitvoeren → NOOIT stil op "Uitgevoerd"
        # zetten (dat maskeert dat er niets gebeurd is).
        raise BadRequestError("Dossier niet gevonden — niets uitgevoerd")

    # Load the step (tenant-scoped)
    step_result = await db.execute(
        select(IncassoPipelineStep).where(
            IncassoPipelineStep.id == rec.incasso_step_id,
            IncassoPipelineStep.tenant_id == tenant_id,
        )
    )
    step = step_result.scalar_one_or_none()

    execution_parts: list[str] = []

    is_generate = (
        rec.recommended_action == RecommendedAction.GENERATE_DOCUMENT
        and step
        and step.template_type
    )
    if is_generate:
        # S205 — wettelijke waarborg art. 6:96 lid 6 BW, óók op dit verzendpad.
        # De "Uitvoeren"-knop rendert en verstuurt exact dezelfde stap-sommaties als
        # de batch; zonder deze gate was dit de tweede open zijdeur (S204-review).
        # Zelfde gedeelde helper → de regel loopt niet uit elkaar. Fout = luid falen
        # mét reden (niet stil op 'Uitgevoerd'); dekt ook approve_and_execute.
        from app.collections.compliance import check_dagenbrief_gate

        gate_reason = await check_dagenbrief_gate(
            db, tenant_id, case, step.name, case_number=case.case_number
        )
        if gate_reason is not None:
            raise BadRequestError(gate_reason)

        # B1 — verstuurpad. De meeste incassostappen (sommatie, faillissement-
        # dreigbrief, ...) zijn E-MAIL-sjablonen, geen Word-brieven. Probeer daarom
        # eerst de e-mailrenderer; alleen als die de sleutel niet kent val je terug
        # op een DOCX-brief met PDF-bijlage. Cruciaal: een mislukte verzending werpt
        # een fout op i.p.v. door te vallen — zo wordt niets meer vals als
        # "Uitgevoerd" geregistreerd terwijl er in werkelijkheid niets de deur uitging.
        if not (case.opposing_party and case.opposing_party.email):
            raise BadRequestError(
                f"{case.case_number}: geen e-mailadres wederpartij — er is niets verstuurd"
            )

        context = await build_base_context(db, tenant_id, case)
        inline_html = render_incasso_email(step.template_type, context)

        if inline_html is not None:
            # E-mailroute: de brief ís de e-mailtekst, geen bijlage.
            doc = GeneratedDocument(
                tenant_id=tenant_id,
                case_id=case.id,
                generated_by_id=user_id,
                title=f"{step.name} - {case.case_number}",
                document_type=step.template_type,
                template_type=step.template_type,
                content_html=inline_html,
            )
            db.add(doc)
            await db.flush()
            await db.refresh(doc)
            rec.generated_document_id = doc.id

            # S211: renteoverzicht als PDF-bijlage bij de 14-dagenbrief/eerste
            # sommatie wanneer de wederpartij privé aansprakelijk is (leest het
            # opgeslagen rechtsvorm-veld, nooit live de KvK).
            rente_attachments = await build_rente_bijlage(
                db, tenant_id, case, step, user_id
            )

            email_log = await send_with_attachment(
                db,
                user_id,
                tenant_id,
                to=case.opposing_party.email,
                subject=build_email_subject(
                    client_name=case.client.name if case.client else None,
                    debtor_name=case.opposing_party.name,
                    letter_type=step.name,
                    case_number=case.case_number,
                ),
                body_html=inline_html,
                attachments=rente_attachments,
                case_id=case.id,
                document_id=doc.id,
                recipient_name=case.opposing_party.name or "",
                send_as_tenant_account=True,
            )
        else:
            # DOCX-route (dagvaarding e.d.): brief als PDF-bijlage.
            docx_bytes, filename, tpl_type, tpl_snapshot = await render_docx(
                db, tenant_id, case, step.template_type, pre_built_context=context
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

            pdf_bytes = await docx_to_pdf(docx_bytes)
            pdf_filename = filename.replace(".docx", ".pdf")

            # S223 — altijd het vaste huisformaat; het oude BaseNet
            # email_subject_template ("TYPE / / ") is stale junk (geen UI bewerkt
            # het) en gaf een onderwerp zonder klant/debiteur.
            email_subject = build_email_subject(
                client_name=case.client.name if case.client else None,
                debtor_name=case.opposing_party.name if case.opposing_party else None,
                letter_type=step.name,
                case_number=case.case_number,
            )
            email_body = step.email_body_template or (
                f"Geachte heer/mevrouw,\n\nBijgevoegd treft u de "
                f"{step.name.lower()} aan inzake dossier {case.case_number}."
            )
            # S202 M4: de body wordt als HTML verstuurd (`<p>{email_body}</p>`),
            # dus database-velden (omschrijving, wederpartij-naam) escapen vóór ze
            # via de find/replace in de body belanden — anders zou een HTML-tag in
            # die velden als echte markup de deur uit gaan. Het onderwerp is platte
            # tekst, daar de rauwe waarde.
            for old, new in [
                ("{{ zaak.zaaknummer }}", case.case_number),
                ("{{ zaak.omschrijving }}", case.description or ""),
                ("{{ wederpartij.naam }}", case.opposing_party.name or ""),
            ]:
                email_subject = email_subject.replace(old, new)
                email_body = email_body.replace(old, html.escape(new))

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
                send_as_tenant_account=True,
            )

        if email_log.status != "sent":
            raise BadRequestError(
                f"{case.case_number}: e-mail niet verstuurd — "
                f"{getattr(email_log, 'error_message', None) or 'onbekende fout'}"
            )
        execution_parts.append(f"E-mail verstuurd naar {case.opposing_party.email}")

        # Vanaf hier is de verzending gelukt — nu pas de administratie bijwerken.
        # S207 (review S205): leg de verzending vast op de open staphistorie-rij,
        # net als het batch- en conceptpad — vóór de auto-advance de stap verlaat.
        # Zonder dit telt een via 'Uitvoeren' verstuurde 14-dagenbrief niet als
        # 'aantoonbaar verstuurd' voor de gate.
        await mark_current_step_communication_sent(
            db, tenant_id, case, document_id=doc.id
        )
        completed = await _auto_complete_tasks(db, tenant_id, case.id, step_id=step.id)
        if completed:
            execution_parts.append(f"{completed} taak/taken afgerond")

        advanced = await _try_auto_advance(db, tenant_id, case, user_id)
        if advanced:
            execution_parts.append("Doorgeschoven naar volgende stap")

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

    else:
        # GENERATE_DOCUMENT zonder (nog) een stap/sjabloon, of een onbekende
        # actie: er is niets gebeurd. Nooit stil op "Uitgevoerd" zetten
        # (Codex-review portie 1) — laat het luid falen zodat het zichtbaar blijft.
        raise BadRequestError(
            f"{case.case_number}: geen uitvoerbare actie (stap/sjabloon ontbreekt) — "
            "niets uitgevoerd"
        )

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


async def preview_recommendation(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rec_id: uuid.UUID,
    user_id: uuid.UUID,
) -> FollowupPreviewOut | None:
    """B13 — render wat er precies uitgaat, zónder te versturen.

    Bouwt exact dezelfde e-mail als `execute_recommendation` (e-mailroute), maar
    verzendt niets. Zo kan de gebruiker vóór de één-klik-verzending zien wat er
    de deur uitgaat en via welk afzender-adres.
    """
    result = await db.execute(
        select(FollowupRecommendation).where(
            FollowupRecommendation.tenant_id == tenant_id,
            FollowupRecommendation.id == rec_id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        return None

    case = (
        await db.execute(
            select(Case).where(Case.id == rec.case_id, Case.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if not case:
        return None

    step = (
        await db.execute(
            select(IncassoPipelineStep).where(
                IncassoPipelineStep.id == rec.incasso_step_id,
                IncassoPipelineStep.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()

    recipient_email = case.opposing_party.email if case.opposing_party else None
    recipient_name = case.opposing_party.name if case.opposing_party else None

    # Toon de afzender die de verzending ÉCHT gaat gebruiken — zelfde volgorde
    # als send_with_attachment: vast kantoorkanaal → account van de klikkende
    # gebruiker → vaste server-afzender (SMTP).
    sender_account = await get_tenant_send_account(db, tenant_id)
    if sender_account is None:
        from app.email.oauth_service import get_email_account

        sender_account = await get_email_account(db, user_id, tenant_id)
    if sender_account is not None:
        sender_email = sender_account.email_address
    else:
        from app.config import settings

        sender_email = settings.smtp_from or "(vaste server-afzender)"

    is_generate = (
        rec.recommended_action == RecommendedAction.GENERATE_DOCUMENT
        and step
        and step.template_type
    )
    if not is_generate:
        return FollowupPreviewOut(
            subject="(geen verzending)",
            body_html=(
                "<p>Deze aanbeveling verstuurt geen e-mail — er wordt een taak voor "
                "handmatige beoordeling aangemaakt.</p>"
            ),
            sender_email=sender_email,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            can_send=False,
            warning="Deze aanbeveling maakt een taak aan i.p.v. een verzending.",
        )

    can_send = bool(recipient_email)
    warning = (
        None
        if can_send
        else "Geen e-mailadres bij de wederpartij — er kan niets verstuurd worden."
    )

    context = await build_base_context(db, tenant_id, case)
    inline_html = render_incasso_email(step.template_type, context)

    if inline_html is not None:
        return FollowupPreviewOut(
            subject=build_email_subject(
                client_name=case.client.name if case.client else None,
                debtor_name=case.opposing_party.name if case.opposing_party else None,
                letter_type=step.name,
                case_number=case.case_number,
            ),
            body_html=inline_html,
            sender_email=sender_email,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            # S211: e-mailtekst zelf heeft geen bijlage, behalve het renteoverzicht
            # bij de 14-dagenbrief/eerste sommatie voor een privé aansprakelijke partij.
            has_attachment=wants_rente_bijlage(case, step),
            can_send=can_send,
            warning=warning,
        )

    # DOCX-route (dagvaarding e.d.) — brief als PDF-bijlage.
    # S223 — altijd het vaste huisformaat (zie boven).
    subject = build_email_subject(
        client_name=case.client.name if case.client else None,
        debtor_name=case.opposing_party.name if case.opposing_party else None,
        letter_type=step.name,
        case_number=case.case_number,
    )
    body = step.email_body_template or (
        f"Geachte heer/mevrouw,\n\nBijgevoegd treft u de {step.name.lower()} aan "
        f"inzake dossier {case.case_number}."
    )
    for old, new in [
        ("{{ zaak.zaaknummer }}", case.case_number),
        ("{{ zaak.omschrijving }}", case.description or ""),
        ("{{ wederpartij.naam }}", recipient_name or ""),
    ]:
        subject = subject.replace(old, new)
        body = body.replace(old, new)

    return FollowupPreviewOut(
        subject=subject,
        body_html=f"<p>{body.replace(chr(10), '<br>')}</p>",
        sender_email=sender_email,
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        has_attachment=True,
        can_send=can_send,
        warning=warning,
    )
