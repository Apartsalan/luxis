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
            "contact_person": debtor_contact.name if debtor_contact else "",
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
        "av_text": None,
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
) -> "AIDraft":
    """Genereer AI-draft voor (case, target_step) en sla op in ai_drafts.

    Gebruikt `incasso_email_prompts.build_full_prompt` met de bron-templates
    uit IncassoPipelineStep.email_subject_template + email_body_template.

    Bij `create_workflow_task=True`: maakt ook een WorkflowTask aan in `/taken`
    queue zodat Lisanne het kan reviewen.
    """
    from app.ai_agent.draft_service import DraftStatus
    from app.ai_agent.incasso_email_prompts import build_full_prompt
    from app.ai_agent.kimi_client import call_intake_ai
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

    # Bouw prompt
    system_prompt, user_prompt = build_full_prompt(
        step_name=target_step.name,
        template_subject=template_subject,
        template_body=template_body,
        template_body_html=template_body_html or None,
        **context,
    )

    logger.info(
        "Generating AI draft for case=%s step=%s (prompt %d chars)",
        case_id, target_step.name, len(user_prompt),
    )

    # Roep AI aan
    result, model_name = await call_intake_ai(system_prompt, user_prompt)

    from app.incasso.html_renderer import render_template_html

    subject = result.get("subject", "") or template_subject
    body = result.get("body", "") or template_body
    # AI returnt geen body_html — server rendert HTML uit template + dossier-context
    body_html = render_template_html(template_body_html, **context) if template_body_html else None

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
