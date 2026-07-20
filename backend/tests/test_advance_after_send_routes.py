"""Wachter (S232, skill breed-testen) — doorschuiven-na-verzending over ALLE routes.

Eén gedrag ("een verstuurde stap-brief schuift het dossier door") is via meerdere
routes bereikbaar: de AI-concept-route (advance-after-send) en de sjabloon-verzendknop
(compose/send). Deze wachter loopt de hele poort-matrix af zodat P1 (alleen stap-brieven
bewegen de pijplijn; antwoorden/vrij/herverzending nooit) op elke route geldt en
dubbel-doorschuiven met de AI-route onmogelijk is.

De doorschuif-beslissing is bewust één pure functie (should_advance_on_template_send)
zodat een TOEKOMSTIGE route die vergeet de guard te zetten hier automatisch afwijkt —
het patroon van test_send_route_drift_guard.py.
"""

import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant
from app.cases.models import Case
from app.incasso.models import (
    CaseStepHistory,
    IncassoPipelineStep,
    StepTransition,
)
from app.incasso.service import (
    advance_after_step_send,
    should_advance_on_template_send,
    template_belongs_to_step,
)
from app.relations.models import Contact

# ── Poort-matrix: should_advance_on_template_send ────────────────────────────
# Kolommen: (template_type gekozen, is_reply_or_forward, stap.template_type) → advance?

_MATRIX = [
    # Stap-brief die bij de huidige stap hoort, verse mail → DOOR.
    ("sommatie_drukte", False, "sommatie_drukte", True),
    # Zelfde brief maar als ANTWOORD/DOORSTUREN → nooit (huisregel P1).
    ("sommatie_drukte", True, "sommatie_drukte", False),
    # Geen sjabloon (vrij bericht óf AI-concept-route) → nooit hier;
    # de AI-route schuift door via advance-after-send (anders dubbel).
    (None, False, "sommatie_drukte", False),
    ("", False, "sommatie_drukte", False),
    # Herverzending van een EERDERE brief terwijl het dossier al verder staat:
    # eerste-sommatie-brief op de tweede-sommatie-stap → matcht niet → niets.
    ("sommatie_drukte", False, "aanmaning", False),
    # Stap zonder brief-koppeling (derde/laatste sommatie in prod) → niets.
    ("wederom_sommatie_kort", False, None, False),
    # Tweede-sommatie-variant op de tweede-sommatie-stap (familie) → DOOR.
    ("sommatie_na_reactie", False, "aanmaning", True),
]


@pytest.mark.parametrize("tpl,is_reply,step_tpl,expected", _MATRIX)
def test_advance_gate_matrix(tpl, is_reply, step_tpl, expected):
    assert should_advance_on_template_send(tpl, is_reply, step_tpl) is expected


def test_skip_pipeline_advance_blocks_double_send():
    """AI-concept-review waar de gebruiker alsnog een stap-sjabloon koos: de aparte
    advance-after-send-call regelt de doorschuif, dus compose/send moet 'm overslaan —
    anders schuift het dossier via BEIDE routes door (dubbel)."""
    # Zonder de guard zou dit doorschuiven (stap-sjabloon, verse mail)...
    assert should_advance_on_template_send("sommatie_drukte", False, "sommatie_drukte") is True
    # ...maar met de guard niet.
    assert should_advance_on_template_send(
        "sommatie_drukte", False, "sommatie_drukte", skip_pipeline_advance=True
    ) is False


# ── Brief-families: template_belongs_to_step ─────────────────────────────────


def test_family_first_summons_only_matches_first():
    assert template_belongs_to_step("sommatie_drukte", "sommatie_drukte")
    # Eerste-sommatie-brief hoort NIET bij de tweede-sommatie-stap.
    assert not template_belongs_to_step("sommatie_drukte", "aanmaning")


def test_family_second_summons_variants_all_match():
    # Alle tweede-sommatie-varianten (incl. het oude 'aanmaning' waar de stap in
    # prod aan hangt) horen bij dezelfde stap.
    for variant in ("aanmaning", "sommatie_na_reactie", "wederom_sommatie_kort", "tweede_sommatie"):
        assert template_belongs_to_step(variant, "aanmaning"), variant


def test_family_empty_never_matches():
    assert not template_belongs_to_step(None, "sommatie_drukte")
    assert not template_belongs_to_step("sommatie_drukte", None)
    assert not template_belongs_to_step(None, None)


# ── Gedrag: advance_after_step_send op een echt dossier ──────────────────────


async def _case_on_step_with_advance_rule(
    db: AsyncSession, tenant_id: uuid.UUID, *, with_rule: bool
):
    client = Contact(id=uuid.uuid4(), tenant_id=tenant_id, contact_type="person", name="Cliënt")
    debtor = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="person",
        name="Debiteur", email="debiteur@example.com",
    )
    db.add_all([client, debtor])
    await db.flush()
    eerste = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name="Eerste sommatie",
        sort_order=1, min_wait_days=0, max_wait_days=4,
        step_category="minnelijk", debtor_type="both", template_type="sommatie_drukte",
    )
    tweede = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name="Tweede sommatie",
        sort_order=2, min_wait_days=4, max_wait_days=4,
        step_category="minnelijk", debtor_type="both", template_type="aanmaning",
    )
    db.add_all([eerste, tweede])
    await db.flush()
    if with_rule:
        db.add(StepTransition(
            id=uuid.uuid4(), tenant_id=tenant_id,
            from_step_id=eerste.id, to_step_id=tweede.id,
            trigger_type="timeout", action="advance_to_step", is_default=True, is_active=True,
        ))
    case = Case(
        id=uuid.uuid4(), tenant_id=tenant_id, case_number="2026-32001",
        case_type="incasso", status="in_behandeling", debtor_type="b2c",
        client_id=client.id, opposing_party_id=debtor.id,
        date_opened=date.today(), incasso_step_id=eerste.id,
    )
    db.add(case)
    await db.flush()
    # Open staphistorie-rij van de huidige stap (zodat mark_current_step... iets vindt).
    db.add(CaseStepHistory(
        tenant_id=tenant_id, case_id=case.id, step_id=eerste.id,
        entered_at=datetime.now(UTC), trigger_type="manual",
    ))
    await db.flush()
    return case, eerste, tweede


@pytest.mark.asyncio
async def test_advance_moves_case_and_logs_send(db: AsyncSession, test_tenant: Tenant):
    case, eerste, tweede = await _case_on_step_with_advance_rule(db, test_tenant.id, with_rule=True)

    result = await advance_after_step_send(db, test_tenant.id, case, None)

    assert result["advanced"] is True
    assert result["to_step_name"] == "Tweede sommatie"
    assert case.incasso_step_id == tweede.id
    # De verzending is vastgelegd op de HUIDIGE (oude) stap vóór het doorschuiven.
    hist = (await db.execute(
        select(CaseStepHistory).where(
            CaseStepHistory.case_id == case.id,
            CaseStepHistory.step_id == eerste.id,
        )
    )).scalar_one()
    assert hist.email_sent is True
    assert hist.email_sent_at is not None


@pytest.mark.asyncio
async def test_advance_noop_without_rule(db: AsyncSession, test_tenant: Tenant):
    case, eerste, _tweede = await _case_on_step_with_advance_rule(db, test_tenant.id, with_rule=False)

    result = await advance_after_step_send(db, test_tenant.id, case, None)

    assert result["advanced"] is False
    # Geen advance-regel → blijft staan, maar de verzending is wél vastgelegd.
    assert case.incasso_step_id == eerste.id
