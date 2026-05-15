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

_REPLY_PROMPT = (
    "Je bent juridisch assistent voor Kesting Legal. Je schrijft een antwoord op "
    "een inkomende email van een debiteur. Pas de toon aan op de gevraagde stijl "
    "(mild/zakelijk/streng). Verwijs naar dossiernummer en openstaand bedrag. "
    "Geen automatische dreiging met dagvaarding tenzij streng en gerechtvaardigd.\n\n"
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


def _build_reply_user_msg(
    case: Case,
    source_email: SyncedEmail,
    classification: EmailClassification | None,
    tone: str | None,
    instruction: str | None,
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


# ── Main entrypoint ───────────────────────────────────────────────────────


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
        user_msg = _build_reply_user_msg(case, source_email, classification, tone, instruction)
        classification_id = classification.id if classification else None
    else:  # FREE_COMPOSE
        system_prompt = _FREE_COMPOSE_PROMPT
        user_msg = _build_free_compose_user_msg(case, instruction)
        classification_id = None

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
    return draft
