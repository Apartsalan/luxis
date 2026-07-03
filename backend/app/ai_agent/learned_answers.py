"""Verweer-antwoord-bibliotheek — laat de standaardantwoorden gecontroleerd groeien.

Herzien in S167 na een kritische review. De oude opzet ('leer stil en automatisch van
elke verzonden mail') werkte in de praktijk niet: Lisanne's verweer-reacties zitten in
een sommatie-sjabloon verpakt, waardoor het filter ze óf helemaal weggooide, óf juist
kopieën van de 5 bestaande standaardteksten terug-leerde — mét persoonsgegevens.

Nieuwe werkwijze — een assistent, Lisanne beslist (besluit S160):
1. VANGEN — uit haar verstuurde antwoorden knippen we de kern-weerlegging (zonder de
   sommatie-omlijsting) en bewaren die als KANDIDAAT. Weerleggingen die te veel op de 5
   bestaande standaardteksten lijken slaan we over — die kennen we al.
2. VOORSTELLEN — bij elke kandidaat maakt het systeem een geanonimiseerd voorstel
   (namen/bedragen/datums vervangen door plaatshouders).
3. GOEDKEUREN — Lisanne bevestigt (of past aan) de geanonimiseerde tekst en keurt hem
   goed. Pas dán, en alleen de geanonimiseerde tekst, gaat als voorbeeld naar de AI.

Geen embeddings/externe provider (AVG-veilig). Matching op verweer-TYPE, niet op datum.

NB (S167): de kern-extractie (`extract_rebuttal`) en de library-gelijkenis zijn heuristisch
en op één echte voorbeeldmail afgesteld. Bij de BaseNet-import (duizenden echte brieven)
nog fijn-afstellen — de menselijke goedkeuring vangt tussentijdse missers op.
"""

import difflib
import logging
import re
import uuid
from datetime import UTC, datetime
from html import unescape as _html_unescape

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.defense_library import DEFENSE_EXAMPLES
from app.ai_agent.models import AIDraft, EmailClassification, LearnedAnswer
from app.email.synced_email_models import SyncedEmail

logger = logging.getLogger(__name__)

# Categorieën waarvoor geleerde voorbeelden zinvol zijn (inhoudelijke verweer-antwoorden).
LEARNABLE_CATEGORIES = ("juridisch_verweer", "betwisting")

# Statuswaarden (spiegelt LearnedAnswer.status).
STATUS_CANDIDATE = "kandidaat"
STATUS_APPROVED = "goedgekeurd"
STATUS_REJECTED = "afgewezen"

# Boven deze gelijkenis met een bestaande standaardtekst kennen we het antwoord al →
# geen kandidaat (voorkomt het terug-leren van de 5 library-teksten). Daaronder, maar
# boven de type-drempel, koppelen we het aan dat verweer-type; nog lager = 'overig'.
_LIBRARY_DUPLICATE_RATIO = 0.85
_LIBRARY_TYPE_RATIO = 0.45


# ── Body opschonen ───────────────────────────────────────────────────────────

# Markers waarna de geciteerde/originele mail of de handtekening begint.
_CUT_MARKERS = [
    re.compile(r"^\s*Op .+ schreef .+:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*Van:\s", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*From:\s", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^-{3,}\s*Oorspronkelijk bericht", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^_{5,}\s*$", re.MULTILINE),
    re.compile(r"^\s*>", re.MULTILINE),
    re.compile(r"(Met vriendelijke groet|Hoogachtend|Met groet|Mvg)\b", re.IGNORECASE),
]
# Hele aanhef-regel ("Geachte ...,"). Alles ervóór (Betreft, adresblok, sjabloon-kop)
# én de regel zelf wordt weggehaald.
_GREETING_LINE = re.compile(r"^\s*Geachte[^\n]*,?\s*$", re.IGNORECASE | re.MULTILINE)


def clean_answer_body(raw: str) -> str:
    """Haal de kern-inhoud uit een antwoord (zonder kop/aanhef/handtekening/quote)."""
    text = (raw or "").replace("\r\n", "\n").strip()
    if not text:
        return ""
    g = _GREETING_LINE.search(text)
    if g:
        text = text[g.end():].lstrip()
    cut = len(text)
    for marker in _CUT_MARKERS:
        m = marker.search(text)
        if m and m.start() < cut:
            cut = m.start()
    text = text[:cut]
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


# ── Kern-weerlegging uit een sommatie-verpakt antwoord knippen ────────────────

# De weerlegging begint hier. Lisanne's verweer-reactie zit ingebed in een sommatiebrief;
# de inhoudelijke reactie start ná een van deze markers.
_REBUTTAL_INTRO = re.compile(
    r"(Hierbij voorzie ik u van een inhoudelijke reactie[^\n.]*\.?|"
    r"waarin ik uw stellingen weerleg\.?)",
    re.IGNORECASE,
)
# Een substantiële weerlegging opent doorgaans zó (dit is óók het signaal 'dit is echt een
# verweer-reactie en geen kale sommatie').
_REBUTTAL_OPENER = re.compile(
    r"(U heeft (gesteld|aangevoerd|betoogd|aangegeven|gereageerd)|"
    r"In reactie op uw (stellingen|verweer|bericht|reactie)|"
    r"Ten aanzien van uw (verweer|stelling|bericht)|"
    r"Uw verweer|Naar aanleiding van uw)",
    re.IGNORECASE,
)
# Waar de weerlegging eindigt en de sommatie-staart (betaal-eis) begint.
_PAYMENT_TAIL = re.compile(
    r"(Ik verzoek u (?:dan ook |vriendelijk |hierbij |thans )*"
    r"(?:om )?(?:het|de|binnen|thans|per omgaande|nogmaals)|"
    r"gelieve (?:het|de|binnen|per)|"
    r"binnen (?:vijf|5|zeven|7|veertien|14|drie|3|acht|8|tien|10) dagen|"
    r"Het (?:totaal(?:aal)? |thans |)verschuldigde bedrag|"
    r"te voldoen op (?:onze|ons|de|het)|"
    r"onder vermelding van|"
    r"bij gebreke (?:van|waarvan)|"
    r"IBAN\s*NL\d{2})",
    re.IGNORECASE,
)


def _looks_like_rebuttal(subject: str | None, body: str | None) -> bool:
    """True als dit een inhoudelijke verweer-reactie is (bevat een weerlegging), en niet
    een kale sommatie/aanmaning. Cruciaal: een echte verweer-reactie ZIT in een
    sommatie-sjabloon — we herkennen hem aan de aanwezigheid van een weerlegging, niet aan
    de afwezigheid van sommatie-woorden (dat was de fout die alle echte antwoorden weggooide)."""
    text = body or ""
    return bool(_REBUTTAL_OPENER.search(text) or _REBUTTAL_INTRO.search(text))


def extract_rebuttal(subject: str | None, body: str | None) -> str:
    """Knip de kern-weerlegging uit een sommatie-verpakt verweer-antwoord.

    Laat de sommatie-preamble ('Eerder heb ik u aangeschreven ... ter incasso') en de
    betaal-staart (bedragen, IBAN, termijn, handtekening) weg, zodat alleen de eigenlijke
    juridische weerlegging overblijft — vergelijkbaar met de hand-voorbeelden.
    """
    text = (body or "").replace("\r\n", "\n").strip()
    if not text:
        return ""

    # START: begin bij de substantiële opener; anders net ná de intro-zin.
    start = 0
    opener = _REBUTTAL_OPENER.search(text)
    if opener:
        start = opener.start()
    else:
        intro = _REBUTTAL_INTRO.search(text)
        if intro:
            start = intro.end()
    core = text[start:].lstrip()

    # EIND: knip bij de betaal-staart of bij handtekening/quote (vroegste wint).
    cut = len(core)
    tail = _PAYMENT_TAIL.search(core)
    if tail:
        cut = tail.start()
    for marker in _CUT_MARKERS:
        m = marker.search(core)
        if m and m.start() < cut:
            cut = m.start()
    core = core[:cut]

    core = re.sub(r"[ \t]+", " ", core)
    core = re.sub(r"\n{3,}", "\n\n", core).strip()
    return core


def _norm_ws(s: str) -> str:
    """Witruimte platslaan zodat 'spatie vs. nieuwe regel'-verschillen de gelijkenis niet drukken."""
    return re.sub(r"\s+", " ", s or "").strip().lower()


def _similarity_to_library(text: str) -> tuple[float, str | None]:
    """Hoogste gelijkenis (0..1) van `text` met een bestaande standaardtekst + de key ervan."""
    norm = _norm_ws(text)
    best_ratio = 0.0
    best_key: str | None = None
    for ex in DEFENSE_EXAMPLES:
        ratio = difflib.SequenceMatcher(None, norm, _norm_ws(ex.body)).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_key = ex.key
    return best_ratio, best_key


# ── Anonimiseren-voorstel ─────────────────────────────────────────────────────

# Heuristische vervangingen — een VOORSTEL dat Lisanne bevestigt/bijstelt. Bewust
# ruimhartig: liever iets te veel maskeren dan een naam/bedrag laten staan.
_ANON_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"€\s?\d[\d.,]*"), "[bedrag]"),
    (re.compile(r"\bNL\d{2}\s?[A-Z]{4}\s?(?:\d{4}\s?){2}\d{2}\b"), "[rekeningnummer]"),
    (re.compile(r"\b20\d{2}-\d{3,6}\b"), "[kenmerk]"),
    (re.compile(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"), "[datum]"),
    (
        re.compile(
            r"\b\d{1,2}\s+(?:januari|februari|maart|april|mei|juni|juli|augustus|"
            r"september|oktober|november|december)\s+\d{4}\b",
            re.IGNORECASE,
        ),
        "[datum]",
    ),
    (
        re.compile(
            r"\b(?:[Dd]e\s+heer|[Mm]evrouw|[Dd]hr\.?|[Mm]evr\.?|[Mm]w\.?)"
            r"\s+[A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+){0,2}"
        ),
        "[naam]",
    ),
]


def suggest_anonymization(text: str) -> str:
    """Vervang namen/bedragen/datums/kenmerken door plaatshouders (een voorstel)."""
    out = text or ""
    for pattern, repl in _ANON_RULES:
        out = pattern.sub(repl, out)
    return out


# ── Ophalen + formatteren voor de prompt (alleen GOEDGEKEURDE) ────────────────


async def get_learned_examples(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    category: str | None,
    *,
    language: str = "nl",
    limit: int = 3,
) -> list[LearnedAnswer]:
    """Haal goedgekeurde verweer-voorbeelden op in deze categorie.

    Kiest op verweer-TYPE gespreid (niet blind 'nieuwste eerst'): eerst de meest
    hergebruikte per type, zodat een divers en passend setje meegaat — anders zou na een
    bulk-import 'nieuwste 3' een willekeurige greep zijn.
    """
    if not category:
        return []
    rows = (
        await db.execute(
            select(LearnedAnswer)
            .where(
                LearnedAnswer.tenant_id == tenant_id,
                LearnedAnswer.category == category,
                LearnedAnswer.status == STATUS_APPROVED,
            )
            .order_by(LearnedAnswer.use_count.desc(), LearnedAnswer.created_at.desc())
            .limit(max(limit * 4, 12))
        )
    ).scalars().all()

    # Spreid over verweer-typen: max één per type tot de limiet, vul daarna aan.
    picked: list[LearnedAnswer] = []
    seen_types: set[str] = set()
    for r in rows:
        t = r.defense_type or "overig"
        if t not in seen_types:
            picked.append(r)
            seen_types.add(t)
        if len(picked) >= limit:
            break
    if len(picked) < limit:
        for r in rows:
            if r not in picked:
                picked.append(r)
            if len(picked) >= limit:
                break
    return picked[:limit]


def format_learned_examples_for_prompt(
    examples: list[LearnedAnswer],
    max_chars: int = 4000,
) -> str:
    """Formatteer goedgekeurde voorbeelden als promptcontext (geanonimiseerde tekst)."""
    if not examples:
        return ""
    header = (
        "--- Extra standaardantwoorden die de advocaat heeft goedgekeurd "
        "(referentie voor TOON en ARGUMENTATIE — de tekst is al geanonimiseerd; "
        "neem GEEN concrete namen, bedragen of datums over) ---"
    )
    parts = [header]
    chars = len(header)
    for i, ex in enumerate(examples, 1):
        text = ex.anonymized_body or ex.body
        block = f"\n[Voorbeeld {i}]\n{text}"
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
    for ex in examples:
        ex.use_count = (ex.use_count or 0) + 1
    return format_learned_examples_for_prompt(examples, max_chars=max_chars)


# ── Kandidaten vangen (backfill) ──────────────────────────────────────────────


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _email_body_text(email: SyncedEmail) -> str:
    """Platte tekst van een mail. Veel mails (Outlook/Graph) hebben ALLÉÉN een HTML-body
    — dan is body_text leeg en moeten we de tekst uit body_html halen."""
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
    """Vang KANDIDAAT-voorbeelden uit de verstuurde verweer-antwoorden.

    Per uitgaande mail op een verweer-dossier: knip de kern-weerlegging eruit, sla hem op
    als KANDIDAAT (met een anonimiseer-voorstel), tenzij het (a) een kale sommatie is
    zonder weerlegging, (b) een oningevuld 'XXX'-sjabloon, (c) te kort, of (d) vrijwel
    gelijk aan een bestaande standaardtekst (die kennen we al). Kandidaten voeden de AI
    NIET — dat gebeurt pas na goedkeuring in het 'Slim leren'-dashboard.

    Idempotent (dedup op source_synced_email_id). Geeft het aantal NIEUWE kandidaten terug.
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
        body_text = _email_body_text(email)
        # (b) oningevuld verweer-sjabloon.
        if " XXX " in body_text:
            continue
        # (a) geen inhoudelijke weerlegging → kale sommatie/aanmaning/overig.
        if not _looks_like_rebuttal(email.subject, body_text):
            continue
        category = await _category_for_outbound(
            db, tenant_id, email.case_id, email.email_date
        )
        if category not in LEARNABLE_CATEGORIES:
            continue
        core = extract_rebuttal(email.subject, body_text)
        if len(core) < 60:  # (c) te kort voor een zinvol voorbeeld
            continue
        ratio, best_key = _similarity_to_library(core)
        if ratio >= _LIBRARY_DUPLICATE_RATIO:  # (d) dit is een bestaande standaardtekst
            continue
        defense_type = best_key if ratio >= _LIBRARY_TYPE_RATIO else "overig"
        db.add(
            LearnedAnswer(
                tenant_id=tenant_id,
                category=category,
                body=core,
                anonymized_body=suggest_anonymization(core),
                defense_type=defense_type,
                language="nl",
                status=STATUS_CANDIDATE,
                is_active=False,
                source_synced_email_id=email.id,
                source_case_id=email.case_id,
            )
        )
        seen.add(email.id)
        added += 1

    if added:
        await db.flush()
    logger.info("Verweer-bibliotheek backfill tenant=%s: %d nieuwe kandidaten", tenant_id, added)
    return added


# ── Kandidaten beoordelen (goedkeuren / afwijzen) ─────────────────────────────


async def list_candidates(
    db: AsyncSession, tenant_id: uuid.UUID
) -> list[LearnedAnswer]:
    """Kandidaten die op beoordeling wachten (nieuwste eerst)."""
    return list(
        (
            await db.execute(
                select(LearnedAnswer)
                .where(
                    LearnedAnswer.tenant_id == tenant_id,
                    LearnedAnswer.status == STATUS_CANDIDATE,
                )
                .order_by(LearnedAnswer.created_at.desc())
            )
        ).scalars().all()
    )


async def approve_candidate(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    candidate_id: uuid.UUID,
    *,
    anonymized_body: str,
    defense_type: str | None = None,
) -> LearnedAnswer | None:
    """Keur een kandidaat goed met de (bevestigde/bewerkte) geanonimiseerde tekst.

    Pas ná deze stap voedt het voorbeeld de AI. Geeft None als de kandidaat niet bestaat.
    """
    row = (
        await db.execute(
            select(LearnedAnswer).where(
                LearnedAnswer.tenant_id == tenant_id,
                LearnedAnswer.id == candidate_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    row.anonymized_body = (anonymized_body or "").strip() or row.anonymized_body or row.body
    if defense_type:
        row.defense_type = defense_type
    row.status = STATUS_APPROVED
    row.is_active = True
    row.reviewed_at = datetime.now(UTC)
    await db.flush()
    return row


async def reject_candidate(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    candidate_id: uuid.UUID,
) -> bool:
    """Wijs een kandidaat af (voedt de AI nooit). True als er iets is gewijzigd."""
    row = (
        await db.execute(
            select(LearnedAnswer).where(
                LearnedAnswer.tenant_id == tenant_id,
                LearnedAnswer.id == candidate_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return False
    row.status = STATUS_REJECTED
    row.is_active = False
    row.reviewed_at = datetime.now(UTC)
    await db.flush()
    return True


# ── Dashboard-statistieken (edit-rate + leer-stats) ──────────────────────────


def _similarity(a: str, b: str) -> float:
    """Gelijkenis 0..1 tussen twee teksten (1 = identiek)."""
    return difflib.SequenceMatcher(None, a or "", b or "").ratio()


async def get_learning_stats(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Statistieken voor het kwaliteits-dashboard.

    - edit_rate: van recent verzonden concepten, hoeveel (bijna) ongewijzigd de deur uit
      gingen (AI-versie vs. wat Lisanne echt verstuurde).
    - candidates / approved: aantal kandidaten dat op review wacht en aantal goedgekeurd.
    - per_category: aantal GOEDGEKEURDE voorbeelden per categorie.
    - top_examples: meest hergebruikte goedgekeurde antwoorden.
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

    # 2. Kandidaat- en goedgekeurd-tellingen.
    status_rows = (
        await db.execute(
            select(LearnedAnswer.status, func.count())
            .where(LearnedAnswer.tenant_id == tenant_id)
            .group_by(LearnedAnswer.status)
        )
    ).all()
    by_status = {status: count for status, count in status_rows}
    candidates = by_status.get(STATUS_CANDIDATE, 0)

    # 3. Goedgekeurde voorbeelden per categorie.
    per_cat_rows = (
        await db.execute(
            select(LearnedAnswer.category, func.count())
            .where(
                LearnedAnswer.tenant_id == tenant_id,
                LearnedAnswer.status == STATUS_APPROVED,
            )
            .group_by(LearnedAnswer.category)
        )
    ).all()
    per_category = {cat: count for cat, count in per_cat_rows}
    total_examples = sum(per_category.values())

    # 4. Meest hergebruikte goedgekeurde antwoorden.
    top = (
        await db.execute(
            select(LearnedAnswer)
            .where(
                LearnedAnswer.tenant_id == tenant_id,
                LearnedAnswer.status == STATUS_APPROVED,
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
            "preview": (ex.anonymized_body or ex.body or "")[:160],
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
        "candidates": candidates,
        "total_examples": total_examples,
        "per_category": per_category,
        "top_examples": top_examples,
    }
