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
from app.documents.rente_bijlage import build_rente_bijlage
from app.email.incasso_templates import render_incasso_email
from app.email.send_service import send_with_attachment
from app.email.subject import build_email_subject
from app.email.templates import _render_base, document_sent
from app.incasso.models import CaseStepHistory, IncassoPipelineStep, StepTransition
from app.incasso.schemas import (
    BatchActionResult,
    BatchBlocker,
    BatchPreviewResponse,
    CaseInPipeline,
    CaseStepHistoryResponse,
    PipelineColumn,
    PipelineOverview,
    PipelineStepCreate,
    PipelineStepResponse,
    PipelineStepUpdate,
    QueueCounts,
    TransitionCreate,
    TransitionResponse,
    TransitionUpdate,
)
from app.shared.exceptions import BadRequestError, NotFoundError
from app.workflow.models import WorkflowTask

logger = logging.getLogger(__name__)

# ── Pipeline → status koppeling (B3, S198) ─────────────────────────────────────
# De status kent 4 vaste waarden (nieuw / in_behandeling / betaald / afgesloten).
# De incasso-PIJPLIJN is de motor; de status wordt door de pijplijn-stap gestuurd:
#   - een terminale eindstap "Betaald"   → status 'betaald'   (+ date_closed)
#   - een terminale eindstap "Afgesloten" → status 'afgesloten' (+ date_closed)
#   - elke andere (werk-)stap             → status 'in_behandeling' (date_closed leeg)
# De vroegere mapping naar de lege workflow_statuses-tabel (STEP_NAME_TO_STATUS +
# existence-check) vuurde nooit — die is vervangen door deze directe 4-status-logica.
# Terminale eindstappen worden herkend aan hun naam (de seed kent er precies 2).
_TERMINAL_STEP_STATUS: dict[str, str] = {
    "Betaald": "betaald",
    "Afgesloten": "afgesloten",
}


def status_for_step(step: IncassoPipelineStep) -> str:
    """Zaak-status die hoort bij een pijplijn-stap (B3, S198).

    Terminale eindstappen → betaald/afgesloten; elke werk-stap → in_behandeling.
    Sleutelt op `is_terminal` (niet op naam): een hernoemde of eigen terminale stap
    sluit de zaak veilig af i.p.v. 'm in in_behandeling-limbo op een verborgen
    terminale stap achter te laten (S198-review, Fable #4).
    """
    if step.is_terminal:
        return _TERMINAL_STEP_STATUS.get(step.name, "afgesloten")
    return "in_behandeling"

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
    """Seed default incasso pipeline steps for a tenant. Adds only missing steps (by name)."""
    existing = await list_pipeline_steps(db, tenant_id, active_only=True)
    existing_names = {s.name for s in existing}

    # Lisanne's officiële incasso-workflow (sessie 133, bron: docs/lisanne-incasso-workflow.md).
    # Hoofdpad = lineair, 4 dagen tussen stappen. Tussenstappen = handmatig.
    # B2C-pad (dagvaarding/vonnis) komt later — niet in deze seed.
    defaults = [
        # B2C-only startstap: de 14-dagenbrief (WIK art. 6:96 lid 6 BW) is bij een
        # particulier wettelijk verplicht en moet vóór de sommaties komen. Staat
        # daarom als eerste in de lijst → laagste sort_order → eerste stap voor B2C.
        {"name": "14-dagenbrief", "min_wait_days": 0, "max_wait_days": 15, "step_category": "minnelijk", "debtor_type": "b2c", "template_type": "14_dagenbrief"},
        # Hoofdpad (B2B verzoekschrift faillissement)
        {"name": "Eerste sommatie", "min_wait_days": 0, "max_wait_days": 4, "step_category": "minnelijk", "debtor_type": "both"},
        {"name": "Tweede sommatie", "min_wait_days": 4, "max_wait_days": 4, "step_category": "minnelijk", "debtor_type": "both"},
        {"name": "Derde sommatie", "min_wait_days": 4, "max_wait_days": 4, "step_category": "minnelijk", "debtor_type": "both"},
        {"name": "Sommatie laatste mogelijkheid", "min_wait_days": 4, "max_wait_days": 4, "step_category": "minnelijk", "debtor_type": "b2b"},
        {"name": "Verzoekschrift faillissement", "min_wait_days": 4, "max_wait_days": 4, "step_category": "gerechtelijk", "debtor_type": "b2b"},
        # Auto-trigger status
        {"name": "Verweer beantwoorden", "min_wait_days": 0, "max_wait_days": 0, "step_category": "administratief", "debtor_type": "both", "is_hold_step": True},
        # Tussenstappen (handmatig door Lisanne)
        {"name": "Opvragen stukken bij cliënt", "min_wait_days": 0, "max_wait_days": 0, "step_category": "administratief", "debtor_type": "both"},
        {"name": "Voorstel dagvaarding", "min_wait_days": 0, "max_wait_days": 0, "step_category": "administratief", "debtor_type": "both"},
        {"name": "Treffen van regeling", "min_wait_days": 0, "max_wait_days": 0, "step_category": "regeling", "debtor_type": "both"},
        {"name": "Bijhouden regeling", "min_wait_days": 0, "max_wait_days": 0, "step_category": "regeling", "debtor_type": "both", "is_hold_step": True},
        {"name": "Akkoord dagvaarden", "min_wait_days": 0, "max_wait_days": 0, "step_category": "administratief", "debtor_type": "both"},
        {"name": "On hold", "min_wait_days": 0, "max_wait_days": 0, "step_category": "administratief", "debtor_type": "both", "is_hold_step": True},
        # Afsluiting
        {"name": "Betaald", "min_wait_days": 0, "max_wait_days": 0, "step_category": "afsluiting", "debtor_type": "both", "is_terminal": True},
        {"name": "Afgesloten", "min_wait_days": 0, "max_wait_days": 0, "step_category": "afsluiting", "debtor_type": "both", "is_terminal": True, "requires_settled": True},
    ]

    max_order = max((s.sort_order for s in existing), default=0)
    new_steps = []
    for d in defaults:
        if d["name"] in existing_names:
            continue
        max_order += 1
        d["sort_order"] = max_order
        step = IncassoPipelineStep(tenant_id=tenant_id, **d)
        db.add(step)
        new_steps.append(step)

    if new_steps:
        await db.flush()
        for step in new_steps:
            await db.refresh(step)

    return list(existing) + new_steps


# ── Step Transition CRUD ──────────────────────────────────────────────────


async def list_transitions(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    from_step_id: uuid.UUID | None = None,
    active_only: bool = True,
) -> list[StepTransition]:
    """List transitions, optionally filtered by source step."""

    query = select(StepTransition).where(StepTransition.tenant_id == tenant_id)
    if from_step_id:
        query = query.where(StepTransition.from_step_id == from_step_id)
    if active_only:
        query = query.where(StepTransition.is_active.is_(True))
    query = query.order_by(StepTransition.priority)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_transition_by_id(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    transition_id: uuid.UUID,
) -> StepTransition:
    """Get a single transition by ID."""
    result = await db.execute(
        select(StepTransition).where(
            StepTransition.tenant_id == tenant_id,
            StepTransition.id == transition_id,
        )
    )
    t = result.scalar_one_or_none()
    if not t:
        raise NotFoundError("Overgang niet gevonden")
    return t


async def create_transition(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: TransitionCreate,
) -> StepTransition:
    """Create a new step transition."""
    import json as _json

    await get_pipeline_step_by_id(db, tenant_id, data.from_step_id)
    await get_pipeline_step_by_id(db, tenant_id, data.to_step_id)

    t = StepTransition(
        tenant_id=tenant_id,
        from_step_id=data.from_step_id,
        to_step_id=data.to_step_id,
        trigger_type=data.trigger_type,
        action=data.action,
        condition=_json.dumps(data.condition) if data.condition else None,
        priority=data.priority,
        is_default=data.is_default,
        label=data.label,
    )
    db.add(t)
    await db.flush()
    await db.refresh(t)
    return t


async def update_transition(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    transition_id: uuid.UUID,
    data: TransitionUpdate,
) -> StepTransition:
    """Update an existing transition."""
    import json as _json

    t = await get_transition_by_id(db, tenant_id, transition_id)
    updates = data.model_dump(exclude_unset=True)
    if "condition" in updates:
        updates["condition"] = _json.dumps(updates["condition"]) if updates["condition"] else None
    for field, value in updates.items():
        setattr(t, field, value)
    await db.flush()
    await db.refresh(t)
    return t


async def delete_transition(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    transition_id: uuid.UUID,
) -> None:
    """Hard-delete a transition."""
    t = await get_transition_by_id(db, tenant_id, transition_id)
    await db.delete(t)
    await db.flush()


def transition_to_response(t: StepTransition) -> TransitionResponse:
    """Convert StepTransition model to response schema."""
    import json as _json

    condition = None
    if t.condition:
        try:
            condition = _json.loads(t.condition)
        except (ValueError, TypeError):
            condition = None

    return TransitionResponse(
        id=t.id,
        from_step_id=t.from_step_id,
        from_step_name=t.from_step.name if t.from_step else "Onbekend",
        to_step_id=t.to_step_id,
        to_step_name=t.to_step.name if t.to_step else "Onbekend",
        trigger_type=t.trigger_type,
        action=t.action,
        condition=condition,
        priority=t.priority,
        is_default=t.is_default,
        label=t.label,
        is_active=t.is_active,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


async def seed_default_transitions(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[StepTransition]:
    """Seed default transitions for Lisanne's incasso workflow."""
    import json as _json

    steps = await seed_default_steps(db, tenant_id)

    step_map = {s.name: s.id for s in steps}

    existing = await list_transitions(db, tenant_id, active_only=False)
    existing_keys = {
        (t.from_step_id, t.to_step_id, t.trigger_type) for t in existing
    }

    # Lisanne's automation rules (sessie 133).
    # Schema: (from_step, to_step, trigger_type, action, condition, is_default, label)
    main_path = ["Eerste sommatie", "Tweede sommatie", "Derde sommatie", "Sommatie laatste mogelijkheid", "Verzoekschrift faillissement"]

    defaults: list[tuple[str, str, str, str, dict | None, bool, str]] = []

    # 1. Hoofdpad: 4 dagen timeout → advance naar volgende stap
    for i in range(len(main_path) - 1):
        defaults.append((
            main_path[i], main_path[i + 1],
            "timeout", "advance_to_step", {"days": 4}, True,
            "Geen reactie na 4 dagen",
        ))

    # 1b. B2C-start: na de 14-dagenbrief (wettelijke termijn van 14 dagen) door naar
    # de eerste sommatie als er niet betaald is. Zo loopt het B2C-pad door op dezelfde
    # sommatie-keten als B2B (de B2B-only stappen worden voor B2C overgeslagen).
    defaults.append((
        "14-dagenbrief", "Eerste sommatie",
        "timeout", "advance_to_step", {"days": 15}, True,
        "Geen betaling na 14-dagentermijn",
    ))

    # AUDIT-H12: GEEN debtor_response- of payment-rules meer seeden. Alleen
    # 'timeout' wordt door de rule-evaluator (evaluate_timeout_rules) gelezen.
    # - debtor_response: een binnenkomende verweer-mail wordt al afgehandeld door
    #   de classificatie-hook (automation_service.trigger_defense_response_for_email),
    #   onafhankelijk van deze tabel — een rule hier was dode dubbele config.
    # - payment: werd nergens geëvalueerd, dus de regel deed niets.
    # Beide toonden loze "Automatische regels" in de UI. Bestaande dode rules
    # worden gedeactiveerd door migratie s151_dead_pipeline_rules.

    new_transitions = []
    for from_name, to_name, trigger, action, cond, is_def, lbl in defaults:
        from_id = step_map.get(from_name)
        to_id = step_map.get(to_name)
        if not from_id or not to_id:
            continue
        if (from_id, to_id, trigger) in existing_keys:
            continue

        t = StepTransition(
            tenant_id=tenant_id,
            from_step_id=from_id,
            to_step_id=to_id,
            trigger_type=trigger,
            action=action,
            condition=_json.dumps(cond) if cond else None,
            priority=len(new_transitions),
            is_default=is_def,
            label=lbl,
        )
        db.add(t)
        new_transitions.append(t)

    if new_transitions:
        await db.flush()
        for t in new_transitions:
            await db.refresh(t)

    return list(existing) + new_transitions


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
        step_category=step.step_category,
        debtor_type=step.debtor_type,
        is_terminal=step.is_terminal,
        is_hold_step=step.is_hold_step,
        is_active=step.is_active,
        created_at=step.created_at,
        updated_at=step.updated_at,
    )


# ── Step Movement & History ──────────────────────────────────────────────


async def move_case_to_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    target_step: IncassoPipelineStep,
    user_id: uuid.UUID | None = None,
    trigger_type: str = "manual",
    notes: str | None = None,
    template_sent: bool = False,
    email_sent: bool = False,
    document_id: uuid.UUID | None = None,
) -> CaseStepHistory:
    """Move a case to a target pipeline step — single source of truth for all step transitions."""
    # FIN-2: een dossier mag niet definitief afgesloten worden zolang er nog
    # derdengelden op staan (of trust-transacties op goedkeuring wachten). Voda
    # art. 6.19: clientgeld moet eerst uitbetaald/verrekend worden. Zelfde bron
    # en melding als de archiveer-guard (cases.service.delete_case).
    if target_step.requires_settled:
        from app.trust_funds.service import get_unsettled_reason

        reason = await get_unsettled_reason(db, tenant_id, case.id)
        if reason:
            raise BadRequestError(reason)

    # S198-review (Codex #2): een zaak handmatig of via batch naar de 'Betaald'-
    # eindstap slepen mag alleen als er niets meer openstaat — anders wordt een zaak
    # mét openstaand saldo als betaald weggeboekt en verdwijnt uit de werkvoorraad.
    # Sluiten mét restant loopt via 'Afsluiten' (status afgesloten). De auto-paden
    # (creatie/auto-advance) sturen nooit naar een terminale eindstap, dus die raakt
    # dit niet.
    if trigger_type in ("manual", "batch") and status_for_step(target_step) == "betaald":
        from app.collections.service import get_case_outstanding

        try:
            outstanding = await get_case_outstanding(db, tenant_id, case)
        except Exception as e:
            # AUDIT-H2: fail-CLOSED (zelfde reden als update_case_status). Een
            # onberekenbaar saldo mag een zaak nooit stil op de 'Betaald'-stap
            # wegboeken; oud fail-open nam €0 aan.
            raise BadRequestError(
                "Kan het openstaande saldo niet berekenen — probeer het opnieuw."
            ) from e
        if outstanding > Decimal("0.01"):
            raise BadRequestError(
                f"Zaak kan niet op de 'Betaald'-stap gezet worden: er staat nog "
                f"€ {outstanding} open. Gebruik 'Afsluiten' om met een restant af te sluiten."
            )

    now = datetime.now(UTC)
    old_step_name = None

    if case.incasso_step_id:
        result = await db.execute(
            select(CaseStepHistory)
            .where(
                CaseStepHistory.tenant_id == tenant_id,
                CaseStepHistory.case_id == case.id,
                CaseStepHistory.step_id == case.incasso_step_id,
                CaseStepHistory.exited_at.is_(None),
            )
            .order_by(CaseStepHistory.entered_at.desc())
            .limit(1)
        )
        current_history = result.scalar_one_or_none()
        if current_history:
            current_history.exited_at = now
            old_step_name = current_history.step.name if current_history.step else None

    history = CaseStepHistory(
        tenant_id=tenant_id,
        case_id=case.id,
        step_id=target_step.id,
        entered_at=now,
        triggered_by=user_id,
        trigger_type=trigger_type,
        template_sent=template_sent,
        email_sent=email_sent,
        document_id=document_id,
        notes=notes,
    )
    db.add(history)

    case.incasso_step_id = target_step.id
    case.step_entered_at = now

    # B3 (S198): de pijplijn stuurt de status. Een terminale eindstap sluit de zaak
    # (betaald/afgesloten + date_closed); elke werk-stap zet de zaak op
    # 'in_behandeling' en maakt een eventuele oude sluitdatum leeg (een zaak op een
    # actieve stap is niet gesloten — dit dekt ook heropenen via de stap-selector).
    # De pipeline_change-activity hieronder is het audit-spoor.
    new_status = status_for_step(target_step)
    if new_status != case.status:
        case.status = new_status
    if new_status in ("betaald", "afgesloten"):
        case.date_closed = now.date()
    else:
        case.date_closed = None

    await db.flush()
    await db.refresh(history)

    if old_step_name:
        title = f"Pipeline: {old_step_name} → {target_step.name}"
        description = f"Verplaatst van '{old_step_name}' naar '{target_step.name}'."
    else:
        title = f"Pipeline: toegewezen aan {target_step.name}"
        description = f"Dossier toegewezen aan stap '{target_step.name}'."

    if trigger_type == "auto_advance":
        description += " (automatisch doorgeschoven)"
    elif trigger_type == "batch":
        description += " (batch actie)"

    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case.id,
        user_id=user_id,
        activity_type="pipeline_change",
        title=title,
        description=description,
    )
    db.add(activity)
    await db.flush()

    # S220 punt 13 — zombie-opruiming: sluit openstaande follow-up-adviezen van dit
    # dossier zodra de stap wisselt. Een advies dat bij de oude stap hoorde is nu
    # verouderd (dubbel-verstuur-risico) én blokkeert de scanner (die ontdubbelt per
    # dossier op een PENDING-advies). Het advies dat déze wissel triggert staat op dat
    # moment op APPROVED (EXECUTED komt erná), dus alleen PENDING wordt geraakt.
    await supersede_open_recommendations(
        db, tenant_id, case.id, reason=f"Stap gewijzigd naar '{target_step.name}'"
    )

    return history


async def supersede_open_recommendations(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    *,
    reason: str,
) -> int:
    """Sluit alle openstaande (PENDING) follow-up-adviezen van een dossier.

    Gebruikt bij een stap-wissel: het advies hoorde bij de oude stap en is nu
    verouderd. Retourneert het aantal gesloten adviezen.
    """
    from app.ai_agent.followup_models import FollowupRecommendation, RecommendationStatus

    now = datetime.now(UTC)
    result = await db.execute(
        select(FollowupRecommendation).where(
            FollowupRecommendation.tenant_id == tenant_id,
            FollowupRecommendation.case_id == case_id,
            FollowupRecommendation.status == RecommendationStatus.PENDING,
        )
    )
    recs = result.scalars().all()
    for rec in recs:
        rec.status = RecommendationStatus.SUPERSEDED
        rec.reviewed_at = now
        rec.review_note = f"Automatisch gesloten: {reason} (advies verouderd)."
    if recs:
        await db.flush()
    return len(recs)


async def mark_current_step_communication_sent(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    *,
    template_sent: bool = True,
    email_sent: bool = True,
    document_id: uuid.UUID | None = None,
) -> CaseStepHistory | None:
    """Markeer de open staphistorie-rij van de HUIDIGE stap als verstuurd.

    Een brief/concept hoort bij de stap waarop het dossier op dat moment staat
    (bv. 'Eerste sommatie'). De `template_sent`/`email_sent`-vlaggen horen dus op
    de open (nog niet verlaten) history-rij van die stap — niet op de volgende stap.
    Zonder dit bleef een daadwerkelijk verzonden sommatie onzichtbaar in de
    staphistorie (alleen het concept werd getoond). Wordt aangeroepen op het
    verzendpad, vóór een eventuele advance naar de volgende stap.

    Geeft de bijgewerkte rij terug, of None als het dossier geen actieve stap of
    geen open history-rij heeft.
    """
    if not case.incasso_step_id:
        return None

    result = await db.execute(
        select(CaseStepHistory)
        .where(
            CaseStepHistory.tenant_id == tenant_id,
            CaseStepHistory.case_id == case.id,
            CaseStepHistory.step_id == case.incasso_step_id,
            CaseStepHistory.exited_at.is_(None),
        )
        .order_by(CaseStepHistory.entered_at.desc())
        .limit(1)
    )
    history = result.scalar_one_or_none()
    if history is None:
        return None

    if template_sent:
        history.template_sent = True
    if email_sent:
        history.email_sent = True
        # S207: leg het échte verzendmoment vast — de 14-dagenbrief-klok rekent
        # hierop. Alleen de EERSTE verzending telt (de wettelijke termijn loopt
        # vanaf de eerste brief; een herhaalde send verschuift het anker niet).
        if history.email_sent_at is None:
            history.email_sent_at = datetime.now(UTC)
    if document_id is not None:
        history.document_id = document_id

    await db.flush()
    return history


async def get_case_step_history(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> list[CaseStepHistoryResponse]:
    """Get step history for a case, newest first."""
    result = await db.execute(
        select(CaseStepHistory)
        .where(
            CaseStepHistory.tenant_id == tenant_id,
            CaseStepHistory.case_id == case_id,
        )
        .order_by(CaseStepHistory.entered_at.desc())
    )
    entries = list(result.scalars().all())

    return [
        CaseStepHistoryResponse(
            id=entry.id,
            step_id=entry.step_id,
            step_name=entry.step.name if entry.step else "Onbekend",
            step_category=entry.step.step_category if entry.step else "onbekend",
            entered_at=entry.entered_at,
            exited_at=entry.exited_at,
            triggered_by_name=(
                entry.triggered_by_user.full_name
                if entry.triggered_by_user
                else None
            ),
            trigger_type=entry.trigger_type,
            template_sent=entry.template_sent,
            email_sent=entry.email_sent,
            document_id=entry.document_id,
            notes=entry.notes,
        )
        for entry in entries
    ]


async def set_case_verweer(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    has_verweer: bool,
    verweer_note: str | None = None,
    verweer_date: date | None = None,
    user_id: uuid.UUID | None = None,
) -> Case:
    """Toggle verweer (objection/dispute) on a case."""
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.id == case_id,
            Case.is_active.is_(True),
        )
    )
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError("Dossier niet gevonden")

    case.has_verweer = has_verweer
    case.verweer_note = verweer_note
    case.verweer_date = verweer_date or (date.today() if has_verweer else None)

    if has_verweer:
        title = "Verweer geregistreerd"
        description = "Verweer gemarkeerd."
        if verweer_note:
            description += f" Notitie: {verweer_note}"
    else:
        title = "Verweer opgeheven"
        description = "Verweer-markering verwijderd."

    activity = CaseActivity(
        tenant_id=tenant_id,
        case_id=case.id,
        user_id=user_id,
        activity_type="verweer_change",
        title=title,
        description=description,
    )
    db.add(activity)
    await db.flush()

    return case


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
        step_name=step.name if step else None,
        debtor_type=case.debtor_type,
        has_verweer=case.has_verweer,
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
    terminal_step_ids = {s.id for s in steps if s.is_terminal}

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
    # AUDIT-H11 / B3 (S198): sinds S198 zet move_case_to_step de status wél mee
    # (terminale stap → betaald/afgesloten), dus de status-filter hierboven vangt
    # pijplijn-gesloten zaken al af. Deze terminale-stap-filter blijft als vangnet
    # voor de randgevallen (bv. een betaald-op-werkstap dat later op een terminale
    # stap belandt zonder statuswissel).
    all_cases = [c for c in all_cases if c.incasso_step_id not in terminal_step_ids]

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
                # AUDIT-H13: AI/HTML-stappen hebben geen vaste briefsjabloon —
                # batch-DOCX-generatie werkt daar niet. Verwijs naar de AI-
                # conceptflow per dossier i.p.v. een dood "geen sjabloon".
                blocked.append(
                    BatchBlocker(
                        case_id=case.id,
                        case_number=case.case_number,
                        reason=(
                            f"Stap '{step.name}' gebruikt AI-concepten i.p.v. een vaste "
                            f"briefsjabloon — open het dossier voor de AI-conceptknop"
                        ),
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

    verweer_count = sum(1 for c in cases if c.has_verweer)

    return BatchPreviewResponse(
        action=action,
        total_selected=len(cases),
        ready=ready,
        blocked=blocked,
        needs_step_assignment=needs_step,
        email_ready=email_ready,
        email_blocked=email_blocked,
        verweer_blocked=verweer_count,
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


async def _skip_review_drafts_for_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    step_id: uuid.UUID,
) -> int:
    """Skip open review_ai_draft tasks voor de huidige step.

    Wordt aangeroepen door batch_execute na succesvolle email-verzending.
    Reden: batch verstuurt via template (geen AI-draft), dus eventuele open
    'review_ai_draft' tasks zijn moot. Zonder dit blokkeren ze auto-advance.

    Status 'skipped' (niet 'completed') geeft aan dat de AI-draft niet via
    review werd afgehandeld maar via batch.
    """
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.case_id == case_id,
            WorkflowTask.task_type == "review_ai_draft",
            WorkflowTask.status.in_(["pending", "due", "overdue"]),
            WorkflowTask.is_active.is_(True),
            WorkflowTask.action_config["source"].astext == "pipeline",
            WorkflowTask.action_config["step_id"].astext == str(step_id),
        )
    )
    tasks = list(result.scalars().all())
    now = datetime.now(UTC)
    for task in tasks:
        task.status = "skipped"
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

    if case.has_verweer:
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

    # AUDIT-M2: auto-advance mag een zaak nooit naar een terminale eindstap
    # (Betaald/Afgesloten) of een hold-stap schuiven. De saldo-guard in
    # move_case_to_step draait alleen voor manual/batch, dus zonder deze check zou
    # een herordende of eigen terminale stap mét template een dossier mét saldo
    # stil als betaald wegboeken. Terminale + hold-stappen worden bewust handmatig
    # of via een expliciete trigger bereikt, niet via lineaire auto-advance.
    if next_step.is_terminal or next_step.is_hold_step:
        logger.debug(
            "Case %s: auto-advance gestopt vóór stap '%s' (terminaal/hold)",
            case.case_number,
            next_step.name,
        )
        return False

    old_step_name = step_list[current_idx].name

    await move_case_to_step(
        db, tenant_id, case, next_step,
        user_id=user_id,
        trigger_type="auto_advance",
    )
    await _create_tasks_for_step(db, tenant_id, case, next_step)

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

    if action == "advance_step":
        if not target_step_id:
            raise BadRequestError("Geen doelstap opgegeven")

        target_step = await get_pipeline_step_by_id(db, tenant_id, target_step_id)

        for case in cases:
            if case.status in ("betaald", "afgesloten"):
                skipped += 1
                errors.append(f"{case.case_number}: status '{case.status}' — overgeslagen")
                continue

            try:
                await move_case_to_step(
                    db, tenant_id, case, target_step,
                    user_id=user_id,
                    trigger_type="batch",
                )
            except BadRequestError as e:
                # FIN-2 afsluit-guard (onafgewikkelde derdengelden): sla dit dossier
                # over i.p.v. de hele batch te laten klappen — zelfde semantiek als
                # de andere skips in deze loop.
                skipped += 1
                errors.append(f"{case.case_number}: {e.detail}")
                continue
            processed += 1

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
                # AUDIT-H13: AI/HTML-stappen kennen geen DOCX-sjabloon — verwijs
                # naar de AI-conceptflow i.p.v. een dood "geen briefsjabloon".
                skipped += 1
                step_name = step.name if step else "onbekend"
                errors.append(
                    f"{case.case_number}: stap '{step_name}' gebruikt AI-concepten "
                    f"i.p.v. een vaste briefsjabloon — open het dossier voor de "
                    f"AI-conceptknop"
                )
                continue

            # S203 #5 / S205: wettelijke waarborg art. 6:96 lid 6 BW. Bij een consument
            # mag geen BIK-claimende sommatie de deur uit (a) vóór de 14-dagenbrief is
            # verstuurd, én (b) binnen 15 dagen ná die brief. De regel woont sinds S205
            # in één gedeelde helper (`check_dagenbrief_gate`) zodat batch, follow-up
            # 'Uitvoeren' en het AI-conceptpad niet uit elkaar lopen. Harde blokkade —
            # overslaan mét reden (niet stil).
            from app.collections.compliance import check_dagenbrief_gate

            gate_reason = await check_dagenbrief_gate(
                db, tenant_id, case, step.name, case_number=case.case_number
            )
            if gate_reason is not None:
                skipped += 1
                errors.append(gate_reason)
                continue

            try:
                # Build context once — reused for e-mail body or DOCX archive.
                base_context = await build_base_context(db, tenant_id, case)

                # B1 — verstuurpad: incasso-stappen zijn meestal E-MAIL-sjablonen.
                # Probeer eerst de e-mailrenderer; val alleen terug op een DOCX-brief
                # (PDF-bijlage) als die sleutel géén e-mailsjabloon is (bv. dagvaarding).
                # De oude volgorde riep render_docx als eerste aan en klapte daarop voor
                # de e-mailsleutels (sommatie_drukte/faillissement_dreigbrief) → er ging
                # nooit iets de deur uit.
                inline_html = render_incasso_email(step.template_type, base_context)

                # Codex-review portie 1: als verzending is gevraagd maar er gaat
                # niets de deur uit, mag de zaak niet doorschuiven (zelfde regel
                # als B1). We houden per zaak bij of er echt iets verstuurd is.
                sent_this_case = False

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
                    generated_doc_ids.append(doc.id)
                    processed += 1

                    if send_email and case.opposing_party and case.opposing_party.email:
                        try:
                            # S211: renteoverzicht-PDF bij 14-dagenbrief/eerste
                            # sommatie voor een privé aansprakelijke wederpartij
                            # (leest het opgeslagen rechtsvorm-veld, nooit de KvK).
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
                                recipient_name=(case.opposing_party.name or ""),
                                send_as_tenant_account=True,
                            )
                            if email_log.status == "sent":
                                emails_sent += 1
                                sent_this_case = True
                            else:
                                emails_failed += 1
                                errors.append(
                                    f"{case.case_number}: e-mail mislukt — {email_log.error_message}"
                                )
                        except Exception as email_exc:
                            emails_failed += 1
                            errors.append(f"{case.case_number}: e-mail fout — {email_exc}")
                            logger.error(
                                "Batch email failed for %s: %s", case.case_number, email_exc
                            )
                else:
                    # DOCX-route (dagvaarding e.d.): brief als PDF-bijlage.
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

                    if send_email and case.opposing_party and case.opposing_party.email:
                        try:
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
                                send_as_tenant_account=True,
                            )
                            if email_log.status == "sent":
                                emails_sent += 1
                                sent_this_case = True
                            else:
                                emails_failed += 1
                                errors.append(
                                    f"{case.case_number}: e-mail mislukt — {email_log.error_message}"
                                )
                        except Exception as email_exc:
                            emails_failed += 1
                            errors.append(f"{case.case_number}: e-mail fout — {email_exc}")
                            logger.error(
                                "Batch email failed for %s: %s", case.case_number, email_exc
                            )

                # Codex-review portie 1: verzending gevraagd maar niets verstuurd
                # (mislukt of geen e-mailadres) → document blijft staan mét fout,
                # maar de zaak schuift NIET door en taken worden niet afgerond.
                if send_email and not sent_this_case:
                    if not (case.opposing_party and case.opposing_party.email):
                        errors.append(
                            f"{case.case_number}: geen e-mailadres wederpartij — "
                            "niet verstuurd, zaak niet doorgeschoven"
                        )
                    continue

                # S205: leg de daadwerkelijke verzending vast op de HUIDIGE stap
                # (vóór de auto-advance de stap verlaat). Zo telt een via de batch
                # verstuurde 14-dagenbrief mee als 'aantoonbaar verstuurd' voor de
                # gate (email_sent), i.p.v. alleen stap-binnenkomst. Ontbrak hier.
                if sent_this_case:
                    await mark_current_step_communication_sent(
                        db, tenant_id, case, document_id=doc.id
                    )

                # Auto-complete matching pipeline tasks for this step
                completed_count = await _auto_complete_tasks(
                    db, tenant_id, case.id, case.incasso_step_id
                )
                tasks_auto_completed += completed_count

                # S143: Skip eventuele open review_ai_draft tasks voor deze step.
                # Batch verstuurt via template (geen AI-draft), dus de review-
                # tasks zijn moot. Zonder dit blokkeren ze _try_auto_advance.
                if case.incasso_step_id:
                    await _skip_review_drafts_for_step(
                        db, tenant_id, case.id, case.incasso_step_id
                    )

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
        # Interest is always computed on the fly (never persisted), so the only
        # thing this action can meaningfully do is resync the cached financial
        # totals. The old version recomputed total_principal to the value it
        # already held (a no-op) — leaving total_paid stale — yet still reported
        # each case as 'processed' (AUDIT-MEDIUM). Refresh principal+paid from the
        # live claims/payments so the reported count reflects real work.
        from app.collections.service import _refresh_case_financials

        for case in cases:
            try:
                await _refresh_case_financials(db, tenant_id, case.id)
                processed += 1
            except Exception as exc:
                logger.error(
                    "Financial refresh failed for %s: %s",
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

        # S202 M4: de body wordt als HTML verstuurd — autoescape zorgt dat
        # data-afkomstige velden (omschrijving, namen) geen rauwe markup de deur
        # uit laten gaan; letterlijke sjabloontekst van het kantoor zelf blijft
        # ongemoeid. Het onderwerp is platte tekst (mailheader) → géén escaping,
        # anders wordt een legitieme '&' daar zichtbaar '&amp;'.
        env_subject = Environment(autoescape=False)
        env_body = Environment(autoescape=True)

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

        subject = env_subject.from_string(step.email_subject_template).render(context)
        body_text = env_body.from_string(step.email_body_template).render(context)
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
    terminal_step_ids = {s.id for s in steps if s.is_terminal}
    result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.case_type == "incasso",
            Case.is_active.is_(True),
            Case.status.notin_(["betaald", "afgesloten"]),
        )
    )
    all_cases = list(result.scalars().all())
    # AUDIT-H11 / B3 (S198): sluit zaken op een terminale stap uit — gesloten zaken
    # hebben geen volgende stap. De status-filter hierboven vangt ze sinds S198 al af
    # (move_case_to_step zet de status mee); dit blijft als vangnet.
    all_cases = [c for c in all_cases if c.incasso_step_id not in terminal_step_ids]

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
