"""Rente-bepaling uit de algemene voorwaarden (AV) van een cliënt lezen.

Principe (opdracht Arsalan, S177): Luxis houdt ALTIJD aan wat er in de AV van de
cliënt staat, tenzij wij het handmatig anders zetten. Deze module leest de
rente-afspraak uit de AV-PDF en levert een `TermsInterest` op. De gelezen waarde
wordt op de cliënt bewaard in aparte `terms_interest_*`-velden (nooit de handmatige
`default_*`-velden — die winnen altijd en mogen niet overschreven worden).

Aanpak: eerst een gerichte regex op de PDF-tekst (goedkoop, deterministisch); vindt
die niets, dan één Haiku-call als vangnet. Alle drie de huidige opdrachtgever-AV's
(Invorderingsbedrijf, Collect 1, Incassocenter) bevatten in artikel 13.3:
"2% per maand vanaf de vervaldag" — dat vangt de regex.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

# "... 2% per maand ..." / "1,5 % per jaar". Discriminant: alleen rente wordt "per
# maand/jaar" uitgedrukt — de incassokosten (15% van de vordering), kantoorkosten
# (6%) e.d. matchen bewust NIET (die staan zonder "per maand/jaar").
_RATE_RE = re.compile(
    r"(?P<rate>\d{1,2}(?:[.,]\d{1,2})?)\s*%\s*per\s*(?P<basis>maand|jaar)",
    re.IGNORECASE,
)
# Artikelnummer vlak vóór de rentebepaling, voor de zichtbare herkomst ("art. 13.3").
_ARTICLE_RE = re.compile(r"(?P<art>\d{1,2}\.\d{1,2})\.?\s*(?=[A-Z(])")


@dataclass
class TermsInterest:
    rate: Decimal              # bv. Decimal("2.00")
    basis: str                 # "monthly" | "yearly"
    compound: bool             # AV noemt zelden samengesteld → default enkelvoudig
    source: str                # zichtbare herkomst, bv. "artikel 13.3: 2% per maand"
    method: str                # "regex" | "ai"


def parse_interest_from_text(text: str) -> TermsInterest | None:
    """Zoek de rente-afspraak in AV-tekst. Puur, geen I/O — los testbaar."""
    m = _RATE_RE.search(text)
    if not m:
        return None
    try:
        rate = Decimal(m.group("rate").replace(",", "."))
    except InvalidOperation:
        return None
    if rate <= 0 or rate > 25:  # sanity: een maand-/jaartarief buiten (0,25] is verdacht
        return None
    basis = "monthly" if m.group("basis").lower() == "maand" else "yearly"

    # Artikelnummer: het dichtstbijzijnde "X.Y" links van de match (zelfde alinea).
    article = None
    window = text[max(0, m.start() - 600) : m.start()]
    arts = _ARTICLE_RE.findall(window)
    if arts:
        article = arts[-1]

    phrase = f"{m.group('rate').replace(',', '.')}% per {m.group('basis').lower()}"
    source = f"artikel {article}: {phrase}" if article else phrase
    return TermsInterest(rate=rate, basis=basis, compound=False, source=source, method="regex")


def _extract_pdf_text(pdf_path: str) -> str:
    """AV-PDF → platte tekst (pymupdf)."""
    import fitz  # pymupdf, al aanwezig via pymupdf4llm

    with fitz.open(pdf_path) as doc:
        return "\n".join(page.get_text() for page in doc)


async def _ai_fallback(text: str) -> TermsInterest | None:
    """Eén Haiku-call als de regex niets vond. Structured output, best-effort."""
    from app.ai_agent.kimi_client import CLAUDE_HAIKU_MODEL
    from app.config import settings

    if not settings.anthropic_api_key:
        return None
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    schema = {
        "type": "object",
        "properties": {
            "found": {"type": "boolean", "description": "Staat er een rentetarief in?"},
            "rate": {"type": "number", "description": "Het percentage, bv. 2"},
            "basis": {"type": "string", "enum": ["monthly", "yearly"]},
            "compound": {"type": "boolean", "description": "Samengesteld? Bijna altijd false."},
            "source": {"type": "string", "description": "Korte herkomst, bv. 'artikel 13.3'"},
        },
        "required": ["found"],
    }
    try:
        resp = await client.messages.create(
            model=CLAUDE_HAIKU_MODEL,
            max_tokens=512,
            system=(
                "Je leest Nederlandse algemene voorwaarden van een incassobureau. Vind de "
                "rente/vertragingsrente die de cliënt of debiteur bij verzuim verschuldigd is "
                "(vaak 'X% per maand vanaf de vervaldag'). NIET de incassokosten (15%), "
                "kantoorkosten (6%) of boetes. Vind je geen rentetarief, zet found=false."
            ),
            messages=[{"role": "user", "content": text[:12000]}],
            tools=[{"name": "rente", "description": "Rente uit de AV", "input_schema": schema}],
            tool_choice={"type": "tool", "name": "rente"},
        )
    except Exception as e:  # noqa: BLE001 — vangnet mag nooit de upload breken
        logger.warning("AI-rente-extractie mislukt: %s", e)
        return None

    for block in resp.content:
        if block.type == "tool_use":
            d = block.input  # type: ignore[assignment]
            if not d.get("found") or d.get("rate") in (None, 0):
                return None
            try:
                rate = Decimal(str(d["rate"]))
            except (InvalidOperation, KeyError, TypeError):
                return None
            if rate <= 0 or rate > 25:
                return None
            return TermsInterest(
                rate=rate,
                basis="monthly" if d.get("basis") == "monthly" else "yearly",
                compound=bool(d.get("compound", False)),
                source=(d.get("source") or f"{rate}% per {d.get('basis', 'jaar')}")[:200],
                method="ai",
            )
    return None


async def read_terms_interest(pdf_path: str, use_ai_fallback: bool = True) -> TermsInterest | None:
    """Lees de rente uit een AV-PDF: eerst regex, dan (optioneel) Haiku-vangnet."""
    try:
        text = _extract_pdf_text(pdf_path)
    except Exception as e:  # noqa: BLE001
        logger.warning("AV-tekst uitlezen mislukt (%s): %s", pdf_path, e)
        return None
    result = parse_interest_from_text(text)
    if result is not None:
        return result
    if use_ai_fallback:
        return await _ai_fallback(text)
    return None
