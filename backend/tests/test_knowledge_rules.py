"""Wachters voor juridische kennisregels (S248).

Zwaartepunt: de harde toepasbaarheids-poort (ontwerp §4 — een zakelijke regel mag NOOIT
een consument-concept voeden). De injectie in alle 3 de draft-paden loopt via
`build_knowledge_rules_text`; de poort zit in die gedeelde functie, dus deze wachters
dekken het foutSOORT 'regel verkeerd toegepast' voor álle routes tegelijk (breed-testen:
één punt, alle callers).
"""

import pytest

from app.ai_agent import knowledge_rules as kr


async def _approved_rule(db, tenant_id, *, defense_type, applies_to, body, basis=None):
    rule = await kr.create_rule(
        db, tenant_id,
        defense_type=defense_type, applies_to=applies_to,
        title=f"regel-{defense_type}-{applies_to}",
        rebuttal_body=body, legal_basis=basis,
    )
    await kr.approve_rule(db, tenant_id, rule.id)
    await db.flush()
    return rule


@pytest.mark.asyncio
async def test_gate_business_rule_never_on_consumer(db, test_tenant):
    """§4-doemscenario: art. 6:235-regel voor niet-consumenten mag niet op een consument."""
    await _approved_rule(
        db, test_tenant.id,
        defense_type="av_toepasselijkheid", applies_to="zakelijk",
        body="Als niet-consument kan de wederpartij de algemene voorwaarden niet vernietigen.",
        basis="art. 6:235 lid 1 BW",
    )
    # b2b → wél
    text_b2b = await kr.build_knowledge_rules_text(db, test_tenant.id, "av_toepasselijkheid", "b2b")
    assert "6:235" in text_b2b
    # b2c → NIET (de poort — een consument mág de AV juist wél vernietigen)
    text_b2c = await kr.build_knowledge_rules_text(db, test_tenant.id, "av_toepasselijkheid", "b2c")
    assert text_b2c == ""
    # onbekend debiteur-type → ook niet (fail closed)
    text_none = await kr.build_knowledge_rules_text(db, test_tenant.id, "av_toepasselijkheid", None)
    assert text_none == ""


@pytest.mark.asyncio
async def test_gate_defense_type_must_match(db, test_tenant):
    """Een regel voedt alleen bij een matchend verweer-type."""
    await _approved_rule(
        db, test_tenant.id,
        defense_type="av_toepasselijkheid", applies_to="alle",
        body="Standaard-weerlegging voor toepasselijkheid van de voorwaarden.",
    )
    match = await kr.build_knowledge_rules_text(db, test_tenant.id, "av_toepasselijkheid", "b2b")
    assert "voorwaarden" in match
    other = await kr.build_knowledge_rules_text(db, test_tenant.id, "reeds_betaald_verrekening", "b2b")
    assert other == ""
    # geen type / 'overig' → niets injecteren
    assert await kr.build_knowledge_rules_text(db, test_tenant.id, None, "b2b") == ""
    assert await kr.build_knowledge_rules_text(db, test_tenant.id, "overig", "b2b") == ""


@pytest.mark.asyncio
async def test_candidate_and_rejected_not_injected(db, test_tenant):
    """Alleen GOEDGEKEURDE + actieve regels voeden de AI — kandidaat/afgewezen nooit."""
    rule = await kr.create_rule(
        db, test_tenant.id,
        defense_type="kosten_rente_hoogte", applies_to="alle",
        title="kosten-regel", rebuttal_body="De incassokosten volgen de wettelijke staffel.",
    )
    await db.flush()
    # kandidaat → niet
    assert await kr.build_knowledge_rules_text(db, test_tenant.id, "kosten_rente_hoogte", "b2b") == ""
    # goedgekeurd → wel
    await kr.approve_rule(db, test_tenant.id, rule.id)
    await db.flush()
    assert "staffel" in await kr.build_knowledge_rules_text(db, test_tenant.id, "kosten_rente_hoogte", "b2b")
    # weer afgewezen (goedkeuring ingetrokken) → niet meer
    await kr.reject_rule(db, test_tenant.id, rule.id)
    await db.flush()
    assert await kr.build_knowledge_rules_text(db, test_tenant.id, "kosten_rente_hoogte", "b2b") == ""


@pytest.mark.asyncio
async def test_consumer_and_all_scopes(db, test_tenant):
    """applies_to='consument' → alleen b2c; 'alle' → beide."""
    await _approved_rule(
        db, test_tenant.id,
        defense_type="betwisting_ongemotiveerd", applies_to="consument",
        body="Bij een consument geldt deze specifieke weerlegging.",
    )
    assert "consument" in await kr.build_knowledge_rules_text(db, test_tenant.id, "betwisting_ongemotiveerd", "b2c")
    assert await kr.build_knowledge_rules_text(db, test_tenant.id, "betwisting_ongemotiveerd", "b2b") == ""


@pytest.mark.asyncio
async def test_validation_rejects_bad_fields(db, test_tenant):
    """Een onbekend type of te korte weerlegging wordt geweigerd (endpoint-poort)."""
    assert kr.validate_rule_fields(
        defense_type="av_toepasselijkheid", applies_to="zakelijk",
        title="ok", rebuttal_body="x" * 25,
    ) is None
    assert kr.validate_rule_fields(
        defense_type="bestaat_niet", applies_to="alle", title="t", rebuttal_body="x" * 25,
    ) is not None
    assert kr.validate_rule_fields(
        defense_type="av_toepasselijkheid", applies_to="onzin", title="t", rebuttal_body="x" * 25,
    ) is not None
    assert kr.validate_rule_fields(
        defense_type="av_toepasselijkheid", applies_to="alle", title="t", rebuttal_body="kort",
    ) is not None
