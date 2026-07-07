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
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.incasso.models import IncassoPipelineStep, StepTransition

if TYPE_CHECKING:
    from app.ai_agent.models import AIDraft

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

    # Pak alle actieve timeout-rules waarvan from_step in gebruik.
    # Deterministische volgorde (created_at, id): zonder ORDER BY was "welke
    # regel wint per from_step" afhankelijk van query-uitvoering — een bron van
    # non-deterministisch gedrag als er per ongeluk twee default-regels bestaan.
    rules_result = await db.execute(
        select(StepTransition)
        .where(
            StepTransition.tenant_id == tenant_id,
            StepTransition.is_active.is_(True),
            StepTransition.trigger_type == "timeout",
            StepTransition.is_default.is_(True),
            StepTransition.from_step_id.in_(step_ids_in_use),
        )
        .order_by(StepTransition.created_at, StepTransition.id)
    )
    rules = list(rules_result.scalars().all())

    # Waarschuw bij de misconfiguratie zelf: meer dan één default timeout-regel
    # vanaf dezelfde stap. Hoort er niet te zijn; surface het i.p.v. stil de
    # "eerste" te pakken.
    rules_per_step: dict[uuid.UUID, int] = {}
    for r in rules:
        rules_per_step[r.from_step_id] = rules_per_step.get(r.from_step_id, 0) + 1

    rules_by_from_step: dict[uuid.UUID, StepTransition] = {}
    for r in rules:
        # Sla regels naar een inactieve doel-stap over: de draft-generator kan
        # geen concept bouwen voor een stap zonder sjabloon → ValueError → zaak
        # blijft stil hangen. Zo wint altijd de regel naar een actieve stap.
        # Waarschuw altijd bij het overslaan (ook als het de énige regel is),
        # anders wordt de poortwachter zelf stil: een verkeerd geconfigureerde
        # stap zou dan geen match én geen signaal geven.
        if r.to_step is None or not r.to_step.is_active:
            logger.warning(
                "evaluate_timeout_rules: timeout-regel %s (stap %s) overgeslagen — "
                "doel-stap is inactief. Wijs de regel naar een actieve stap of "
                "deactiveer 'm.",
                r.id, r.from_step_id,
            )
            continue
        if r.from_step_id not in rules_by_from_step:
            rules_by_from_step[r.from_step_id] = r
    for from_step_id, count in rules_per_step.items():
        if count > 1:
            chosen = rules_by_from_step.get(from_step_id)
            logger.warning(
                "evaluate_timeout_rules: %d actieve default timeout-regels vanaf "
                "stap %s — deterministisch gekozen: regel %s. Ruim de dubbele "
                "regel(s) op.",
                count, from_step_id,
                chosen.id if chosen else "geen (alle doel-stappen inactief)",
            )

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


def _dedupe_subject_slots(body: str) -> str:
    """Vervang dubbele slot-vermelding in Betreft-regel: '/ X / X' → '/ X'.

    AI volgt niet altijd prompt-instructie dat kenmerk == dossiernummer
    slechts één slot moet zijn. Server-side regex als vangnet — patroon
    '/ <token> / <token>' waar beide tokens identiek zijn wordt vervangen
    door '/ <token>'. Werkt alleen op identieke tokens, dus bij ECHT
    verschillend kenmerk + dossiernummer blijft '/ REF-123 / 2026-00049'
    onaangetast.
    """
    import re
    if not body:
        return body
    pattern = re.compile(r"/\s*([^\s/][^\s/]*)\s*/\s*\1(?!\S)")
    return pattern.sub(r"/ \1", body)


def _ensure_iban_kenmerk(body: str, case_number: str) -> str:
    """Vul leeg kenmerk in IBAN-betalingsinstructie met dossiernummer.

    AI laat soms kenmerk leeg na 'onder vermelding van het kenmerk'
    (resultaat van prompt-instructie 'kenmerk = (geen)'). Voor betaling
    is dossiernummer als kenmerk verplicht — anders kan debiteur niet
    correct overmaken. Server-side vangnet vervangt lege vermeldingen.
    """
    import re
    if not body or not case_number:
        return body
    # Patroon: "kenmerk" gevolgd door whitespace, dan punt/komma/einde-regel
    # zonder iets ertussen → invoegen case_number.
    body = re.sub(
        r"(onder vermelding van het kenmerk)\s*([.,\n])",
        rf"\1 {case_number}\2",
        body,
    )
    return body


def _amount_variants(amount: Decimal) -> set[str]:
    """Alle gangbare schrijfwijzen van een bedrag: NL (1.234,56 / 1234,56),
    EN (1,234.56 / 1234.56) en bij hele euro's ook '500,-'."""
    q = amount.quantize(Decimal("0.01"))
    en_thousands = f"{q:,.2f}"  # 1,234.56
    nl_thousands = (
        en_thousands.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    )  # 1.234,56
    plain_en = f"{q}"  # 1234.56
    plain_nl = plain_en.replace(".", ",")  # 1234,56
    variants = {en_thousands, nl_thousands, plain_en, plain_nl}
    if q == q.to_integral_value():
        whole_nl_thousands = f"{int(q):,}".replace(",", ".")  # 1.234
        variants |= {f"{int(q)},-", f"{whole_nl_thousands},-"}
    return variants


def _draft_fidelity_issues(
    body: str,
    *,
    step_name: str,
    template_body: str,
    case_number: str,
    amounts: dict[str, Decimal],
) -> list[str]:
    """Getrouwheids-poort (S182, plan wet-en-regelgeving §1 actie B): de dragende
    dossier-elementen moeten letterlijk in het concept staan.

    Gecontroleerd: dossiernummer + (als het sjabloon een bedragen-tabel heeft,
    herkenbaar aan '€') hoofdsom, rentebedrag en te-voldoen-bedrag, elk alleen
    als > 0. Bewuste plan-afwijking: GEEN rentepercentage-check — de sjablonen
    vermelden rente als bedrag met een vaste uitleg-alinea zonder percentage;
    een percentage afdwingen zou elke contractuele-rente-brief vals flaggen én
    de AI van het sjabloon wegduwen (regel 1: sjabloon is leidend). Het
    rentebedrag controleren is sterker: dan klopt de daadwerkelijke rente-eis.
    Bij de verweer-stap hoort ook de 'XXX'-plaatshouder vervangen te zijn (de
    oude check keek naar de dict-sleutels i.p.v. de tekst en werkte dus nooit).
    """
    if not body:
        return ["lege body"]
    issues: list[str] = []
    if case_number and case_number not in body:
        issues.append(f"dossiernummer {case_number}")
    if "€" in (template_body or ""):
        for label, value in (
            ("hoofdsom", amounts.get("hoofdsom")),
            ("rente", amounts.get("rente")),
            ("te voldoen", amounts.get("te_voldoen")),
        ):
            if value is None or value <= 0:
                continue
            if not any(v in body for v in _amount_variants(value)):
                issues.append(f"{label} € {value}")
    if step_name == "Verweer beantwoorden" and "XXX" in body:
        issues.append("'XXX'-plaatshouder niet vervangen")
    return issues


def _capitalize_name(name: str) -> str:
    """Capitalize eerste letter als naam helemaal lowercase ingevoerd is.

    'peterson' → 'Peterson'. 'de Vries' (al gemixt) → 'De Vries'.
    'Peterson' (al goed) → onveranderd.
    """
    if not name:
        return name
    if name == name.lower():
        return name[:1].upper() + name[1:]
    return name


def _last_name_from_full(full: str) -> str:
    """Pak alleen het laatste woord als achternaam.

    Sommige contacten hebben `last_name` leeg en alles in `name` staan
    ('Arsalan Seidony'). De aanhef moet 'Geachte heer/mevrouw Seidony'
    worden, niet 'Geachte heer/mevrouw Arsalan Seidony'.
    """
    if not full:
        return ""
    parts = full.strip().split()
    return parts[-1] if parts else full


async def _resolve_contact_person(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact: Any,
) -> tuple[str, str]:
    """Bepaal contactpersoon-achternaam + aanhef voor in mail-aanhef.

    Returnt tuple (achternaam, salutation):
    - Persoon-debiteur: eigen achternaam (of volledige naam) + eigen salutation.
    - Bedrijf-debiteur: eerste actieve ContactLink.person achternaam +
      salutation van die persoon. Voorkeur rol "Contactpersoon".
    - Anders (onbekend / geen link): ("", "unknown") → AI gebruikt generieke
      aanhef.

    Salutation is altijd één van: 'mr', 'mrs', 'unknown' (default 'unknown').
    """
    if not contact:
        return "", "unknown"
    contact_type = getattr(contact, "contact_type", "")
    if contact_type == "person":
        last = contact.last_name or _last_name_from_full(contact.name or "")
        salutation = getattr(contact, "salutation", None) or "unknown"
        return _capitalize_name(last), salutation
    if contact_type == "company":
        from app.relations.models import Contact, ContactLink

        links = (await db.execute(
            select(ContactLink).where(
                ContactLink.tenant_id == tenant_id,
                ContactLink.company_id == contact.id,
                ContactLink.is_active.is_(True),
            )
        )).scalars().all()
        if not links:
            return "", "unknown"
        preferred = next(
            (
                link
                for link in links
                if (link.role_at_company or "").lower() == "contactpersoon"
            ),
            links[0],
        )
        person = (await db.execute(
            select(Contact).where(
                Contact.tenant_id == tenant_id,
                Contact.id == preferred.person_id,
            )
        )).scalar_one_or_none()
        if not person:
            return "", "unknown"
        last = person.last_name or _last_name_from_full(person.name or "")
        salutation = getattr(person, "salutation", None) or "unknown"
        return _capitalize_name(last), salutation
    return "", "unknown"


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
    from app.collections.service import get_financial_summary

    case = (await db.execute(
        select(Case).where(Case.tenant_id == tenant_id, Case.id == case_id)
    )).scalar_one()

    # Case heeft client + opposing_party als directe relations (selectin loaded)
    client_contact = case.client
    debtor_contact = case.opposing_party

    # Contactpersoon + aanhef voor aanhef — bij bedrijf via ContactLink async query
    contact_person_name, debtor_salutation = await _resolve_contact_person(
        db, tenant_id, debtor_contact
    )

    claims = (await db.execute(
        select(Claim).where(Claim.tenant_id == tenant_id, Claim.case_id == case_id)
    )).scalars().all()

    # DF138-06: bedragen via get_financial_summary (rente + BIK + BTW correct,
    # zelfde bron als de UI in dossier-detail). Eerder stonden rente/BIK/BTW
    # hardcoded op 0 als MVP-schortje — gevolg: mail aan wederpartij toonde
    # alleen hoofdsom en miste vervallen rente en incassokosten.
    include_btw_on_bik = (
        not client_contact.is_btw_plichtig if client_contact is not None else False
    )
    try:
        summary = await get_financial_summary(
            db,
            tenant_id,
            case_id,
            case.interest_type,
            case.contractual_rate,
            case.contractual_compound,
            bik_override=case.bik_override,
            bik_override_percentage=case.bik_override_percentage,
            include_btw_on_bik=include_btw_on_bik,
        )
        hoofdsom = summary["total_principal"]
        rente = summary["total_interest"]
        bik = summary["bik_amount"]
        btw = summary["bik_btw"]
        total_paid = summary["total_paid"]
        totaal = summary["grand_total"].quantize(Decimal("0.01"))
        te_voldoen = summary["total_outstanding"].quantize(Decimal("0.01"))
    except Exception:
        # Fail-safe: bij berekeningsfout vallen we terug op hoofdsom-only zodat
        # draft-generatie niet volledig faalt. Wordt gelogd voor opvolg.
        logger.exception(
            "Case %s: get_financial_summary mislukt — fallback naar hoofdsom-only",
            case.case_number,
        )
        payments = (await db.execute(
            select(Payment).where(Payment.tenant_id == tenant_id, Payment.case_id == case_id)
        )).scalars().all()
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

    # Algemene Voorwaarden van cliënt — geversioneerd (S140). Sinds S173 via de gedeelde
    # resolver (app.ai_agent.knowledge_context) zodat álle AI-conceptpaden dezelfde AV
    # zien; gedrag hier identiek aan voorheen (zelfde selectie, zelfde 50k-extractie).
    from app.ai_agent.knowledge_context import resolve_case_terms

    target_date: date | None = None
    if claims:
        invoice_dates = [c.invoice_date for c in claims if c.invoice_date is not None]
        if invoice_dates:
            target_date = min(invoice_dates)
    av_text, av_pdf_path = await resolve_case_terms(
        db, tenant_id, case, target_date=target_date, max_chars=50000
    )

    # DF138-05: Reference (kenmerk) NIET gebruiken in mail aan wederpartij.
    # case.reference is de KLANT-referentie en hoort alleen in communicatie met
    # de cliënt (bv. factuur naar cliënt). Pipeline-mails gaan naar debiteur,
    # daar gebruiken we uitsluitend ons eigen dossiernummer als kenmerk.
    reference_value = ""

    def _fmt_nl_date(d: date | None) -> str:
        return d.strftime("%d-%m-%Y") if d else ""

    # Goedgekeurde extra standaardantwoorden — alleen relevant bij de verweer-stap. We
    # bepalen hier enkel de categorie; de tekst wordt in generate_draft_for_step opgehaald
    # ná de stap-check, zodat use_count niet oploopt bij stappen die de voorbeelden negeren.
    # S174: gedeelde helper i.p.v. een eigen `created_at`-query (dezelfde bug die de S173-
    # review in het compose-pad fixte: created_at is onbetrouwbaar na de BaseNet-import).
    # Ook het verweer-type erbij (V4) → gerichte voorrang bij de geleerde voorbeelden.
    from app.ai_agent.knowledge_context import last_inbound_defense

    last_cls_category, last_cls_defense_type = await last_inbound_defense(
        db, tenant_id, case_id
    )

    return {
        "case_data": {
            "case_number": case.case_number,
            "reference": reference_value,
            "debtor_type": getattr(case, "debtor_type", None) or "b2b",
            "opened_at": _fmt_nl_date(case.date_opened),
            # Grondslag-signaal voor de AI (abonnement / uren / afwikkeling).
            "description": getattr(case, "description", None) or "",
        },
        "client_data": {
            "name": client_contact.name if client_contact else "?",
            "address": (client_contact.visit_address or client_contact.postal_address or "") if client_contact else "",
            "coc_number": client_contact.kvk_number if client_contact else None,
        },
        "debtor_data": {
            "name": debtor_contact.name if debtor_contact else "?",
            "address": (debtor_contact.visit_address or debtor_contact.postal_address or "") if debtor_contact else "",
            "contact_person": contact_person_name,
            "salutation": debtor_salutation,
            "contact_type": (
                getattr(debtor_contact, "contact_type", "company")
                if debtor_contact else "company"
            ),
            "email": debtor_contact.email if debtor_contact else "",
        },
        "invoices": [
            {
                "number": c.invoice_number or "?",
                "date": _fmt_nl_date(c.invoice_date),
                "due_date": _fmt_nl_date(c.default_date),
                "amount": str(c.principal_amount or Decimal("0.00")),
                "description": getattr(c, "description", None) or "",
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
        "learned_examples_text": "",
        "_last_cls_category": last_cls_category,
        "_last_cls_defense_type": last_cls_defense_type,
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

    # Goedgekeurde extra standaardantwoorden alleen bij de verweer-stap ophalen — dat is de
    # enige stap die ze gebruikt. Zo blijft use_count (het 'meest gebruikt'-dashboard) zuiver.
    last_cls_category = context.pop("_last_cls_category", None)
    last_cls_defense_type = context.pop("_last_cls_defense_type", None)
    if target_step.name == "Verweer beantwoorden":
        from app.ai_agent.learned_answers import build_learned_examples_text

        context["learned_examples_text"] = await build_learned_examples_text(
            db, tenant_id, last_cls_category,
            defense_type=last_cls_defense_type, max_chars=4000,
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

    # Roep AI aan — Sonnet primary, met PDF bij verweer-stap.
    result, model_name = await call_draft_ai(
        system_prompt,
        user_prompt,
        av_pdf_path=av_pdf_path if use_pdf_route else None,
    )

    from app.incasso.html_renderer import render_subject, render_template_html

    # Subject altijd server-side renderen — AI maakt soms fouten met de
    # `/ kenmerk / dossiernummer` structuur (zet bv. contactnaam in plaats
    # van dossiernummer in 2e slot).
    case_data = context.get("case_data", {})
    case_number_str = str(case_data.get("case_number") or "")
    subject = render_subject(
        template_subject,
        case_number=case_number_str,
        kenmerk=str(case_data.get("reference") or ""),
    )

    def _post_process(res: dict) -> str:
        # Server-side fixes:
        # 1. Dedupe "/ X / X" in Betreft-regel
        # 2. Vul leeg kenmerk in IBAN-betalingsinstructie met case_number
        b = res.get("body", "") or template_body
        b = _dedupe_subject_slots(b)
        return _ensure_iban_kenmerk(b, case_number_str)

    def _issues_for(b: str) -> list[str]:
        return _draft_fidelity_issues(
            b,
            step_name=target_step.name,
            template_body=template_body,
            case_number=case_number_str,
            amounts=context.get("amounts", {}),
        )

    # Getrouwheids-poort (S182): dragende elementen (dossiernummer, bedragen)
    # moeten in het concept staan; bij de verweer-stap ook geen achtergebleven
    # 'XXX'-plaatshouder (vervangt de oude XXX-lus die op de dict-sleutels
    # checkte en dus nooit vuurde). Ontbreekt iets → regenereren (max 3 AI-
    # calls totaal); blijft het fout → concept tóch aanmaken maar de
    # reviewtaak gemarkeerd. Nooit stil doorlaten, nooit stil weggooien.
    body = _post_process(result)
    fidelity_issues = _issues_for(body)
    _attempt = 1
    while fidelity_issues and _attempt < 3:
        logger.warning(
            "Case %s: concept mist dragende elementen (%s) — regenereren (poging %d)",
            case_id, "; ".join(fidelity_issues), _attempt,
        )
        result, model_name = await call_draft_ai(
            system_prompt,
            user_prompt,
            av_pdf_path=av_pdf_path if use_pdf_route else None,
        )
        body = _post_process(result)
        fidelity_issues = _issues_for(body)
        _attempt += 1
    if fidelity_issues:
        logger.error(
            "Case %s: concept wijkt na %d AI-pogingen nog af van de context (%s) "
            "— reviewtaak wordt gemarkeerd voor extra controle",
            case_id, _attempt, "; ".join(fidelity_issues),
        )
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
            "fidelity_issues": fidelity_issues or None,
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
            fidelity_issues=fidelity_issues,
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
        # Switch case naar verweer (alleen vanuit hoofdpad) via de centrale
        # step-transitie, zodat er een CaseStepHistory-rij + pipeline_change-
        # activity ontstaat én `step_entered_at` (de echte kolom) reset — i.p.v.
        # een losse attribuut-write zonder spoor (AUDIT-#97; ondervangt ook #H10).
        from app.incasso.service import move_case_to_step

        await move_case_to_step(
            db,
            tenant_id,
            case,
            verweer_step,
            trigger_type="auto_advance",
            notes="Automatische switch naar 'Verweer beantwoorden' (verweer-email ontvangen)",
        )
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
    fidelity_issues: list[str] | None = None,
) -> None:
    """Maak WorkflowTask aan zodat draft in /taken queue verschijnt.

    Bij `fidelity_issues` (getrouwheids-poort faalde na regeneraties) wordt de
    taak zichtbaar gemarkeerd — het concept bestaat, maar wijkt af van de
    dossier-context en verdient extra controle.
    """
    from app.workflow.models import WorkflowTask

    title = f"Review concept-email: {step_name}"
    description = f"AI heeft een concept-email klaargezet ({reason}). Bekijk en verstuur."
    if fidelity_issues:
        title = f"⚠ {title}"
        description += (
            " LET OP: concept wijkt af van het sjabloon/dossier "
            f"(ontbreekt: {'; '.join(fidelity_issues)}) — extra controleren."
        )

    task = WorkflowTask(
        tenant_id=tenant_id,
        case_id=case_id,
        task_type="review_ai_draft",
        title=title,
        description=description,
        due_date=datetime.now(UTC).date(),
        status="pending",
        action_config={"draft_id": str(draft_id), "step_name": step_name},
    )
    db.add(task)
    await db.flush()
    logger.info("WorkflowTask aangemaakt voor draft %s (case %s)", draft_id, case_id)
