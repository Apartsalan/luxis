"""Juridische kennisregels (S248) — curated proactieve kennis met een HARDE poort.

Anders dan `learned_answers` (empirisch, uit Lisanne's echte mail, met bronzaak): een
kennisregel is juridische kennis die Lisanne intikt — "déze standaard-stelling is onjuist,
dít is de weerlegging (art. X BW)". Deelt alleen de goedkeur-flow (kandidaat → goedgekeurd/
afgewezen), niet de knip-/dedup-machinerie.

Twee poorten bepalen of een goedgekeurde regel de verweer-prompt voedt:
1. `defense_type` matcht het type van de laatste inkomende (classificatie) — de bestaande
   13-type-woordenschat is de matchsleutel; nul nieuwe herken-machinerie.
2. `applies_to` klopt tegen `Case.debtor_type` — HARD in code, niet alleen in de tekst.
   Dit doodt het doemscenario (ontwerp §4): een zakelijke regel (art. 6:235 BW, "de B.V.
   kan de AV niet vernietigen") mag NOOIT op een consument los — die mág de AV juist wél
   vernietigen. Faalrichting is veilig: twijfel/onbekend → NIET injecteren (concept mist
   hooguit extra kennis; nooit een fout juridisch argument).
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.defense_types import DEFENSE_TYPE_KEYS, normalize_defense_type
from app.ai_agent.models import LegalKnowledgeRule

logger = logging.getLogger(__name__)

# Statuswaarden (spiegelen learned_answers, zelfde goedkeur-flow).
STATUS_CANDIDATE = "kandidaat"
STATUS_APPROVED = "goedgekeurd"
STATUS_REJECTED = "afgewezen"

# Toepasbaarheids-poort. Gematcht tegen Case.debtor_type ('b2b' / 'b2c').
APPLIES_ALL = "alle"
APPLIES_BUSINESS = "zakelijk"
APPLIES_CONSUMER = "consument"
APPLIES_TO_VALUES = frozenset({APPLIES_ALL, APPLIES_BUSINESS, APPLIES_CONSUMER})

# Hoeveel regels maximaal per verweer-prompt (S164: hoe meer losse tekst, hoe vaker de AI
# afdwaalt — houd het krap).
_MAX_RULES = 3


def rule_applies(applies_to: str, debtor_type: str | None) -> bool:
    """Mag deze regel op een dossier van dit debiteur-type? HARDE poort (ontwerp §4).

    `alle` → altijd. `zakelijk` → alleen b2b. `consument` → alleen b2c. Onbekende poort of
    onbekend debiteur-type → False (fail closed: liever geen kennis dan verkeerd toegepast).
    """
    if applies_to == APPLIES_ALL:
        return True
    if applies_to == APPLIES_BUSINESS:
        return debtor_type == "b2b"
    if applies_to == APPLIES_CONSUMER:
        return debtor_type == "b2c"
    return False


def validate_rule_fields(
    *, defense_type: str, applies_to: str, title: str, rebuttal_body: str
) -> str | None:
    """Geef een NL-foutmelding als een veld ongeldig is, anders None."""
    if normalize_defense_type(defense_type) != defense_type or defense_type not in DEFENSE_TYPE_KEYS:
        return f"Onbekend verweer-type: {defense_type!r}"
    # Reviewvondst S248: 'overig' zou een stil-dode regel opleveren — de matcher slaat
    # 'overig' bewust over (anders vuurt de regel op elk onbekend verweer).
    if defense_type == "overig":
        return "Kies een specifiek verweer-type — een regel op 'overig' wordt nooit gebruikt"
    if applies_to not in APPLIES_TO_VALUES:
        return f"Ongeldige toepasbaarheid: {applies_to!r} (kies alle/zakelijk/consument)"
    if not (title or "").strip():
        return "Titel is verplicht"
    if len((rebuttal_body or "").strip()) < 20:
        return "Weerlegging is te kort (minimaal 20 tekens)"
    return None


# ── Voeding voor de prompt (alleen GOEDGEKEURDE + actieve, poorten gecheckt) ──────


async def get_applicable_rules(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    defense_type: str | None,
    debtor_type: str | None,
    *,
    limit: int = _MAX_RULES,
) -> list[LegalKnowledgeRule]:
    """Goedgekeurde, actieve regels die op dit verweer-type + debiteur-type van toepassing zijn.

    Beide poorten hard: type-match (via normalize, dus oude aliassen tellen mee) én
    `rule_applies`. Nieuwste goedkeuring eerst.
    """
    if not defense_type:
        return []
    want = normalize_defense_type(defense_type)
    if want == "overig":
        # 'overig' matcht niets specifieks — regels op 'overig' zouden op elk onbekend
        # verweer vuren; bewust niet injecteren (voorkomt breed lekken).
        return []
    rows = (
        await db.execute(
            select(LegalKnowledgeRule)
            .where(
                LegalKnowledgeRule.tenant_id == tenant_id,
                LegalKnowledgeRule.status == STATUS_APPROVED,
                LegalKnowledgeRule.is_active.is_(True),
            )
            .order_by(
                LegalKnowledgeRule.reviewed_at.desc().nullslast(),
                LegalKnowledgeRule.created_at.desc(),
            )
        )
    ).scalars().all()

    picked: list[LegalKnowledgeRule] = []
    for r in rows:
        if normalize_defense_type(r.defense_type) != want:
            continue
        if not rule_applies(r.applies_to, debtor_type):
            continue
        picked.append(r)
        if len(picked) >= limit:
            break
    return picked


def format_rules_for_prompt(rules: list[LegalKnowledgeRule], max_chars: int = 2500) -> str:
    """Formatteer regels als promptcontext — conditionele kennis, GEEN toon-voorbeeld."""
    if not rules:
        return ""
    header = (
        "--- Juridische kennisregels die de advocaat heeft goedgekeurd "
        "(pas een regel ALLEEN toe als de debiteur de beschreven onjuiste stelling "
        "daadwerkelijk voert; dit is standaard juridische kennis, geen verzonnen argument) ---"
    )
    parts = [header]
    chars = len(header)
    for i, r in enumerate(rules, 1):
        lines = [f"\n[Kennisregel {i} — {r.title}]"]
        if r.claim_description:
            lines.append(f"Stelling van de debiteur: {r.claim_description}")
        lines.append(f"Standaard-weerlegging: {r.rebuttal_body}")
        if r.legal_basis:
            lines.append(f"Juridische grondslag: {r.legal_basis}")
        block = "\n".join(lines)
        if chars + len(block) > max_chars:
            break
        parts.append(block)
        chars += len(block)
    # Reviewvondst S248: past er geen enkele regel binnen het budget, stuur dan óók de
    # kop niet mee — een bungelende aankondiging zonder regels is prompt-ruis, en de te
    # lange regel zou stil nooit aankomen. Fail closed + luid loggen.
    if len(parts) == 1:
        logger.warning(
            "Kennisregel(s) passen niet binnen het promptbudget (%d tekens) — "
            "injectie overgeslagen; kort de weerlegging in via het dashboard", max_chars,
        )
        return ""
    return "\n".join(parts)


async def build_knowledge_rules_text(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    defense_type: str | None,
    debtor_type: str | None,
    *,
    max_chars: int = 2500,
) -> str:
    """Ophalen + formatteren — de enige call die de prompt-bouwers nodig hebben.

    Lege string als er geen toepasbare regel is (beide poorten). Gedeeld door alle 3 de
    draft-paden (automation_service / draft_service / unified_draft_service).
    """
    rules = await get_applicable_rules(db, tenant_id, defense_type, debtor_type)
    return format_rules_for_prompt(rules, max_chars=max_chars)


# ── CRUD + goedkeur-flow (dashboard) ──────────────────────────────────────────


async def list_rules(
    db: AsyncSession, tenant_id: uuid.UUID
) -> list[LegalKnowledgeRule]:
    """Alle regels van deze tenant (nieuwste eerst) — kandidaten + goedgekeurd + afgewezen."""
    return list(
        (
            await db.execute(
                select(LegalKnowledgeRule)
                .where(LegalKnowledgeRule.tenant_id == tenant_id)
                .order_by(LegalKnowledgeRule.created_at.desc())
            )
        ).scalars().all()
    )


async def create_rule(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    defense_type: str,
    applies_to: str,
    title: str,
    rebuttal_body: str,
    claim_description: str | None = None,
    legal_basis: str | None = None,
    language: str = "nl",
) -> LegalKnowledgeRule:
    """Maak een nieuwe regel aan als KANDIDAAT (voedt de AI pas na goedkeuring)."""
    row = LegalKnowledgeRule(
        tenant_id=tenant_id,
        defense_type=defense_type,
        applies_to=applies_to,
        title=title.strip(),
        rebuttal_body=rebuttal_body.strip(),
        claim_description=(claim_description or "").strip() or None,
        legal_basis=(legal_basis or "").strip() or None,
        language=language,
        status=STATUS_CANDIDATE,
        is_active=False,
    )
    db.add(row)
    await db.flush()
    return row


async def update_rule(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    rule_id: uuid.UUID,
    *,
    defense_type: str,
    applies_to: str,
    title: str,
    rebuttal_body: str,
    claim_description: str | None = None,
    legal_basis: str | None = None,
) -> LegalKnowledgeRule | None:
    """Bewerk een bestaande regel (inhoud). Raakt de status/goedkeuring niet."""
    row = (
        await db.execute(
            select(LegalKnowledgeRule).where(
                LegalKnowledgeRule.tenant_id == tenant_id,
                LegalKnowledgeRule.id == rule_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    row.defense_type = defense_type
    row.applies_to = applies_to
    row.title = title.strip()
    row.rebuttal_body = rebuttal_body.strip()
    row.claim_description = (claim_description or "").strip() or None
    row.legal_basis = (legal_basis or "").strip() or None
    await db.flush()
    return row


async def approve_rule(
    db: AsyncSession, tenant_id: uuid.UUID, rule_id: uuid.UUID
) -> LegalKnowledgeRule | None:
    """Keur een regel goed — pas hierna voedt hij de AI. None als niet gevonden."""
    row = (
        await db.execute(
            select(LegalKnowledgeRule).where(
                LegalKnowledgeRule.tenant_id == tenant_id,
                LegalKnowledgeRule.id == rule_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    row.status = STATUS_APPROVED
    row.is_active = True
    row.reviewed_at = datetime.now(UTC)
    await db.flush()
    return row


async def reject_rule(
    db: AsyncSession, tenant_id: uuid.UUID, rule_id: uuid.UUID
) -> bool:
    """Wijs een regel af / trek een goedkeuring in — voedt de AI nooit meer. True bij wijziging."""
    row = (
        await db.execute(
            select(LegalKnowledgeRule).where(
                LegalKnowledgeRule.tenant_id == tenant_id,
                LegalKnowledgeRule.id == rule_id,
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


async def delete_rule(
    db: AsyncSession, tenant_id: uuid.UUID, rule_id: uuid.UUID
) -> bool:
    """Verwijder een regel definitief (curated content — geen empirische bron om te bewaren)."""
    row = (
        await db.execute(
            select(LegalKnowledgeRule).where(
                LegalKnowledgeRule.tenant_id == tenant_id,
                LegalKnowledgeRule.id == rule_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return False
    await db.delete(row)
    await db.flush()
    return True


if __name__ == "__main__":
    # ponytail: één runnbare zelfcheck op de veiligheidspoort (het hart van deze feature).
    # Een zakelijke regel mag NOOIT op een consument; onbekend faalt dicht.
    assert rule_applies(APPLIES_ALL, "b2b") is True
    assert rule_applies(APPLIES_ALL, "b2c") is True
    assert rule_applies(APPLIES_ALL, None) is True
    assert rule_applies(APPLIES_BUSINESS, "b2b") is True
    assert rule_applies(APPLIES_BUSINESS, "b2c") is False  # doemscenario §4
    assert rule_applies(APPLIES_BUSINESS, None) is False
    assert rule_applies(APPLIES_CONSUMER, "b2c") is True
    assert rule_applies(APPLIES_CONSUMER, "b2b") is False
    assert rule_applies("onzin", "b2b") is False  # onbekende poort → dicht
    assert validate_rule_fields(
        defense_type="av_toepasselijkheid", applies_to="zakelijk",
        title="AV-vernietiging B.V.", rebuttal_body="x" * 25,
    ) is None
    assert validate_rule_fields(
        defense_type="bestaat_niet", applies_to="alle", title="t", rebuttal_body="x" * 25,
    ) is not None
    assert validate_rule_fields(
        defense_type="av_toepasselijkheid", applies_to="alle", title="t", rebuttal_body="kort",
    ) is not None
    print("knowledge_rules self-check OK")
