"""AI extraction clients — model routing per taak (100% Claude sinds S159).

Historische bestandsnaam (`kimi_client`): de fallback-keten liep ooit via
Gemini Flash → Kimi (Moonshot) → Claude. Sinds S159 zijn Kimi en Gemini
volledig verwijderd — debiteur-PII mag niet naar Moonshot (China, geen
EU-verwerkersovereenkomst) of de gratis Gemini-tier (AVG-blocker B1, zie
docs/research/readiness-audit.md). Alle routes draaien nu uitsluitend op Claude.

INTAKE / CLASSIFICATIE / INVOICE (high volume, pattern matching):
  Claude Haiku 4.5 — goedkoop, snel.

DRAFT GENERATIE (juridische kwaliteit kritiek — emails naar wederpartij):
  Claude Sonnet 4.6 → Claude Haiku 4.5 (last-resort).
  Sonnet excelleert in Nederlandse juridische taal + AV-citaten.
  Bij Verweer beantwoorden + AV-PDF beschikbaar: native PDF input
  (lost truncatie-probleem op, Sonnet leest PDF direct).

S238: elke aanroeper geeft zijn JSON-schema EXPLICIET mee (schema= + purpose=).
De oude trefwoord-detectie op de prompttekst (_detect_schema) is verwijderd —
een gewijzigde promptzin kan de schema-koppeling niet meer stil breken.
Tekst-routes gebruiken native structured outputs (output_config.format,
GA voor Sonnet 4.6 + Haiku 4.5); de PDF-route houdt forced tool_use mét
strict=True omdat de docs structured outputs + document-input niet
garanderen (geverifieerd 22-7-2026, platform.claude.com structured-outputs).
"""

import json
import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

CLAUDE_SONNET_MODEL = "claude-sonnet-4-6"
CLAUDE_HAIKU_MODEL = "claude-haiku-4-5"

# Kosten per 1M tokens (USD) — bron: officiële Anthropic-prijstabel, 20-7-2026.
# Cache-lezen kost ~0,1× de inputprijs, cache-schrijven ~1,25× (5-min TTL).
# Decimal, geen float — huisregel financiële precisie (CLAUDE.md).
MODEL_PRICES_PER_M = {
    CLAUDE_SONNET_MODEL: (Decimal("3.00"), Decimal("15.00")),
    CLAUDE_HAIKU_MODEL: (Decimal("1.00"), Decimal("5.00")),
}
CACHE_READ_FACTOR = Decimal("0.1")
CACHE_WRITE_FACTOR = Decimal("1.25")
_SIX_PLACES = Decimal("0.000001")


def estimate_cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> Decimal | None:
    """Geschatte kosten van één aanroep; None als het model onbekend is."""
    prices = MODEL_PRICES_PER_M.get(model)
    if prices is None:
        return None
    in_price, out_price = prices
    kosten = (
        input_tokens * in_price
        + cache_read_tokens * in_price * CACHE_READ_FACTOR
        + cache_write_tokens * in_price * CACHE_WRITE_FACTOR
        + output_tokens * out_price
    ) / 1_000_000
    return kosten.quantize(_SIX_PLACES, rounding=ROUND_HALF_UP)


async def _record_usage(purpose: str, model: str, response: Any) -> None:
    """Schrijf één verbruiksregel naar ai_usage (S230, kostenvraag).

    Eigen sessie, fouten gedempt: meten mag een AI-aanroep nooit laten falen.
    Zelfde patroon als de scheduler-heartbeat (workflow/scheduler.py).
    """
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    in_tok = getattr(usage, "input_tokens", 0) or 0
    out_tok = getattr(usage, "output_tokens", 0) or 0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cost = estimate_cost_usd(model, in_tok, out_tok, cache_read, cache_write)
    logger.info(
        "AI usage: %s model=%s in=%d out=%d cache_r=%d cache_w=%d cost=$%s",
        purpose, model, in_tok, out_tok, cache_read, cache_write,
        f"{cost:.4f}" if cost is not None else "?",
    )
    try:
        # Volledige model-registry laden: in de app al gebeurd (no-op), maar in
        # losse scripts (testronde) faalt de mapper-configuratie anders op
        # relaties naar niet-geïmporteerde modellen (S230, zelfde valkuil als
        # scripts/ai/antwoord_testronde._load_goud).
        import app.main  # noqa: F401
        from app.ai_agent.models import AIUsage
        from app.database import async_session

        async with async_session() as session:
            session.add(
                AIUsage(
                    purpose=purpose[:50],
                    model=model[:50],
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    cache_read_tokens=cache_read,
                    cache_write_tokens=cache_write,
                    cost_usd=cost,
                )
            )
            await session.commit()
    except Exception:
        logger.exception("AI usage: registratie mislukt voor %s", purpose)

# ── JSON schemas voor structured output ──────────────────────────────────────
# Huisregel (S238): elk schema dekt EXACT de velden die zijn prompt vraagt —
# additionalProperties=false blokkeert alles daarbuiten. Wijzig je een
# prompt-JSON-instructie, wijzig dan hetzelfde schema mee.

CLASSIFICATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": [
                "belofte_tot_betaling",
                "betwisting",
                "betalingsregeling_verzoek",
                "beweert_betaald",
                "onvermogen",
                "juridisch_verweer",
                "ontvangstbevestiging",
                "niet_gerelateerd",
            ],
        },
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
        "sentiment": {
            "type": "string",
            "enum": ["meewerkend", "neutraal", "gefrustreerd", "boos", "wanhopig"],
        },
        "suggested_action": {
            "type": "string",
            "enum": [
                "wait_and_remind",
                "escalate",
                "send_template",
                "dismiss",
                "request_proof",
                "no_action",
            ],
        },
        "suggested_template_key": {"type": ["string", "null"]},
        "suggested_reminder_days": {"type": ["integer", "null"]},
        "promise_date": {"type": ["string", "null"]},
        "promise_amount": {"type": ["number", "null"]},
        "defense_type": {"type": ["string", "null"]},
    },
    "required": ["category", "confidence", "reasoning", "suggested_action"],
    "additionalProperties": False,
}

INTAKE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "debtor_name": {"type": ["string", "null"]},
        "debtor_email": {"type": ["string", "null"]},
        "debtor_kvk": {"type": ["string", "null"]},
        "debtor_address": {"type": ["string", "null"]},
        "debtor_city": {"type": ["string", "null"]},
        "debtor_postcode": {"type": ["string", "null"]},
        "debtor_type": {"type": "string", "enum": ["company", "person"]},
        "invoice_number": {"type": ["string", "null"]},
        "invoice_date": {"type": ["string", "null"]},
        "due_date": {"type": ["string", "null"]},
        "principal_amount": {"type": ["number", "null"]},
        "description": {"type": ["string", "null"]},
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
    },
    "required": ["debtor_name", "debtor_type", "confidence", "reasoning"],
    "additionalProperties": False,
}

INCASSO_DRAFT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "subject": {
            "type": "string",
            "description": "Gepersonaliseerde Betreft-regel voor de email.",
        },
        "body": {
            "type": "string",
            "description": "Volledige email-body als plain text. Gebruik \\n voor regelovergangen.",
        },
    },
    "required": ["subject", "body"],
    "additionalProperties": False,
}

# Alle velden die INVOICE_PARSE_SYSTEM_PROMPT vraagt (invoice_prompts.py) —
# 28 stuks; het confidence-object spiegelt dezelfde lijst.
_INVOICE_FIELDS: list[str] = [
    *(
        f"debtor_{f}"
        for f in (
            "name", "contact_person", "type", "address", "postcode", "city",
            "postal_address", "postal_postcode", "postal_city", "kvk", "email",
        )
    ),
    *(
        f"creditor_{f}"
        for f in (
            "name", "contact_person", "type", "address", "postcode", "city",
            "postal_address", "postal_postcode", "postal_city", "kvk", "btw", "email",
        )
    ),
    "invoice_number", "invoice_date", "due_date", "principal_amount", "description",
]

INVOICE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        **{f: {"type": ["string", "null"]} for f in _INVOICE_FIELDS},
        "debtor_type": {"type": "string", "enum": ["company", "person"]},
        "principal_amount": {"type": ["number", "null"]},
        "confidence": {
            "type": "object",
            "properties": {f: {"type": "number"} for f in _INVOICE_FIELDS},
            # Alles verplicht (velden zijn nullable): de structured-outputs-API
            # staat max 24 optionele velden per schema toe (live gemeten S238:
            # 54 optioneel → 400 "grammar compilation inefficient").
            "required": _INVOICE_FIELDS,
            "additionalProperties": False,
        },
    },
    "required": [*_INVOICE_FIELDS, "confidence"],
    "additionalProperties": False,
}


# Grammar-limieten van structured outputs / strict tool_use — live gemeten
# op de API (S238, 22-7-2026): 400 bij >24 optionele velden en 400 bij >16
# nullable/union-getypeerde velden. Past een schema daar niet in (alleen het
# factuurschema), dan valt de aanroep terug op niet-strict forced tool_use —
# het oude, in de praktijk bewezen gedrag, maar mét expliciet schema.
_GRAMMAR_MAX_OPTIONAL = 24
_GRAMMAR_MAX_UNIONS = 16


def _grammar_fits(schema: dict[str, Any]) -> bool:
    """Past dit schema binnen de grammar-limieten van structured outputs?"""
    optional = 0
    unions = 0

    def walk(node: Any) -> None:
        nonlocal optional, unions
        if isinstance(node, dict):
            if node.get("type") == "object":
                props = node.get("properties", {})
                required = set(node.get("required", []))
                optional += sum(1 for p in props if p not in required)
                for prop_schema in props.values():
                    if isinstance(prop_schema, dict) and (
                        isinstance(prop_schema.get("type"), list) or "anyOf" in prop_schema
                    ):
                        unions += 1
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema)
    return optional <= _GRAMMAR_MAX_OPTIONAL and unions <= _GRAMMAR_MAX_UNIONS


async def _call_structured(
    model: str,
    system_prompt: str,
    user_message: str,
    schema: dict[str, Any],
    purpose: str,
    max_tokens: int = 16384,
) -> dict:
    """Eén Claude-aanroep met gegarandeerd schema-gebonden JSON-resultaat.

    Primair native structured outputs (output_config.format) — de API
    garandeert dan een text-block met schema-geldige JSON. Past het schema
    niet binnen de grammar-limieten (zie _grammar_fits), dan forced tool_use
    zonder strict — zelfde resultaatvorm, iets zwakkere garantie.
    """
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = None
    if _grammar_fits(schema):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                output_config={"format": {"type": "json_schema", "schema": schema}},
            )
        except anthropic.BadRequestError as e:
            # Runtime-vangnet (S238-review): de grammar kan óók falen binnen de
            # limieten ("Grammar compilation timed out", live gezien op het
            # intake-schema). Elke 400 hier → forced tool_use, nooit hard stuk.
            logger.warning(
                "Structured output geweigerd (%s) — terugval op forced tool_use: %s",
                purpose, e,
            )
    else:
        logger.info(
            "Structured output via forced tool_use (%s): schema te groot voor grammar",
            purpose,
        )
    if response is None:
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            tools=[
                {
                    "name": purpose,
                    "description": "Extract structured data from the input.",
                    "input_schema": schema,
                }
            ],
            tool_choice={"type": "tool", "name": purpose},
        )
    await _record_usage(purpose, model, response)

    if response.stop_reason == "max_tokens":
        raise ValueError(f"AI output afgekapt op max_tokens ({purpose})")
    if response.stop_reason == "refusal":
        raise ValueError(f"AI weigerde de aanvraag ({purpose})")
    # Eerst tool_use (tool-pad kan een text-block vóór het resultaat zetten)
    for block in response.content:
        if block.type == "tool_use":
            return block.input  # type: ignore[return-value]
    for block in response.content:
        if block.type == "text":
            return json.loads(block.text)
    raise ValueError(f"AI gaf geen bruikbaar resultaat-block terug ({purpose})")


async def call_claude_with_pdf(
    system_prompt: str,
    user_message: str,
    pdf_path: str,
    model: str = CLAUDE_SONNET_MODEL,
    *,
    schema: dict[str, Any],
    purpose: str,
) -> dict:
    """AI-TECH-02: Send a PDF directly to Claude for deep analysis.

    Uses Claude's native PDF understanding (base64-encoded document block).
    Structured output via forced tool_use — de docs garanderen structured
    outputs (output_config) niet in combinatie met document-input, dus deze
    route houdt bewust de tool_use-vorm (S238). strict=True alléén als het
    schema binnen de grammar-limieten past (zie _grammar_fits).

    Args:
        system_prompt: System instructions for the analysis.
        user_message: User message / context about what to analyze.
        pdf_path: Absolute path to the PDF file.
        model: Claude model to use (default: Sonnet for cost/quality balance).
        schema: JSON-schema van het verwachte resultaat (verplicht, expliciet).
        purpose: Label voor ai_usage-registratie én de tool-naam.

    Returns:
        Parsed dict uit het tool_use-block.
    """
    import base64
    from pathlib import Path

    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise ValueError(f"PDF file not found: {pdf_path}")

    pdf_b64 = base64.standard_b64encode(pdf_file.read_bytes()).decode("ascii")
    file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
    logger.info("Claude PDF analysis: %s (%.1f MB), model=%s", pdf_file.name, file_size_mb, model)

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def _pdf_request(strict: bool):
        return await client.messages.create(
            model=model,
            max_tokens=16384,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64,
                            },
                        },
                        {"type": "text", "text": user_message},
                    ],
                }
            ],
            tools=[
                {
                    "name": purpose,
                    "description": "Extract structured data from the document.",
                    "strict": strict,
                    "input_schema": schema,
                }
            ],
            tool_choice={"type": "tool", "name": purpose},
        )

    if _grammar_fits(schema):
        try:
            response = await _pdf_request(strict=True)
        except anthropic.BadRequestError as e:
            # Zelfde vangnet als _call_structured: grammar-compilatie kan ook
            # binnen de limieten falen → één herkansing zonder strict.
            logger.warning(
                "Strict tool_use geweigerd (pdf_%s) — herkansing zonder strict: %s",
                purpose, e,
            )
            response = await _pdf_request(strict=False)
    else:
        response = await _pdf_request(strict=False)
    await _record_usage(f"pdf_{purpose}", model, response)
    for block in response.content:
        if block.type == "tool_use":
            return block.input  # type: ignore[return-value]
    raise ValueError(f"AI gaf geen tool_use-block terug (pdf_{purpose})")


async def call_intake_ai(
    system_prompt: str,
    user_message: str,
    *,
    schema: dict[str, Any],
    purpose: str,
    model: str = CLAUDE_HAIKU_MODEL,
) -> tuple[dict, str]:
    """Structured AI-aanroep voor extractie/classificatie/concepten.

    De aanroeper geeft zijn schema en purpose expliciet mee (S238) — geen
    trefwoord-detectie meer. Default-model Haiku (high volume); concept-routes
    geven zelf CLAUDE_SONNET_MODEL mee.

    Returns (parsed_result, model_name).
    """
    try:
        result = await _call_structured(model, system_prompt, user_message, schema, purpose)
        logger.info("Intake AI: %s extraction successful (%s)", model, purpose)
        return result, model
    except Exception as e:
        logger.error("Intake AI: Claude extraction failed (%s): %s", purpose, e)
        raise ValueError(f"AI provider failed: {e}") from e


async def call_draft_ai(
    system_prompt: str,
    user_message: str,
    av_pdf_path: str | None = None,
    *,
    schema: dict[str, Any],
    purpose: str,
) -> tuple[dict, str]:
    """Call AI for incasso draft generation. Claude-only (S159).

    Priority: Claude Sonnet 4.6 → Claude Haiku 4.5 (last-resort).
    Bij `av_pdf_path` gegeven: native Sonnet PDF input — leest AV-PDF direct
    zonder text-extract truncatie (voor Verweer beantwoorden met AV-citatie).

    Returns (parsed_result, model_name).
    """
    # PDF-pad: native Sonnet PDF voor AV-citaat accuracy
    if av_pdf_path and settings.anthropic_api_key:
        try:
            result = await call_claude_with_pdf(
                system_prompt, user_message, av_pdf_path,
                model=CLAUDE_SONNET_MODEL,
                schema=schema, purpose=purpose,
            )
            logger.info("Draft AI: Sonnet+PDF generation successful")
            return result, f"{CLAUDE_SONNET_MODEL}+pdf"
        except Exception as e:
            logger.warning(
                "Draft AI: Sonnet+PDF failed, fallback naar plain Sonnet: %s", e
            )

    # Sonnet primary (geen PDF, of PDF-pad gefaald)
    if settings.anthropic_api_key:
        try:
            result = await _call_structured(
                CLAUDE_SONNET_MODEL, system_prompt, user_message, schema, purpose
            )
            logger.info("Draft AI: Sonnet generation successful")
            return result, CLAUDE_SONNET_MODEL
        except Exception as e:
            logger.warning("Draft AI: Sonnet failed, last-resort Haiku: %s", e)

    # Last resort
    try:
        result = await _call_structured(
            CLAUDE_HAIKU_MODEL, system_prompt, user_message, schema, purpose
        )
        logger.info("Draft AI: Haiku last-resort successful")
        return result, CLAUDE_HAIKU_MODEL
    except Exception as e:
        logger.error("Draft AI: all providers failed: %s", e)
        raise ValueError(f"All AI providers failed: {e}") from e
