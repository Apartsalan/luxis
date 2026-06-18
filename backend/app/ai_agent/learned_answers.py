"""Shadow-learning service — leer van de echte verzonden antwoorden van de advocaat.

Kerngedachte (besluit S160: assistent, geen autonomie): bij het opstellen van een
concept-antwoord stuurt de agent niet (alleen) de 5 hand-gecureerde voorbeelden mee,
maar Lisanne's EIGEN eerdere antwoorden in dezelfde classificatie-categorie. Elk
verzonden antwoord wordt automatisch een toekomstig voorbeeld → continu lerend.

Bewust SIMPEL gehouden (geen embeddings/vector-database, geen externe provider):
* Bron = uitgaande SyncedEmail (haar echte, hand-bewerkte tekst) gekoppeld aan de
  categorie van de inkomende mail waarop ze reageerde (via dossier + tijd).
* Ophalen = categorie-filter, nieuwste eerst. Bij het kleine huidige volume voegt
  semantische gelijkenis vrijwel niets toe; embeddings zijn een latere upgrade.
* PII: voorbeelden worden meegestuurd als referentie voor TOON en ARGUMENTATIE; de
  prompt instrueert expliciet om geen concrete namen/bedragen/data over te nemen.
"""

import difflib
import logging
import re
import uuid
from html import unescape as _html_unescape

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.models import AIDraft, EmailClassification, LearnedAnswer
from app.email.synced_email_models import SyncedEmail

logger = logging.getLogger(__name__)

# Categorieën waarvoor geleerde voorbeelden zinvol zijn (inhoudelijke verweer-antwoorden).
LEARNABLE_CATEGORIES = ("juridisch_verweer", "betwisting")

# ── Body opschonen ───────────────────────────────────────────────────────────

# Markers waarna de geciteerde/originele mail of de handtekening begint — alles
# daarna knippen we weg zodat alleen de kern-argumentatie overblijft (zoals de
# hand-voorbeelden). Heuristisch en bewust conservatief; later te verbeteren met
# een AI-extractiestap als de kwaliteit dat vraagt.
_CUT_MARKERS = [
    re.compile(r"^\s*Op .+ schreef .+:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*Van:\s", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*From:\s", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^-{3,}\s*Oorspronkelijk bericht", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^_{5,}\s*$", re.MULTILINE),
    re.compile(r"^\s*>", re.MULTILINE),
    re.compile(r"^\s*(Met vriendelijke groet|Hoogachtend|Met groet|Mvg)\b", re.IGNORECASE | re.MULTILINE),
]
# Hele aanhef-regel ("Geachte ...,"). Alles ervóór (Betreft, adresblok, sjabloon-kop)
# én de regel zelf wordt weggehaald, zodat alleen de eigenlijke inhoud overblijft.
_GREETING_LINE = re.compile(r"^\s*Geachte[^\n]*,?\s*$", re.IGNORECASE | re.MULTILINE)


def clean_answer_body(raw: str) -> str:
    """Haal de kern-inhoud uit een antwoord (zonder kop/aanhef/handtekening/quote)."""
    text = (raw or "").replace("\r\n", "\n").strip()
    if not text:
        return ""
    # Drop alles t/m de aanhef-regel (Betreft/adresblok/"Geachte ...").
    g = _GREETING_LINE.search(text)
    if g:
        text = text[g.end():].lstrip()
    # Knip bij de vroegste quote-/handtekening-marker.
    cut = len(text)
    for marker in _CUT_MARKERS:
        m = marker.search(text)
        if m and m.start() < cut:
            cut = m.start()
    text = text[:cut]
    # Lege regels samentrekken + trimmen.
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


# ── Ophalen + formatteren voor de prompt ─────────────────────────────────────


async def get_learned_examples(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    category: str | None,
    *,
    language: str = "nl",
    limit: int = 3,
) -> list[LearnedAnswer]:
    """Haal Lisanne's eigen eerdere antwoorden op in deze categorie (nieuwste eerst)."""
    if not category:
        return []
    result = await db.execute(
        select(LearnedAnswer)
        .where(
            LearnedAnswer.tenant_id == tenant_id,
            LearnedAnswer.category == category,
            LearnedAnswer.is_active.is_(True),
        )
        .order_by(LearnedAnswer.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


def format_learned_examples_for_prompt(
    examples: list[LearnedAnswer],
    max_chars: int = 4000,
) -> str:
    """Formatteer geleerde voorbeelden als promptcontext, met PII-instructie."""
    if not examples:
        return ""
    header = (
        "--- Mijn eigen eerdere antwoorden in vergelijkbare situaties "
        "(referentie voor TOON en ARGUMENTATIE — neem GEEN concrete namen, "
        "bedragen, datums of dossiergegevens uit deze voorbeelden over) ---"
    )
    parts = [header]
    chars = len(header)
    for i, ex in enumerate(examples, 1):
        block = f"\n[Voorbeeld {i}]\n{ex.body}"
        if chars + len(block) > max_chars:
            break
        parts.append(block)
        chars += len(block)
    return "\n".join(parts)


async def build_learned_examples_text(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    category: str | None,
    *,
    max_chars: int = 4000,
) -> str:
    """Ophalen + formatteren + use_count bijwerken — de enige call die de prompt-bouwers nodig hebben."""
    examples = await get_learned_examples(db, tenant_id, category)
    if not examples:
        return ""
    # Tel het gebruik (voor het dashboard: welke eigen antwoorden worden het meest hergebruikt).
    for ex in examples:
        ex.use_count = (ex.use_count or 0) + 1
    return format_learned_examples_for_prompt(examples, max_chars=max_chars)


# ── Backfill + capture (leer-data vullen) ────────────────────────────────────


# Collectiebrief-markers: in het ONDERWERP óf in de kop/opening van de BODY. Een vrije
# verweer-reactie weerlegt de argumenten van de debiteur; een collectiebrief (sommatie,
# aanmaning, of een follow-up "Eerder heb ik u aangeschreven ... ter incasso") kondigt
# een betaal-eis aan. Bij twijfel sluiten we uit — liever geen voorbeeld dan een fout
# voorbeeld. (De eerste versie keek alleen naar het onderwerp en miste brieven waar de
# "Betreft: SOMMATIE"-kop in de body staat.)
_TEMPLATE_MARKERS = re.compile(
    r"(sommatie|aanmaning|herinnering|betalingsherinnering|ingebrekestelling|"
    r"dagvaarding|verzoekschrift|14[- ]?dagenbrief|ter incasso|"
    r"eerder heb ik u aangeschreven|eerder schreef ik u aan)",
    re.IGNORECASE,
)


def _looks_like_collection_letter(subject: str | None, body: str | None) -> bool:
    """True als dit een sjabloon-collectiebrief is (geen vrije verweer-reactie)."""
    head = f"{subject or ''}\n{(body or '')[:400]}"
    return bool(_TEMPLATE_MARKERS.search(head))


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _email_body_text(email: SyncedEmail) -> str:
    """Platte tekst van een mail. Veel mails (Outlook/Graph) hebben ALLÉÉN een HTML-body
    — dan is body_text leeg en moeten we de tekst uit body_html halen. Zonder dit keek
    het filter naar een lege body en glipten sjabloon-sommaties er doorheen."""
    if email.body_text and email.body_text.strip():
        return email.body_text
    if email.body_html:
        stripped = _HTML_TAG_RE.sub(" ", email.body_html)
        return re.sub(r"\s+", " ", _html_unescape(stripped)).strip()
    return email.snippet or ""


async def _category_for_outbound(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    sent_before: object,
) -> str | None:
    """Categorie waarop een uitgaand antwoord reageert: de classificatie van de meest
    recente INKOMENDE mail op dit dossier vóór de verzenddatum."""
    return (
        await db.execute(
            select(EmailClassification.category)
            .join(SyncedEmail, EmailClassification.synced_email_id == SyncedEmail.id)
            .where(
                EmailClassification.tenant_id == tenant_id,
                EmailClassification.case_id == case_id,
                SyncedEmail.direction == "inbound",
                SyncedEmail.email_date <= sent_before,
            )
            .order_by(SyncedEmail.email_date.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def backfill_learned_answers(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> int:
    """Leer van wat de advocaat ÉCHT verstuurt — haar correcties.

    Bron = uitgaande SyncedEmail (de werkelijk verzonden tekst = haar correctie op het
    AI-voorstel), op een dossier waar de recentste inkomende mail als verweer is
    geclassificeerd (betwisting/juridisch_verweer). Sjabloonbrieven (sommatie/aanmaning/
    ...) worden via het onderwerp uitgesloten — dat zijn geen vrije verweer-reacties.

    Bewust de uitgaande mail en niet het AIDraft: het concept in de database is het
    AI-VOORSTEL; de verzonden mail is wat Lisanne er werkelijk van maakte. Wij leren van
    haar versie. Idempotent (dedup op source_synced_email_id). Draait na elke e-mailsync,
    dus haar nieuwe antwoorden worden vanzelf opgepikt (continu lerend). Geeft het aantal
    NIEUW toegevoegde voorbeelden terug.
    """
    existing = (
        await db.execute(
            select(LearnedAnswer.source_synced_email_id).where(
                LearnedAnswer.tenant_id == tenant_id,
                LearnedAnswer.source_synced_email_id.is_not(None),
            )
        )
    ).scalars().all()
    seen = {e for e in existing if e is not None}

    outbound = (
        await db.execute(
            select(SyncedEmail)
            .where(
                SyncedEmail.tenant_id == tenant_id,
                SyncedEmail.direction == "outbound",
                SyncedEmail.case_id.is_not(None),
                SyncedEmail.is_bounce.is_(False),
            )
            .order_by(SyncedEmail.email_date.asc())
        )
    ).scalars().all()

    added = 0
    for email in outbound:
        if email.id in seen:
            continue
        # Volledige tekst (uit body_html als body_text leeg is — vaak bij Outlook).
        body_text = _email_body_text(email)
        # Sjabloon-collectiebrief of oningevuld verweer-sjabloon ("XXX") overslaan.
        if _looks_like_collection_letter(email.subject, body_text) or " XXX " in body_text:
            continue
        category = await _category_for_outbound(
            db, tenant_id, email.case_id, email.email_date
        )
        if category not in LEARNABLE_CATEGORIES:
            continue
        body = clean_answer_body(body_text)
        if len(body) < 40:  # te kort voor een zinvol voorbeeld
            continue
        db.add(
            LearnedAnswer(
                tenant_id=tenant_id,
                category=category,
                body=body,
                language="nl",
                source_synced_email_id=email.id,
                source_case_id=email.case_id,
            )
        )
        seen.add(email.id)
        added += 1

    if added:
        await db.flush()
    logger.info("Shadow-learning backfill tenant=%s: %d nieuwe voorbeelden", tenant_id, added)
    return added


# ── Dashboard-statistieken (edit-rate + leer-stats) ──────────────────────────


def _similarity(a: str, b: str) -> float:
    """Gelijkenis 0..1 tussen twee teksten (1 = identiek)."""
    return difflib.SequenceMatcher(None, a or "", b or "").ratio()


async def get_learning_stats(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Statistieken voor het kwaliteits-dashboard.

    - edit_rate: van recent verzonden concepten, hoeveel (bijna) ongewijzigd de deur uit
      gingen (AI-versie vs. wat Lisanne echt verstuurde).
    - per_category: aantal geleerde voorbeelden per categorie.
    - top_examples: meest hergebruikte eigen antwoorden.
    """
    # 1. Edit-rate: koppel verzonden AI-concepten aan de uitgaande mail erna.
    sent_drafts = (
        await db.execute(
            select(AIDraft)
            .where(
                AIDraft.tenant_id == tenant_id,
                AIDraft.status == "sent",
            )
            .order_by(AIDraft.sent_at.desc().nullslast())
            .limit(50)
        )
    ).scalars().all()

    buckets = {"ongewijzigd": 0, "licht": 0, "fors": 0}
    matched = 0
    for draft in sent_drafts:
        if not draft.case_id or not draft.generated_at:
            continue
        outbound = (
            await db.execute(
                select(SyncedEmail)
                .where(
                    SyncedEmail.tenant_id == tenant_id,
                    SyncedEmail.case_id == draft.case_id,
                    SyncedEmail.direction == "outbound",
                    SyncedEmail.email_date >= draft.generated_at,
                )
                .order_by(SyncedEmail.email_date.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if not outbound:
            continue
        ai_body = clean_answer_body(draft.body or "")
        sent_body = clean_answer_body(_email_body_text(outbound))
        if not ai_body or not sent_body:
            continue
        ratio = _similarity(ai_body, sent_body)
        if ratio >= 0.9:
            buckets["ongewijzigd"] += 1
        elif ratio >= 0.6:
            buckets["licht"] += 1
        else:
            buckets["fors"] += 1
        matched += 1

    # 2. Geleerde voorbeelden per categorie.
    per_cat_rows = (
        await db.execute(
            select(LearnedAnswer.category, func.count())
            .where(
                LearnedAnswer.tenant_id == tenant_id,
                LearnedAnswer.is_active.is_(True),
            )
            .group_by(LearnedAnswer.category)
        )
    ).all()
    per_category = {cat: count for cat, count in per_cat_rows}
    total_examples = sum(per_category.values())

    # 3. Meest hergebruikte eigen antwoorden.
    top = (
        await db.execute(
            select(LearnedAnswer)
            .where(
                LearnedAnswer.tenant_id == tenant_id,
                LearnedAnswer.is_active.is_(True),
                LearnedAnswer.use_count > 0,
            )
            .order_by(LearnedAnswer.use_count.desc())
            .limit(5)
        )
    ).scalars().all()
    top_examples = [
        {
            "category": ex.category,
            "use_count": ex.use_count,
            "preview": (ex.body or "")[:160],
        }
        for ex in top
    ]

    return {
        "edit_rate": {
            "matched": matched,
            "ongewijzigd": buckets["ongewijzigd"],
            "licht": buckets["licht"],
            "fors": buckets["fors"],
        },
        "total_examples": total_examples,
        "per_category": per_category,
        "top_examples": top_examples,
    }
