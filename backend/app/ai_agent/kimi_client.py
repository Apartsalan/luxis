"""AI extraction clients — model routing per taak.

INTAKE / CLASSIFICATIE / INVOICE (high volume, pattern matching):
  Gemini Flash 2.5 → Kimi 2.5 → Claude Haiku 4.5
  Goedkoop, snel, JSON-output betrouwbaar via tool_use.

DRAFT GENERATIE (juridische kwaliteit kritiek — emails naar wederpartij):
  Claude Sonnet 4.6 → Gemini Flash 2.5 → Claude Haiku 4.5
  Sonnet excelleert in Nederlandse juridische taal + AV-citaten.
  Bij Verweer beantwoorden + AV-PDF beschikbaar: native PDF input
  (lost truncatie-probleem op, Sonnet leest PDF direct).

AI-TECH-03: Tool_use forced as structured output → guarantees valid JSON.
"""

import json
import logging
from typing import Any

import anthropic
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

KIMI_API_BASE = "https://api.moonshot.ai/v1"
KIMI_MODEL = "moonshot-v1-auto"

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-2.5-flash"

CLAUDE_SONNET_MODEL = "claude-sonnet-4-5-20250514"
CLAUDE_HAIKU_MODEL = "claude-haiku-4-5"

# Kosten per 1M tokens (Sonnet 4.5) — voor cost-logging per draft
SONNET_INPUT_PRICE_PER_M = 3.0
SONNET_OUTPUT_PRICE_PER_M = 15.0

# ── JSON schemas for structured output (tool_use) ────────────────────────────

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
    },
    "required": ["category", "confidence", "reasoning", "suggested_action"],
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
}

INVOICE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "debtor_name": {"type": ["string", "null"]},
        "debtor_type": {"type": "string", "enum": ["company", "person"]},
        "debtor_address": {"type": ["string", "null"]},
        "debtor_postcode": {"type": ["string", "null"]},
        "debtor_city": {"type": ["string", "null"]},
        "debtor_kvk": {"type": ["string", "null"]},
        "debtor_email": {"type": ["string", "null"]},
        "creditor_name": {"type": ["string", "null"]},
        "creditor_btw": {"type": ["string", "null"]},
        "invoice_number": {"type": ["string", "null"]},
        "invoice_date": {"type": ["string", "null"]},
        "due_date": {"type": ["string", "null"]},
        "principal_amount": {"type": ["number", "null"]},
        "description": {"type": ["string", "null"]},
        "confidence": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "number"},
                "debtor_type": {"type": "number"},
                "debtor_address": {"type": "number"},
                "debtor_postcode": {"type": "number"},
                "debtor_city": {"type": "number"},
                "debtor_kvk": {"type": "number"},
                "debtor_email": {"type": "number"},
                "creditor_name": {"type": "number"},
                "creditor_btw": {"type": "number"},
                "invoice_number": {"type": "number"},
                "invoice_date": {"type": "number"},
                "due_date": {"type": "number"},
                "principal_amount": {"type": "number"},
                "description": {"type": "number"},
            },
        },
    },
    "required": ["debtor_name", "debtor_type", "confidence"],
}

# Map system prompts to their schemas (matched by first line keyword)
_PROMPT_SCHEMA_MAP = {
    "classificeert": ("extract_classification", CLASSIFICATION_SCHEMA),
    "incassodossier willen aanmaken": ("extract_intake", INTAKE_SCHEMA),
    "pdf-facturen": ("extract_invoice", INVOICE_SCHEMA),
    "email-assistent": ("generate_incasso_email", INCASSO_DRAFT_SCHEMA),
}


def _detect_schema(system_prompt: str) -> tuple[str, dict[str, Any]] | None:
    """Detect which JSON schema to use based on system prompt content."""
    prompt_lower = system_prompt.lower()
    for keyword, schema_pair in _PROMPT_SCHEMA_MAP.items():
        if keyword.lower() in prompt_lower:
            return schema_pair
    return None


async def _call_gemini(system_prompt: str, user_message: str) -> dict:
    """Call Google Gemini Flash API met retry-on-503.

    Uses the generateContent endpoint met JSON response.
    Gemini geeft soms transient 503 — 1x retry na 2s lost dat meestal op.
    """
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    url = f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}:generateContent?key={settings.gemini_api_key}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_message}"}]},
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "maxOutputTokens": 16384,
        },
    }

    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url, headers={"Content-Type": "application/json"}, json=payload
                )
                response.raise_for_status()
                data = response.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return _parse_json(raw_text)
        except httpx.HTTPStatusError as e:
            last_exc = e
            if e.response.status_code in (503, 429, 500) and attempt == 0:
                logger.warning("Gemini %s — retry in 2s", e.response.status_code)
                import asyncio as _asyncio
                await _asyncio.sleep(2)
                continue
            raise
    raise last_exc  # type: ignore[misc]


async def _call_kimi(system_prompt: str, user_message: str) -> dict:
    """Call Moonshot/Kimi API (OpenAI-compatible format).

    Raises ValueError if API key not set or response is invalid.
    """
    if not settings.kimi_api_key:
        raise ValueError("KIMI_API_KEY is not configured")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{KIMI_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.kimi_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": KIMI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
                "max_tokens": 16384,
            },
        )
        response.raise_for_status()
        data = response.json()

    raw_text = data["choices"][0]["message"]["content"].strip()
    return _parse_json(raw_text)


async def _call_haiku(system_prompt: str, user_message: str) -> dict:
    """Call Claude Haiku (or Sonnet bij complexe schemas) als fallback met tool_use.

    AI-TECH-03: Uses tool_use with forced tool_choice to guarantee valid JSON.
    Falls back to plain text + _parse_json if schema detection fails.
    Voor incasso-draft generatie wordt Sonnet 4.5 gebruikt — Haiku kopieert
    HTML-sjablonen letterlijk in plaats van placeholders te vervangen.
    """
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    schema_info = _detect_schema(system_prompt)
    # Draft-generatie heeft een complexer prompt + grote HTML-output — Sonnet hier
    is_draft = bool(schema_info and schema_info[0] == "generate_incasso_email")
    model_name = "claude-sonnet-4-5-20250514" if is_draft else "claude-haiku-4-5"

    if schema_info:
        tool_name, schema = schema_info
        response = await client.messages.create(
            model=model_name,
            max_tokens=16384,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            tools=[
                {
                    "name": tool_name,
                    "description": "Extract structured data from the input.",
                    "input_schema": schema,
                }
            ],
            tool_choice={"type": "tool", "name": tool_name},
        )
        # With forced tool_choice, the response is guaranteed to be a tool_use block
        for block in response.content:
            if block.type == "tool_use":
                logger.info("Haiku structured output: tool_use block received")
                return block.input  # type: ignore[return-value]
        # Shouldn't happen with forced tool_choice, but fallback
        logger.warning("Haiku: no tool_use block in response, falling back to text parse")

    # Fallback: plain text response (no schema detected or tool_use failed)
    response = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    raw_text = response.content[0].text.strip()
    return _parse_json(raw_text)


async def _call_sonnet(system_prompt: str, user_message: str) -> dict:
    """Call Claude Sonnet 4.5 met tool_use voor structured JSON output.

    Gebruikt voor incasso-draft generatie — Nederlandse juridische taal +
    AV-citaten kwaliteit beter dan Gemini Flash (Harvey BigLaw Bench).
    Logs token-usage voor cost-monitoring per draft.
    """
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    schema_info = _detect_schema(system_prompt)

    if schema_info:
        tool_name, schema = schema_info
        response = await client.messages.create(
            model=CLAUDE_SONNET_MODEL,
            max_tokens=16384,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            tools=[
                {
                    "name": tool_name,
                    "description": "Generate structured email draft.",
                    "input_schema": schema,
                }
            ],
            tool_choice={"type": "tool", "name": tool_name},
        )
        _log_sonnet_cost(response, "Sonnet draft")
        for block in response.content:
            if block.type == "tool_use":
                return block.input  # type: ignore[return-value]
        logger.warning("Sonnet: no tool_use block in response, fallback to text")

    # Fallback: plain text JSON
    response = await client.messages.create(
        model=CLAUDE_SONNET_MODEL,
        max_tokens=16384,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    _log_sonnet_cost(response, "Sonnet text-fallback")
    raw_text = response.content[0].text.strip()
    return _parse_json(raw_text)


def _log_sonnet_cost(response: Any, label: str) -> None:
    """Log Sonnet token-usage en geschatte kosten per call."""
    usage = getattr(response, "usage", None)
    if not usage:
        return
    in_tokens = getattr(usage, "input_tokens", 0)
    out_tokens = getattr(usage, "output_tokens", 0)
    cost_usd = (
        in_tokens * SONNET_INPUT_PRICE_PER_M / 1_000_000
        + out_tokens * SONNET_OUTPUT_PRICE_PER_M / 1_000_000
    )
    logger.info(
        "%s: tokens in=%d out=%d cost=$%.4f",
        label, in_tokens, out_tokens, cost_usd,
    )


def _parse_json(raw_text: str) -> dict:
    """Parse JSON from AI response, handling markdown code blocks."""
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        if "```" in raw_text:
            json_part = raw_text.split("```")[1]
            if json_part.startswith("json"):
                json_part = json_part[4:]
            return json.loads(json_part.strip())
        raise ValueError(f"AI returned invalid JSON: {raw_text[:200]}")


async def call_claude_with_pdf(
    system_prompt: str,
    user_message: str,
    pdf_path: str,
    model: str = "claude-sonnet-4-5-20250514",
) -> dict:
    """AI-TECH-02: Send a PDF directly to Claude for deep analysis.

    Uses Claude's native PDF understanding (base64-encoded document block).
    Intended for heavy analysis (contract disputes, complex documents) — not
    for daily high-volume work which uses Kimi.

    Args:
        system_prompt: System instructions for the analysis.
        user_message: User message / context about what to analyze.
        pdf_path: Absolute path to the PDF file.
        model: Claude model to use (default: Sonnet for cost/quality balance).

    Returns:
        Parsed JSON dict from Claude's response.
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

    # Try structured output first
    schema_info = _detect_schema(system_prompt)

    messages = [
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
    ]

    if schema_info:
        tool_name, schema = schema_info
        response = await client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            messages=messages,
            tools=[
                {
                    "name": tool_name,
                    "description": "Extract structured data from the document.",
                    "input_schema": schema,
                }
            ],
            tool_choice={"type": "tool", "name": tool_name},
        )
        for block in response.content:
            if block.type == "tool_use":
                return block.input  # type: ignore[return-value]

    # Fallback: plain text
    response = await client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=messages,
    )
    raw_text = response.content[0].text.strip()
    return _parse_json(raw_text)


async def call_intake_ai(system_prompt: str, user_message: str) -> tuple[dict, str]:
    """Call AI for intake extraction. Returns (parsed_result, model_name).

    Priority: Gemini Flash 2.5 → Kimi 2.5 → Claude Haiku 4.5.
    """
    # Try Gemini first (best instruction following)
    if settings.gemini_api_key:
        try:
            result = await _call_gemini(system_prompt, user_message)
            logger.info("Intake AI: Gemini Flash extraction successful")
            return result, "gemini-2.5-flash"
        except Exception as e:
            logger.warning("Intake AI: Gemini failed, trying Kimi: %s", e)

    # Fallback to Kimi
    if settings.kimi_api_key:
        try:
            result = await _call_kimi(system_prompt, user_message)
            logger.info("Intake AI: Kimi extraction successful")
            return result, "kimi-2.5"
        except Exception as e:
            logger.warning("Intake AI: Kimi failed, falling back to Haiku: %s", e)

    # Final fallback to Anthropic (Sonnet voor draft, Haiku voor rest)
    try:
        result = await _call_haiku(system_prompt, user_message)
        schema_info = _detect_schema(system_prompt)
        is_draft = bool(schema_info and schema_info[0] == "generate_incasso_email")
        model_name = "claude-sonnet-4-5" if is_draft else "claude-haiku-4-5"
        logger.info("Intake AI: %s extraction successful", model_name)
        return result, model_name
    except Exception as e:
        logger.error("Intake AI: all providers failed: %s", e)
        raise ValueError(f"All AI providers failed: {e}") from e


async def call_draft_ai(
    system_prompt: str,
    user_message: str,
    av_pdf_path: str | None = None,
) -> tuple[dict, str]:
    """Call AI for incasso draft generation. Sonnet primary for legal quality.

    Priority: Claude Sonnet 4.6 → Gemini Flash 2.5 → Claude Haiku 4.5.
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
            )
            logger.info("Draft AI: Sonnet+PDF generation successful")
            return result, "claude-sonnet-4-5+pdf"
        except Exception as e:
            logger.warning(
                "Draft AI: Sonnet+PDF failed, fallback naar plain Sonnet: %s", e
            )

    # Sonnet primary (geen PDF, of PDF-pad gefaald)
    if settings.anthropic_api_key:
        try:
            result = await _call_sonnet(system_prompt, user_message)
            logger.info("Draft AI: Sonnet generation successful")
            return result, "claude-sonnet-4-5"
        except Exception as e:
            logger.warning("Draft AI: Sonnet failed, fallback naar Gemini: %s", e)

    # Gemini fallback
    if settings.gemini_api_key:
        try:
            result = await _call_gemini(system_prompt, user_message)
            logger.info("Draft AI: Gemini fallback successful")
            return result, "gemini-2.5-flash"
        except Exception as e:
            logger.warning(
                "Draft AI: Gemini failed, last-resort Haiku: %s", e
            )

    # Last resort
    try:
        result = await _call_haiku(system_prompt, user_message)
        logger.info("Draft AI: Haiku last-resort successful")
        return result, CLAUDE_HAIKU_MODEL
    except Exception as e:
        logger.error("Draft AI: all providers failed: %s", e)
        raise ValueError(f"All AI providers failed: {e}") from e
