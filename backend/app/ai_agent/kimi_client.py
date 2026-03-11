"""Kimi/Moonshot AI client — primary extraction model with Haiku fallback.

Kimi 2.5 (moonshot-v1-auto): ~$0.001/call via OpenAI-compatible API.
Claude Haiku 4.5: ~$0.005/call fallback via Anthropic API.
"""

import json
import logging

import anthropic
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

KIMI_API_BASE = "https://api.moonshot.cn/v1"
KIMI_MODEL = "moonshot-v1-auto"


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
            },
        )
        response.raise_for_status()
        data = response.json()

    raw_text = data["choices"][0]["message"]["content"].strip()
    return _parse_json(raw_text)


async def _call_haiku(system_prompt: str, user_message: str) -> dict:
    """Call Claude Haiku as fallback.

    Raises ValueError if API key not set or response is invalid.
    """
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text.strip()
    return _parse_json(raw_text)


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


async def call_intake_ai(system_prompt: str, user_message: str) -> tuple[dict, str]:
    """Call AI for intake extraction. Returns (parsed_result, model_name).

    Tries Kimi 2.5 first (cheaper), falls back to Claude Haiku.
    """
    # Try Kimi first
    if settings.kimi_api_key:
        try:
            result = await _call_kimi(system_prompt, user_message)
            logger.info("Intake AI: Kimi extraction successful")
            return result, "kimi-2.5"
        except Exception as e:
            logger.warning("Intake AI: Kimi failed, falling back to Haiku: %s", e)

    # Fallback to Haiku
    try:
        result = await _call_haiku(system_prompt, user_message)
        logger.info("Intake AI: Haiku extraction successful")
        return result, "claude-haiku-4-5"
    except Exception as e:
        logger.error("Intake AI: both Kimi and Haiku failed: %s", e)
        raise ValueError(f"All AI providers failed: {e}") from e
