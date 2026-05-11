"""Automation rule evaluator + draft generator voor de incasso-pipeline.

Sessie 133. Pivot: lineaire pipeline + losse automation rules (geen branching graaf).

Twee verantwoordelijkheden:
1. **Rule evaluator** — bepaalt welke dossiers vandaag een action moeten ondergaan
   (timeout, debtor_response, payment). Geen AI calls hier.
2. **Draft generator** — voor een (case, rule) pair: roept AI aan via
   `incasso_email_prompts.build_full_prompt`, slaat AIDraft op en maakt een
   WorkflowTask aan zodat Lisanne het in `/taken` ziet.

Manual trigger (endpoint) hergebruikt deze functies voor 1 dossier per keer.
Daily scheduler hergebruikt deze functies voor alle dossiers per tenant.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.incasso.models import IncassoPipelineStep, StepTransition

logger = logging.getLogger(__name__)


# ── Datatype voor rule-match ──────────────────────────────────────────────


@dataclass
class RuleMatch:
    """Resultaat van rule-evaluation: 1 match per (case, rule) pair."""

    case_id: uuid.UUID
    case_number: str
    from_step_id: uuid.UUID
    from_step_name: str
    to_step_id: uuid.UUID
    to_step_name: str
    rule_id: uuid.UUID
    trigger_type: str
    action: str
    reason: str  # menselijke uitleg, voor logging + UI


# ── Rule evaluator ─────────────────────────────────────────────────────────


async def evaluate_timeout_rules(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    today: date | None = None,
) -> list[RuleMatch]:
    """Evalueer timeout-rules voor alle actieve dossiers in een tenant.

    Een match treedt op als:
    - case.incasso_step_id is gezet
    - er een StepTransition bestaat met from_step_id = case.incasso_step_id,
      trigger_type='timeout', is_active=true, is_default=true
    - (today - case.step_entered_at).days >= condition['days']

    Returnt lijst van RuleMatch objecten — uitvoeren is verantwoordelijkheid van
    de caller (draft-generator + workflow-task creator).
    """
    import json as _json

    today = today or datetime.now(UTC).date()

    # Pak alle actieve dossiers met een incasso_step
    cases_result = await db.execute(
        select(Case).where(
            Case.tenant_id == tenant_id,
            Case.is_active.is_(True),
            Case.incasso_step_id.is_not(None),
            Case.step_entered_at.is_not(None),
        )
    )
    cases = list(cases_result.scalars().all())
    if not cases:
        return []

    step_ids_in_use = {c.incasso_step_id for c in cases if c.incasso_step_id}

    # Pak alle actieve timeout-rules waarvan from_step in gebruik
    rules_result = await db.execute(
        select(StepTransition).where(
            StepTransition.tenant_id == tenant_id,
            StepTransition.is_active.is_(True),
            StepTransition.trigger_type == "timeout",
            StepTransition.is_default.is_(True),
            StepTransition.from_step_id.in_(step_ids_in_use),
        )
    )
    rules = list(rules_result.scalars().all())

    rules_by_from_step: dict[uuid.UUID, StepTransition] = {}
    for r in rules:
        # Eerste rule per from_step (er zou maar 1 default timeout-rule per stap moeten zijn)
        if r.from_step_id not in rules_by_from_step:
            rules_by_from_step[r.from_step_id] = r

    matches: list[RuleMatch] = []
    for case in cases:
        rule = rules_by_from_step.get(case.incasso_step_id)
        if not rule:
            continue
        cond = _json.loads(rule.condition) if rule.condition else {}
        wait_days = int(cond.get("days", 0))
        if wait_days <= 0:
            continue
        days_since = (today - case.step_entered_at.date()).days
        if days_since < wait_days:
            continue

        matches.append(RuleMatch(
            case_id=case.id,
            case_number=case.case_number,
            from_step_id=rule.from_step_id,
            from_step_name=rule.from_step.name if rule.from_step else "?",
            to_step_id=rule.to_step_id,
            to_step_name=rule.to_step.name if rule.to_step else "?",
            rule_id=rule.id,
            trigger_type="timeout",
            action=rule.action,
            reason=f"Geen reactie na {wait_days} dagen ({days_since} dagen verstreken)",
        ))

    logger.info(
        "evaluate_timeout_rules: tenant=%s cases=%d rules=%d matches=%d",
        tenant_id, len(cases), len(rules), len(matches),
    )
    return matches


# ── Helpers voor draft-generator ──────────────────────────────────────────


def _extract_pdf_text(path: str, max_chars: int = 8000) -> str | None:
    """Extract text from PDF at given path. Returns None bij fouten of leeg."""
    try:
        import pymupdf
    except ImportError:
        logger.warning("pymupdf niet beschikbaar — AV-text extractie uitgeschakeld")
        return None
    try:
        doc = pymupdf.open(path)
    except Exception as e:
        logger.warning(f"AV PDF kan niet geopend worden ({path}): {e}")
        return None
    try:
        parts: list[str] = []
        total = 0
        for page in doc:
            text = page.get_text("text") or ""
            parts.append(text)
            total += len(text)
            if total >= max_chars:
                break
        result = "\n".join(parts).strip()
        return result[:max_chars] if result else None
    finally:
        doc.close()


async def gather_case_context(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> dict[str, Any]:
    """Verzamel alle bronnen die de AI nodig heeft voor draft-generatie.

    Returnt dict met sleutels matchend op `incasso_email_prompts.build_user_prompt`:
    case_data, debtor_data, client_data, invoices, amounts, av_text,
    incoming_defense, prior_correspondence.

    Lazy-imports modellen om circulaire dependencies te vermijden bij module-load.
    """
    from app.collections.models import Claim, Payment

    case = (await db.execute(
        select(Case).where(Case.tenant_id == tenant_id, Case.id == case_id)
    )).scalar_one()

    # Case heeft client + opposing_party als directe relations (selectin loaded)
    client_contact = case.client
    debtor_contact = case.opposing_party

    claims = (await db.execute(
        select(Claim).where(Claim.tenant_id == tenant_id, Claim.case_id == case_id)
    )).scalars().all()
    payments = (await db.execute(
        select(Payment).where(Payment.tenant_id == tenant_id, Payment.case_id == case_id)
    )).scalars().all()

    # Bedragen-tabel — pragmatisch: Claim heeft alleen principal_amount,
    # rente + BIK worden elders berekend (interest.py + wik.py). Voor MVP
    # gebruiken we case.total_principal/total_paid (cached) en laten rente/BIK/BTW
    # op 0 staan zodat Lisanne ze handmatig in de compose-dialog kan zetten.
    hoofdsom = sum(
        (c.principal_amount or Decimal("0.00") for c in claims), Decimal("0.00")
    ) or (case.total_principal or Decimal("0.00"))
    rente = Decimal("0.00")
    bik = Decimal("0.00")
    btw = Decimal("0.00")
    total_paid = sum(
        (p.amount or Decimal("0.00") for p in payments), Decimal("0.00")
    ) or (case.total_paid or Decimal("0.00"))
    totaal = (hoofdsom + rente + bik + btw).quantize(Decimal("0.01"))
    te_voldoen = (totaal - total_paid).quantize(Decimal("0.01"))

    # Algemene Voorwaarden van cliënt — pad voor Sonnet native PDF input,
    # tekst-extract als fallback voor Gemini/Haiku-pad.
    av_text: str | None = None
    av_pdf_path: str | None = None
    if client_contact and client_contact.terms_file_path:
        av_pdf_path = client_contact.terms_file_path
        av_text = _extract_pdf_text(client_contact.terms_file_path, max_chars=50000)
        if av_text:
            logger.info(
                "Case %s: AV geladen voor %s (PDF=%s, %d chars text-fallback)",
                case.case_number, client_contact.name, av_pdf_path, len(av_text),
            )

    return {
        "case_data": {
            "case_number": case.case_number,
            "reference": getattr(case, "reference", None) or case.case_number,
            "debtor_type": getattr(case, "debtor_type", None) or "b2b",
            "opened_at": case.date_opened.isoformat() if case.date_opened else "",
        },
        "client_data": {
            "name": client_contact.name if client_contact else "?",
            "address": (client_contact.visit_address or client_contact.postal_address or "") if client_contact else "",
            "coc_number": client_contact.kvk_number if client_contact else None,
        },
        "debtor_data": {
            "name": debtor_contact.name if debtor_contact else "?",
            "address": (debtor_contact.visit_address or debtor_contact.postal_address or "") if debtor_contact else "",
            # contact_person ALLEEN bij natuurlijk persoon-debiteur; bij bedrijf
            # zonder gekoppelde persoon → leeg, AI mag dan geen naam in aanhef
            # plaatsen (geen "Geachte heer/mevrouw [BedrijfBV]," fout).
            "contact_person": (
                (debtor_contact.last_name or debtor_contact.name or "")
                if debtor_contact and getattr(debtor_contact, "contact_type", "") == "person"
                else ""
            ),
            "contact_type": (
                getattr(debtor_contact, "contact_type", "company")
                if debtor_contact else "company"
            ),
            "email": debtor_contact.email if debtor_contact else "",
        },
        "invoices": [
            {
                "number": c.invoice_number or "?",
                "date": c.invoice_date.isoformat() if c.invoice_date else "",
                "due_date": c.default_date.isoformat() if c.default_date else "",
                "amount": str(c.principal_amount or Decimal("0.00")),
            }
            for c in claims
        ],
        "amounts": {
            "hoofdsom": hoofdsom,
            "rente": rente,
            "hoofdsom_plus_rente": (hoofdsom + rente).quantize(Decimal("0.01")),
            "incassokosten": bik,
            "btw": btw,
            "totaal": totaal,
            "voldaan_bij_klant": Decimal("0.00"),
            "door_ons_ontvangen": total_paid,
            "te_voldoen": te_voldoen,
        },
        "av_text": av_text,
        "av_pdf_path": av_pdf_path,
        "incoming_defense": None,
        "prior_correspondence": [],
    }


# ── Daily rate limit ──────────────────────────────────────────────────────


async def count_drafts_today(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> int:
    """Telt AI-drafts gegenereerd vandaag voor deze tenant (rate-limit guard)."""
    from app.ai_agent.models import AIDraft

    today_start = datetime.combine(datetime.now(UTC).date(), datetime.min.time(), tzinfo=UTC)
    result = await db.execute(
        select(AIDraft).where(
            AIDraft.tenant_id == tenant_id,
            AIDraft.generated_at >= today_start,
        )
    )
    return len(list(result.scalars().all()))


# ── Draft generator ───────────────────────────────────────────────────────


# Maximaal aantal AI-drafts dat de daily scheduler per tenant per dag genereert.
# Manual trigger telt NIET mee — die werkt altijd. Sanity-bescherming tegen
# runaway draft-generatie bij bugs in rule-evaluator.
DAILY_DRAFT_RATE_LIMIT = 50


async def generate_draft_for_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    target_step_id: uuid.UUID,
    *,
    rule_match: RuleMatch | None = None,
    create_workflow_task: bool = True,
    incoming_defense: str | None = None,
) -> "AIDraft":
    """Genereer AI-draft voor (case, target_step) en sla op in ai_drafts.

    Gebruikt `incasso_email_prompts.build_full_prompt` met de bron-templates
    uit IncassoPipelineStep.email_subject_template + email_body_template.

    Bij `create_workflow_task=True`: maakt ook een WorkflowTask aan in `/taken`
    queue zodat Lisanne het kan reviewen.
    """
    from app.ai_agent.draft_service import DraftStatus
    from app.ai_agent.incasso_email_prompts import build_full_prompt
    from app.ai_agent.kimi_client import call_draft_ai
    from app.ai_agent.models import AIDraft

    # Pak target step (= stap waarvoor we draft genereren)
    target_step = (await db.execute(
        select(IncassoPipelineStep).where(
            IncassoPipelineStep.tenant_id == tenant_id,
            IncassoPipelineStep.id == target_step_id,
        )
    )).scalar_one()

    template_subject = target_step.email_subject_template or ""
    template_body = target_step.email_body_template or ""
    template_body_html = target_step.email_body_template_html or ""
    if not template_body:
        logger.warning(
            "Stap '%s' heeft geen email-sjabloon — draft-generatie overgeslagen",
            target_step.name,
        )
        raise ValueError(
            f"Stap '{target_step.name}' heeft geen email-sjabloon geconfigureerd"
        )

    # Verzamel dossier-context
    context = await gather_case_context(db, tenant_id, case_id)
    if incoming_defense:
        context["incoming_defense"] = incoming_defense
    elif target_step.name == "Verweer beantwoorden":
        # Manual trigger op verweer-stap zonder explicit incoming_defense:
        # haal automatisch laatste inbound email op uit case-correspondentie.
        # AI kan anders niets weerleggen want hij weet niet wat debiteur stelde.
        from app.email.synced_email_models import SyncedEmail

        last_inbound = (await db.execute(
            select(SyncedEmail).where(
                SyncedEmail.tenant_id == tenant_id,
                SyncedEmail.case_id == case_id,
                SyncedEmail.direction == "inbound",
            ).order_by(SyncedEmail.email_date.desc()).limit(1)
        )).scalar_one_or_none()
        if last_inbound:
            context["incoming_defense"] = (
                last_inbound.body_text or last_inbound.snippet or ""
            )[:8000]
            logger.info(
                "Case %s: incoming_defense auto-geladen uit SyncedEmail %s (%d chars)",
                case_id, last_inbound.id, len(context["incoming_defense"]),
            )
        else:
            logger.warning(
                "Case %s: Verweer beantwoorden zonder inbound email — "
                "AI kan niet weerleggen zonder verweer-tekst",
                case_id,
            )

    # AV-PDF pad alleen bij Verweer beantwoorden — daar moet AI citeren uit AV.
    # Andere stappen (sommaties zonder verweer) hebben AV niet nodig.
    av_pdf_path = context.pop("av_pdf_path", None)
    use_pdf_route = (
        av_pdf_path is not None
        and target_step.name == "Verweer beantwoorden"
    )

    # Bouw prompt
    system_prompt, user_prompt = build_full_prompt(
        step_name=target_step.name,
        template_subject=template_subject,
        template_body=template_body,
        template_body_html=template_body_html or None,
        **context,
    )

    logger.info(
        "Generating AI draft for case=%s step=%s (prompt %d chars, pdf_route=%s)",
        case_id, target_step.name, len(user_prompt), use_pdf_route,
    )

    # Roep AI aan — Sonnet primary, met PDF bij verweer-stap
    result, model_name = await call_draft_ai(
        system_prompt,
        user_prompt,
        av_pdf_path=av_pdf_path if use_pdf_route else None,
    )

    from app.incasso.html_renderer import render_template_html, render_subject

    # Subject altijd server-side renderen — AI maakt soms fouten met de
    # `/ kenmerk / dossiernummer` structuur (zet bv. contactnaam in plaats
    # van dossiernummer in 2e slot).
    case_data = context.get("case_data", {})
    subject = render_subject(
        template_subject,
        case_number=str(case_data.get("case_number") or ""),
        kenmerk=str(case_data.get("reference") or case_data.get("case_number") or ""),
    )
    body = result.get("body", "") or template_body
    # AI returnt geen body_html — server rendert HTML uit template + dossier-context.
    # ai_body wordt meegegeven zodat XXX-placeholder (Verweer beantwoorden) gevuld
    # kan worden met de AI-gegenereerde weerlegging.
    body_html = (
        render_template_html(template_body_html, ai_body=body, **context)
        if template_body_html
        else None
    )

    # Sla AIDraft op
    draft = AIDraft(
        tenant_id=tenant_id,
        case_id=case_id,
        subject=subject,
        body=body,
        body_html=body_html,
        tone="formeel",
        sources={
            "step_name": target_step.name,
            "step_id": str(target_step.id),
            "rule_id": str(rule_match.rule_id) if rule_match else None,
            "trigger_type": rule_match.trigger_type if rule_match else "manual",
            "reason": rule_match.reason if rule_match else "Handmatig getriggerd",
        },
        status=DraftStatus.GENERATED,
        model_used=model_name,
        instruction=f"Auto-draft voor stap '{target_step.name}'",
    )
    db.add(draft)
    await db.flush()
    await db.refresh(draft)
    logger.info(
        "AIDraft %s opgeslagen (model=%s, %d chars body)",
        draft.id, model_name, len(body),
    )

    # Maak WorkflowTask aan voor Taken queue
    if create_workflow_task:
        await _create_review_task(
            db, tenant_id=tenant_id, case_id=case_id,
            draft_id=draft.id, step_name=target_step.name,
            reason=rule_match.reason if rule_match else "Handmatig getriggerd",
        )

    return draft


# ── Email-event trigger (sessie 134) ───────────────────────────────────────


# Stappen waarop binnenkomende verweer-email een pipeline-switch triggert.
# Andere stappen ("Verweer beantwoorden", "Opvragen stukken", etc.) zijn al
# verweer-flow — niet opnieuw triggeren.
_HOOFDPAD_STEPS_FOR_DEFENSE = {
    "Eerste sommatie",
    "Tweede sommatie",
    "Derde sommatie",
    "Sommatie laatste mogelijkheid",
    "Verzoekschrift faillissement",
}

# Categorieen die als verweer worden gezien — alleen deze triggeren switch.
_DEFENSE_CATEGORIES = {"juridisch_verweer", "betwisting"}


async def trigger_defense_response_for_email(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    synced_email_id: uuid.UUID,
    classification_category: str,
) -> "AIDraft | None":
    """Hook na email-classificatie: verweer detecteerd → switch case + draft.

    Wordt aangeroepen NA `classify_email`. Als de email is geclassificeerd als
    verweer EN het dossier zit in een hoofdpad-stap, dan:
      1. Set case.incasso_step_id naar 'Verweer beantwoorden'
      2. Genereer AI draft op basis van TWEEDE SOMMATIE INDIEN WEL VERWEER met
         incoming_defense=email body + defense_library voorbeelden
      3. Maak WorkflowTask in /taken queue zodat Lisanne het ziet

    Returns de AIDraft of None als geen actie nodig.
    """
    from app.ai_agent.models import AIDraft  # noqa: F401
    from app.email.synced_email_models import SyncedEmail

    if classification_category not in _DEFENSE_CATEGORIES:
        return None

    synced = (await db.execute(
        select(SyncedEmail).where(
            SyncedEmail.id == synced_email_id,
            SyncedEmail.tenant_id == tenant_id,
        )
    )).scalar_one_or_none()
    if not synced or not synced.case_id:
        return None
    if synced.direction != "inbound":
        return None

    case = (await db.execute(
        select(Case).where(Case.id == synced.case_id, Case.tenant_id == tenant_id)
    )).scalar_one_or_none()
    if not case or not case.incasso_step_id:
        return None

    current_step = (await db.execute(
        select(IncassoPipelineStep).where(
            IncassoPipelineStep.id == case.incasso_step_id,
            IncassoPipelineStep.tenant_id == tenant_id,
        )
    )).scalar_one_or_none()
    # Drie scenario's:
    #   A. Hoofdpad-stap → switch naar Verweer beantwoorden + draft
    #   B. Al in Verweer beantwoorden → nieuwe draft (re-trigger op vervolgreactie)
    #   C. Andere zijpad-stap → niets doen
    if not current_step:
        return None

    is_hoofdpad = current_step.name in _HOOFDPAD_STEPS_FOR_DEFENSE
    is_already_verweer = current_step.name == "Verweer beantwoorden"
    if not (is_hoofdpad or is_already_verweer):
        logger.info(
            "Email %s op case %s: stap '%s' is geen hoofdpad/verweer — geen actie",
            synced_email_id, case.case_number, current_step.name,
        )
        return None

    verweer_step = (await db.execute(
        select(IncassoPipelineStep).where(
            IncassoPipelineStep.tenant_id == tenant_id,
            IncassoPipelineStep.name == "Verweer beantwoorden",
            IncassoPipelineStep.is_active.is_(True),
        )
    )).scalar_one_or_none()
    if not verweer_step:
        logger.warning(
            "Tenant %s mist 'Verweer beantwoorden' stap — kan niet switchen",
            tenant_id,
        )
        return None

    if is_hoofdpad:
        # Switch case naar verweer (alleen vanuit hoofdpad)
        case.incasso_step_id = verweer_step.id
        case.incasso_step_entered_at = datetime.now(UTC)
        await db.flush()
    else:
        logger.info(
            "Case %s al in Verweer beantwoorden — vervolgreactie %s, "
            "regenereer draft zonder stap-switch",
            case.case_number, synced_email_id,
        )
    if is_hoofdpad:
        logger.info(
            "Case %s: switch %s → Verweer beantwoorden (verweer-email %s)",
            case.case_number, current_step.name, synced_email_id,
        )

    # Genereer draft met incoming verweer-tekst
    defense_text = (synced.body_text or synced.snippet or "")[:8000]
    draft = await generate_draft_for_step(
        db,
        tenant_id=tenant_id,
        case_id=case.id,
        target_step_id=verweer_step.id,
        rule_match=None,
        create_workflow_task=True,
        incoming_defense=defense_text,
    )
    return draft


async def _create_review_task(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    draft_id: uuid.UUID,
    step_name: str,
    reason: str,
) -> None:
    """Maak WorkflowTask aan zodat draft in /taken queue verschijnt."""
    from app.workflow.models import WorkflowTask

    task = WorkflowTask(
        tenant_id=tenant_id,
        case_id=case_id,
        task_type="review_ai_draft",
        title=f"Review concept-email: {step_name}",
        description=f"AI heeft een concept-email klaargezet ({reason}). Bekijk en verstuur.",
        due_date=datetime.now(UTC).date(),
        status="pending",
        action_config={"draft_id": str(draft_id), "step_name": step_name},
    )
    db.add(task)
    await db.flush()
    logger.info("WorkflowTask aangemaakt voor draft %s (case %s)", draft_id, case_id)
