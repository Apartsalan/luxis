"""UnifiedDraftService — single AI draft pipeline routing all 3 intents
(next_step / reply_to_email / free_compose) through the same branded HTML
render path used by the incasso batch flow.

Goal (sessie 145): visual consistency across every AI-generated message.
The AI ALWAYS returns plain body text. Server-side we wrap it via
incasso_templates._render_branded() so the output gets:
- Embedded data-URL logo (not blocked by Outlook/Gmail)
- Kantoor + ontvanger header
- Date + reference lines
- Signature with case_type-dependent email address
- Schuldhulp/disclaimer block (incasso cases only)
"""

from __future__ import annotations

import logging
import uuid
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai_agent.kimi_client import call_intake_ai
from app.ai_agent.models import AIDraft, DraftStatus, EmailClassification
from app.ai_agent.prompts import strip_html
from app.cases.models import Case, CaseParty
from app.documents.docx_service import build_base_context
from app.email.incasso_templates import (
    _render_branded,
    _schuldhulp_disclaimer,
    _signature,
)
from app.email.synced_email_models import SyncedEmail

logger = logging.getLogger(__name__)


class DraftIntent(StrEnum):
    """Three supported draft intents."""

    NEXT_STEP = "next_step"
    REPLY_TO_EMAIL = "reply_to_email"
    FREE_COMPOSE = "free_compose"


# ── System prompts ─────────────────────────────────────────────────────────

_NO_HTML_RULE = (
    "BELANGRIJK — output regels:\n"
    "- Geef PLATTE TEKST terug. GEEN HTML, GEEN markdown, GEEN opmaak-tags.\n"
    "- Gebruik gewone alineas gescheiden door lege regels.\n"
    "- Zet bedragen NIET in kolommen die je met spaties of tabs uitlijnt (dat wordt "
    "scheef in de uiteindelijke mail). Gebruik in plaats daarvan korte regels met een "
    "label, bijv. 'Hoofdsom: € 3.500,00' — elk op een eigen regel.\n"
    "- Eindig NIET met een handtekening — die wordt server-side toegevoegd.\n"
    "- Antwoord ALLEEN met valide JSON: "
    '{"subject": "<onderwerp>", "body": "<platte tekst>", "tone": "<formeel|vriendelijk|streng>"}'
)

_NEXT_STEP_PROMPT = (
    "Je bent juridisch assistent voor Kesting Legal (incassokantoor te Amsterdam, "
    "advocaat mr. L. Kesting). Je stelt het bericht op voor de volgende stap in een "
    "incasso-traject. Schrijf zakelijk Nederlands, gebruik 'u', verwijs naar "
    "dossiernummer en hoofdsom. Vermeld geen plaatshouders.\n\n" + _NO_HTML_RULE
)

# S221 blok 4.3 — begrip-eerst antwoordroute. De AI leest de inkomende mail én de
# dossierfeiten en schrijft zélf een passend antwoord, gestuurd door spelregels
# i.p.v. een vast sjabloon. De verweer-voorbeelden/AV worden apart als referentie
# meegegeven (bij een verweer-categorie); ze zijn leidraad, geen keurslijf.
_REPLY_PROMPT = (
    "Je bent juridisch assistent voor Kesting Legal (incassokantoor te Amsterdam, "
    "advocaat mr. L. Kesting). Lees de inkomende email van de debiteur zorgvuldig en "
    "schrijf een passend, zakelijk antwoord in het Nederlands ('u'). Beantwoord "
    "daadwerkelijk wat er gevraagd of gesteld wordt — begrijp de mail eerst, kies dan "
    "je woorden.\n\n"
    "SPELREGELS (strikt):\n"
    "- Gebruik ALLEEN feiten uit de meegegeven dossiergegevens (cliënt/opdrachtgever, "
    "debiteur, openstaand bedrag, vorderingen/factuurnummers). Verzin NOOIT bedragen, "
    "namen, data of factuurnummers. Staat een gevraagd feit niet in het dossier, zeg "
    "dan dat u dit navraagt — verzin het niet.\n"
    "- Doe GEEN toezeggingen namens de cliënt (geen kwijtschelding, geen uitstel, geen "
    "betalingsregeling, geen excuses namens de cliënt). Zulke verzoeken bevestig je niet; "
    "je geeft aan ze aan de cliënt voor te leggen.\n"
    "- Neem GEEN juridische standpunten in die niet in de dossiergegevens of algemene "
    "voorwaarden staan.\n"
    "- Antwoordt de debiteur op de vraag 'wie bent u / wie is uw cliënt': noem het kantoor "
    "en de opdrachtgever bij naam (staan in de dossiergegevens).\n"
    "- Bij een te lastig of juridisch gevoelig geval (advocatenbrief van de tegenpartij, "
    "AVG-/privacyverzoek, dagvaarding, dreiging, klacht over de advocaat): schrijf een korte "
    "ontvangstbevestiging en zet in het antwoord dat het intern wordt opgepakt — verzin "
    "geen inhoudelijk standpunt.\n"
    "- Verwijs naar het dossiernummer en, waar relevant, het openstaande bedrag.\n"
    "- Pas de toon aan op de gevraagde stijl (mild/zakelijk/streng); dreig niet met "
    "dagvaarding tenzij expliciet streng én gerechtvaardigd.\n"
    "- Gebruik de eventueel meegegeven verweer-voorbeelden en algemene voorwaarden als "
    "referentie/leidraad, niet als verplichte tekst.\n\n"
    + _NO_HTML_RULE
)

_FREE_COMPOSE_PROMPT = (
    "Je bent juridisch assistent voor Kesting Legal. Schrijf een passend "
    "concept-bericht op basis van de dossiercontext en eventuele gebruikersinstructie. "
    "Schrijf zakelijk Nederlands, gebruik 'u'.\n\n" + _NO_HTML_RULE
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _plain_to_html(text: str) -> str:
    """Convert plain text to safe HTML: blank lines → paragraphs,
    single newlines → <br>. Defensive against AI returning HTML — strip first."""
    if not text:
        return ""
    cleaned = strip_html(text).strip()
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    return "".join(
        f"<p style=\"margin:0 0 12px 0;\">{p.replace(chr(10), '<br>')}</p>"
        for p in paragraphs
    )


def _betreft_line(case_number: str, subject: str) -> str:
    """Format the 'Betreft' / subject line for the email header."""
    return f"<strong>Betreft:</strong> {subject}" if subject else f"<strong>Betreft:</strong> dossier {case_number}"


async def _load_case(
    db: AsyncSession, tenant_id: uuid.UUID, case_id: uuid.UUID
) -> Case:
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id, Case.tenant_id == tenant_id)
        .options(
            selectinload(Case.parties).selectinload(CaseParty.contact),
            selectinload(Case.client),
            selectinload(Case.opposing_party),
            selectinload(Case.incasso_step),
        )
    )
    case = result.scalar_one_or_none()
    if not case:
        raise ValueError("Dossier niet gevonden")
    return case


async def _load_classification_for_email(
    db: AsyncSession, tenant_id: uuid.UUID, source_email_id: uuid.UUID
) -> EmailClassification | None:
    """Find the most recent classification for a source email, if any."""
    result = await db.execute(
        select(EmailClassification)
        .where(
            EmailClassification.synced_email_id == source_email_id,
            EmailClassification.tenant_id == tenant_id,
        )
        .order_by(EmailClassification.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _load_source_email(
    db: AsyncSession, tenant_id: uuid.UUID, source_email_id: uuid.UUID
) -> SyncedEmail | None:
    result = await db.execute(
        select(SyncedEmail).where(
            SyncedEmail.id == source_email_id,
            SyncedEmail.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


# ── Prompt builders per intent ────────────────────────────────────────────


def _build_next_step_user_msg(case: Case, instruction: str | None) -> str:
    step_label = case.incasso_step.name if case.incasso_step else "volgende incassostap"
    parts = [
        f"Dossier: {case.case_number}",
        f"Zaaktype: {case.case_type}",
        f"Huidige incassostap: {step_label}",
    ]
    if case.opposing_party:
        parts.append(f"Wederpartij: {case.opposing_party.name}")
    if case.client:
        parts.append(f"Cliënt: {case.client.name}")
    if case.description:
        parts.append(f"Omschrijving: {case.description}")
    if instruction:
        parts.append(f"\nInstructie: {instruction}")
    else:
        parts.append(
            f"\nSchrijf een passend bericht voor de stap '{step_label}'. "
            "Houd het kort en zakelijk."
        )
    return "\n".join(parts)


async def _build_dossier_facts(
    db: AsyncSession, tenant_id: uuid.UUID, case: Case
) -> str:
    """Feitenblok voor de begrip-eerst-antwoordroute: cliënt, debiteur, openstaand
    bedrag en vorderingen (factuurnummer + hoofdsom). De AI mag ALLEEN hieruit putten;
    zo antwoordt hij met echte dossierdata i.p.v. verzonnen bedragen/namen."""
    from app.collections.models import Claim
    from app.collections.service import get_case_outstanding

    lines: list[str] = ["--- Dossiergegevens (enige toegestane feitenbron) ---"]
    if case.client:
        lines.append(f"Opdrachtgever (onze cliënt): {case.client.name}")
    if case.opposing_party:
        lines.append(f"Debiteur (wederpartij): {case.opposing_party.name}")

    try:
        outstanding = await get_case_outstanding(db, tenant_id, case)
        lines.append(f"Openstaand bedrag (incl. rente + kosten): € {outstanding}")
    except Exception:
        pass  # saldo niet berekenbaar → gewoon weglaten, niets verzinnen

    result = await db.execute(
        select(Claim).where(
            Claim.case_id == case.id,
            Claim.tenant_id == tenant_id,
            Claim.is_active.is_(True),
        )
    )
    claims = list(result.scalars().all())
    if claims:
        lines.append("Vorderingen:")
        for c in claims[:20]:
            nr = c.invoice_number or "(geen factuurnummer)"
            datum = c.invoice_date.isoformat() if c.invoice_date else "onbekend"
            lines.append(f"  - factuur {nr} d.d. {datum}: hoofdsom € {c.principal_amount}")
    return "\n".join(lines)


def _build_reply_user_msg(
    case: Case,
    source_email: SyncedEmail,
    classification: EmailClassification | None,
    tone: str | None,
    instruction: str | None,
    dossier_facts: str = "",
) -> str:
    body = source_email.body_text or strip_html(source_email.body_html or "") or ""
    body = body[:2000]
    parts = [
        f"Dossier: {case.case_number}",
        f"Zaaktype: {case.case_type}",
        f"Gewenste toon: {tone or 'zakelijk'}",
    ]
    if classification:
        parts.append(f"Classificatie: {classification.category}")
        if classification.sentiment:
            parts.append(f"Sentiment: {classification.sentiment}")
    if dossier_facts:
        parts.append("\n" + dossier_facts)
    parts.append("\n--- Inkomende email ---")
    parts.append(f"Van: {source_email.from_email}")
    parts.append(f"Onderwerp: {source_email.subject}")
    parts.append(body)
    if instruction:
        parts.append(f"\nExtra instructie: {instruction}")
    return "\n".join(parts)


def _build_free_compose_user_msg(case: Case, instruction: str | None) -> str:
    parts = [
        f"Dossier: {case.case_number}",
        f"Zaaktype: {case.case_type}",
        f"Status: {case.status}",
    ]
    if case.opposing_party:
        parts.append(f"Wederpartij: {case.opposing_party.name}")
    if case.client:
        parts.append(f"Cliënt: {case.client.name}")
    if instruction:
        parts.append(f"\nInstructie: {instruction}")
    else:
        parts.append("\nSchrijf een passend concept-bericht op basis van bovenstaande context.")
    return "\n".join(parts)


# ── Kennis-injectie (S173) ─────────────────────────────────────────────────


async def _build_verweer_knowledge(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    category: str | None,
    defense_type: str | None = None,
) -> str:
    """AV + verweer-bibliotheek + goedgekeurde geleerde voorbeelden voor de prompt.

    Alleen bij een verweer-categorie (juridisch_verweer/betwisting) — bij een gewoon
    bericht voegen deze niets toe en vergroten ze alleen de kans dat het model afdwaalt
    (S164-les). Lege string als er niets zinvols is. Gebruikt bewust de bestaande gedeelde
    helpers zodat de bibliotheek/geleerde voorbeelden identiek zijn aan de andere paden.
    `defense_type` (V4) geeft geleerde voorbeelden van hetzelfde verweer-type voorrang.
    """
    from app.ai_agent.learned_answers import LEARNABLE_CATEGORIES, build_learned_examples_text

    if category not in LEARNABLE_CATEGORIES:
        return ""

    from app.ai_agent.defense_library import (
        DEFENSE_EXAMPLES,
        format_examples_for_prompt,
    )
    from app.ai_agent.knowledge_context import resolve_case_terms

    parts: list[str] = []
    av_text, _ = await resolve_case_terms(db, tenant_id, case)
    if av_text:
        parts.append(
            "--- Algemene Voorwaarden van cliënt "
            "(citeer artikelnummer + tekst waar relevant) ---\n" + av_text
        )
    # Alle 5 voorbeelden (incl. de Engelse) net als het incasso-pad — get_relevant_examples
    # filterde op NL en liet het Engelse voorbeeld vallen (S174). Alle voorbeelden delen de
    # verweer-categorieën, dus het categorie-filter voegde hier niets toe.
    defense_text = format_examples_for_prompt(DEFENSE_EXAMPLES, max_chars=8000)
    if defense_text:
        parts.append(defense_text)
    learned_text = await build_learned_examples_text(
        db, tenant_id, category, defense_type=defense_type
    )
    if learned_text:
        parts.append(learned_text)
    return "\n\n".join(parts)


# ── Main entrypoint ───────────────────────────────────────────────────────


# Concepten die nog niet zijn verstuurd of weggegooid tellen als "open".
_OPEN_DRAFT_STATUSES = (
    DraftStatus.GENERATED,
    DraftStatus.REVIEWED,
    DraftStatus.APPROVED,
)


async def _find_open_duplicate_draft(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    intent: DraftIntent,
    *,
    step_id: uuid.UUID | None,
    classification_id: uuid.UUID | None,
) -> AIDraft | None:
    """S221 3.2 — bestaat er al een open concept voor dezelfde bedoeling?

    Voorkomt een tweede (betaalde) generatie bij dubbelklik of opnieuw-genereren:
    - volgende stap → zelfde zaak + zelfde pijplijnstap
    - antwoord op mail → zelfde zaak + zelfde bron-mail (classificatie)
    - vrij opstellen → nooit ontdubbelen (gebruiker wil bewust een nieuwe).

    Retourneert het nieuwste passende open concept, of None.
    """
    if intent == DraftIntent.FREE_COMPOSE:
        return None
    query = select(AIDraft).where(
        AIDraft.tenant_id == tenant_id,
        AIDraft.case_id == case_id,
        AIDraft.intent == intent.value,
        AIDraft.status.in_(_OPEN_DRAFT_STATUSES),
    )
    if intent == DraftIntent.NEXT_STEP:
        # Zelfde stap (of allebei stap-loos) → dubbelklik-bescherming.
        if step_id is None:
            query = query.where(AIDraft.step_id.is_(None))
        else:
            query = query.where(AIDraft.step_id == step_id)
    else:  # REPLY_TO_EMAIL
        if classification_id is None:
            return None
        query = query.where(AIDraft.classification_id == classification_id)
    query = query.order_by(AIDraft.generated_at.desc()).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def generate_unified_draft(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    *,
    case_id: uuid.UUID,
    intent: DraftIntent | str,
    tone: str | None = None,
    source_email_id: uuid.UUID | None = None,
    instruction: str | None = None,
) -> AIDraft:
    """Generate an AI draft via the unified pipeline.

    Returns persisted AIDraft (caller must commit). body_html is wrapped via
    incasso_templates._render_branded — falls back to None if base context
    can't be built (case without client/claims).
    """
    if isinstance(intent, str):
        intent = DraftIntent(intent)

    case = await _load_case(db, tenant_id, case_id)
    classification: EmailClassification | None = None

    if intent == DraftIntent.NEXT_STEP:
        system_prompt = _NEXT_STEP_PROMPT
        user_msg = _build_next_step_user_msg(case, instruction)
        classification_id = None
    elif intent == DraftIntent.REPLY_TO_EMAIL:
        if not source_email_id:
            raise ValueError("source_email_id is verplicht voor reply_to_email")
        source_email = await _load_source_email(db, tenant_id, source_email_id)
        if not source_email:
            raise ValueError("Bronemail niet gevonden")
        classification = await _load_classification_for_email(
            db, tenant_id, source_email_id
        )
        system_prompt = _REPLY_PROMPT
        dossier_facts = await _build_dossier_facts(db, tenant_id, case)
        user_msg = _build_reply_user_msg(
            case, source_email, classification, tone, instruction, dossier_facts
        )
        classification_id = classification.id if classification else None
    else:  # FREE_COMPOSE
        system_prompt = _FREE_COMPOSE_PROMPT
        user_msg = _build_free_compose_user_msg(case, instruction)
        classification_id = None

    # S221 3.2 — geen tweede concept (en geen tweede AI-rekening) als er al een open
    # concept voor dezelfde bedoeling staat. Toon het bestaande i.p.v. te dubbelen.
    existing = await _find_open_duplicate_draft(
        db, tenant_id, case_id, intent,
        step_id=case.incasso_step_id,
        classification_id=classification_id,
    )
    if existing is not None:
        logger.info(
            "UnifiedDraftService: bestaand open concept %s hergebruikt (case=%s, intent=%s)",
            existing.id, case.case_number, intent.value,
        )
        return existing

    # S173: geef álle 3 de intents dezelfde kennis (AV + verweer-bibliotheek + geleerde
    # voorbeelden) als het incasso-pad — maar alléén bij een verweer-categorie. Voorheen
    # zag de compose-dialog niets, dus hing de kwaliteit af van welke knop toevallig werd
    # gebruikt. Categorie: van de bron-email (reply) of de laatste dossier-classificatie.
    from app.ai_agent.knowledge_context import last_inbound_defense

    if classification:
        category = classification.category
        defense_type = classification.defense_type
    else:
        category, defense_type = await last_inbound_defense(db, tenant_id, case.id)
    knowledge = await _build_verweer_knowledge(db, tenant_id, case, category, defense_type)
    if knowledge:
        user_msg = f"{user_msg}\n\n{knowledge}"

    logger.info(
        "UnifiedDraftService: case=%s intent=%s tone=%s",
        case.case_number,
        intent.value,
        tone,
    )

    result, model = await call_intake_ai(system_prompt, user_msg)

    subject = (result.get("subject") or "").strip()
    body = (result.get("body") or "").strip()
    ai_tone = (result.get("tone") or tone or "formeel").strip()

    # Wrap to branded HTML — defensive: fall back to None if context build fails
    body_html: str | None = None
    try:
        ctx = await build_base_context(db, tenant_id, case)
        content_html = _plain_to_html(body)
        afsluiting = _signature(ctx)
        disclaimer = _schuldhulp_disclaimer(ctx) if case.case_type == "incasso" else ""
        body_html = _render_branded(
            ctx,
            betreft=_betreft_line(case.case_number, subject),
            content_html=content_html,
            afsluiting_html=afsluiting,
            disclaimer_html=disclaimer,
        )
    except Exception as e:
        logger.warning(
            "UnifiedDraftService: branded wrap mislukt voor case %s — fallback naar plain body. Reden: %s",
            case.case_number,
            e,
        )

    draft = AIDraft(
        tenant_id=tenant_id,
        case_id=case.id,
        classification_id=classification_id,
        subject=subject,
        body=body,
        body_html=body_html,
        tone=ai_tone,
        sources=None,
        reasoning=None,
        status=DraftStatus.GENERATED,
        model_used=model,
        instruction=instruction,
        intent=intent.value,
        step_id=case.incasso_step_id,
    )
    db.add(draft)
    await db.flush()
    await db.refresh(draft)

    logger.info(
        "UnifiedDraftService: draft %s persisted (case=%s, model=%s, html=%s)",
        draft.id,
        case.case_number,
        model,
        "yes" if body_html else "no",
    )

    # Notify tenant users that the AI draft is ready (CaseActionFeed S146)
    try:
        from app.notifications.service import create_draft_ready_notification

        preview = (strip_html(body) if body else "").strip()
        await create_draft_ready_notification(
            db,
            tenant_id,
            case.id,
            case.case_number,
            intent.value,
            preview,
        )
    except Exception:
        logger.exception(
            "Notification voor ai_draft_ready mislukt — draft is wel opgeslagen"
        )

    return draft
