"""S238 — wachters voor de expliciete schema-koppeling van de AI-laag.

Foutsoort die deze wachters bewaken: een AI-aanroep die zijn schema stil
kwijtraakt of een schema dat ongeldig is voor native structured outputs.
De oude trefwoord-detectie (_detect_schema) brak zodra iemand een promptzin
wijzigde — dat kan nu structureel niet meer, en deze tests bewaken dat het
zo blijft:

1. schema/purpose zijn VERPLICHTE keyword-args op elke publieke AI-functie;
2. elk meegeleverd schema is geldig voor structured outputs
   (additionalProperties=false op élk object, required ⊆ properties);
3. elk veld dat een prompt in zijn JSON-instructie vraagt, bestaat in het
   bijbehorende schema — additionalProperties=false blokkeert anders stil
   precies dat veld (de intake-postal-les uit de S238-meting);
4. _call_structured stuurt output_config.format en parst het text-block.
"""

import inspect
import json
import re
from types import SimpleNamespace

import pytest

from app.ai_agent import kimi_client
from app.ai_agent.draft_service import CASE_DRAFT_SCHEMA, DRAFT_SYSTEM_PROMPT
from app.ai_agent.incasso_email_prompts import SYSTEM_PROMPT as INCASSO_EMAIL_SYSTEM_PROMPT
from app.ai_agent.intake_prompts import INTAKE_SYSTEM_PROMPT
from app.ai_agent.invoice_prompts import INVOICE_PARSE_SYSTEM_PROMPT
from app.ai_agent.kimi_client import (
    CLASSIFICATION_SCHEMA,
    INCASSO_DRAFT_SCHEMA,
    INTAKE_SCHEMA,
    INVOICE_SCHEMA,
    _call_structured,
    call_claude_with_pdf,
    call_draft_ai,
    call_intake_ai,
)
from app.ai_agent.prompts import CLASSIFICATION_SYSTEM_PROMPT
from app.ai_agent.unified_draft_service import _REPLY_PROMPT, UNIFIED_DRAFT_SCHEMA

ALL_SCHEMAS = {
    "classification": CLASSIFICATION_SCHEMA,
    "intake": INTAKE_SCHEMA,
    "incasso_draft": INCASSO_DRAFT_SCHEMA,
    "invoice": INVOICE_SCHEMA,
    "case_draft": CASE_DRAFT_SCHEMA,
    "unified_draft": UNIFIED_DRAFT_SCHEMA,
}


# ── 1. Verplichte expliciete schema-koppeling ──────────────────────────────

@pytest.mark.parametrize("func", [call_intake_ai, call_draft_ai, call_claude_with_pdf])
def test_schema_en_purpose_zijn_verplichte_keyword_args(func):
    sig = inspect.signature(func)
    for name in ("schema", "purpose"):
        param = sig.parameters[name]
        assert param.kind is inspect.Parameter.KEYWORD_ONLY
        assert param.default is inspect.Parameter.empty, (
            f"{func.__name__}.{name} mag geen default hebben — elke aanroeper "
            "geeft zijn schema expliciet mee (S238)"
        )


# ── 2. Schema-geldigheid voor structured outputs ───────────────────────────

def _walk_objects(node):
    """Yield elk object-schema in een (genest) JSON-schema."""
    if isinstance(node, dict):
        if node.get("type") == "object":
            yield node
        for value in node.values():
            yield from _walk_objects(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_objects(item)


@pytest.mark.parametrize("naam", sorted(ALL_SCHEMAS))
def test_schema_geldig_voor_structured_outputs(naam):
    schema = ALL_SCHEMAS[naam]
    objecten = list(_walk_objects(schema))
    assert objecten, f"{naam}: geen object-schema gevonden"
    for obj in objecten:
        assert obj.get("additionalProperties") is False, (
            f"{naam}: object mist additionalProperties=false — structured "
            "outputs weigert het schema dan"
        )
        props = set(obj.get("properties", {}))
        assert set(obj.get("required", [])) <= props, (
            f"{naam}: required bevat velden die niet in properties staan"
        )


# ── 3. Prompt ↔ schema in sync ─────────────────────────────────────────────

def _schema_property_names(schema) -> set[str]:
    names: set[str] = set()
    for obj in _walk_objects(schema):
        names |= set(obj.get("properties", {}))
    return names


_PROMPT_KEY_RE = re.compile(r'"([a-z_]+)"\s*:')

PROMPT_SCHEMA_PAIRS = {
    "classification": (CLASSIFICATION_SYSTEM_PROMPT, CLASSIFICATION_SCHEMA),
    "intake": (INTAKE_SYSTEM_PROMPT, INTAKE_SCHEMA),
    "invoice": (INVOICE_PARSE_SYSTEM_PROMPT, INVOICE_SCHEMA),
    "case_draft": (DRAFT_SYSTEM_PROMPT, CASE_DRAFT_SCHEMA),
    "unified_reply": (_REPLY_PROMPT, UNIFIED_DRAFT_SCHEMA),
    "incasso_draft": (INCASSO_EMAIL_SYSTEM_PROMPT, INCASSO_DRAFT_SCHEMA),
}


@pytest.mark.parametrize("naam", sorted(PROMPT_SCHEMA_PAIRS))
def test_prompt_json_velden_gedekt_door_schema(naam):
    prompt, schema = PROMPT_SCHEMA_PAIRS[naam]
    gevraagd = set(_PROMPT_KEY_RE.findall(prompt))
    assert gevraagd, f"{naam}: geen JSON-veldinstructie in de prompt gevonden"
    gedekt = _schema_property_names(schema)
    ontbreekt = gevraagd - gedekt
    assert not ontbreekt, (
        f"{naam}: prompt vraagt velden die het schema niet kent: {sorted(ontbreekt)} "
        "— additionalProperties=false zou ze stil wegfilteren"
    )


# ── 4. _call_structured request-vorm + parsing ─────────────────────────────

class _FakeMessages:
    def __init__(self, response):
        self._response = response
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return self._response


def _fake_anthropic(monkeypatch, response):
    fake = SimpleNamespace(messages=_FakeMessages(response))
    monkeypatch.setattr(kimi_client.anthropic, "AsyncAnthropic", lambda api_key: fake)
    monkeypatch.setattr(kimi_client.settings, "anthropic_api_key", "test-key")
    return fake


async def test_call_structured_stuurt_schema_en_parst_text_block(monkeypatch):
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text=json.dumps({"a": 1}))],
        stop_reason="end_turn",
        usage=None,
    )
    fake = _fake_anthropic(monkeypatch, response)
    schema = {"type": "object", "properties": {"a": {"type": "integer"}},
              "required": ["a"], "additionalProperties": False}

    result = await _call_structured("m", "sys", "user", schema, "test_purpose")

    assert result == {"a": 1}
    sent = fake.messages.kwargs
    assert sent["output_config"] == {"format": {"type": "json_schema", "schema": schema}}
    assert "tools" not in sent


async def test_call_structured_weigert_afgekapte_output(monkeypatch):
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text='{"a"')],
        stop_reason="max_tokens",
        usage=None,
    )
    _fake_anthropic(monkeypatch, response)

    with pytest.raises(ValueError, match="max_tokens"):
        await _call_structured("m", "sys", "user", {"type": "object"}, "test_purpose")
