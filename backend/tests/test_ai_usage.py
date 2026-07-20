"""S230 — verbruiksregistratie per AI-aanroep (kostenvraag Arsalan).

De kostenformule is het niet-triviale deel: tokens × prijs per model, met
cache-lezen op 0,1× en cache-schrijven op 1,25× de inputprijs. De bedragen
hieronder zijn met de hand nagerekend tegen de officiële prijstabel
(Sonnet 4.6: $3/$15 per 1M; Haiku 4.5: $1/$5 per 1M).
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.ai_agent.kimi_client import _record_usage, estimate_cost_usd
from app.ai_agent.models import AIUsage


def test_kosten_sonnet_met_de_hand_nagerekend():
    # 10.000 in × $3/M = $0,03 · 2.000 uit × $15/M = $0,03 → $0,06
    assert estimate_cost_usd("claude-sonnet-4-6", 10_000, 2_000) == Decimal("0.060000")


def test_kosten_haiku_met_cache():
    # 1.000 in × $1/M = 0,001 · 500 uit × $5/M = 0,0025
    # 10.000 cache-read × $1/M × 0,1 = 0,001 · 4.000 cache-write × $1/M × 1,25 = 0,005
    kosten = estimate_cost_usd("claude-haiku-4-5", 1_000, 500, 10_000, 4_000)
    assert kosten == Decimal("0.009500")


def test_onbekend_model_geeft_none():
    """Prijs onbekend → geen gok; tokens worden wél geregistreerd (cost NULL)."""
    assert estimate_cost_usd("claude-toekomst-9", 1000, 1000) is None


@pytest.mark.asyncio
async def test_record_usage_overleeft_db_fout(monkeypatch, caplog):
    """Meten mag een AI-aanroep nooit laten falen: DB stuk → alleen een logregel."""
    import app.database as database

    def _boom():
        raise RuntimeError("db weg")

    monkeypatch.setattr(database, "async_session", _boom)
    response = SimpleNamespace(usage=SimpleNamespace(input_tokens=10, output_tokens=5))
    await _record_usage("test", "claude-haiku-4-5", response)  # mag niet raisen


@pytest.mark.asyncio
async def test_record_usage_zonder_usage_doet_niets():
    await _record_usage("test", "claude-haiku-4-5", SimpleNamespace())  # geen usage-attr


@pytest.mark.asyncio
async def test_record_usage_schrijft_regel(db):
    """Eén aanroep → één regel met tokens en kosten. Het echte schrijfpad
    gebruikt zijn eigen sessie; hier volstaat het model + de formule samen."""
    regel = AIUsage(
        purpose="extract_classification",
        model="claude-haiku-4-5",
        input_tokens=1_000,
        output_tokens=500,
        cache_read_tokens=0,
        cache_write_tokens=0,
        cost_usd=estimate_cost_usd("claude-haiku-4-5", 1_000, 500),
    )
    db.add(regel)
    await db.flush()
    assert regel.id is not None
    assert regel.cost_usd == Decimal("0.003500")
