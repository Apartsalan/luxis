"""S166 backlog-fixes (rood→groen):

* Punt 2 — een verzonden brief wordt gelogd op de OPEN history-rij van de huidige
  stap, zodat 'E-mail verzonden' in de staphistorie verschijnt.
* Punt 4 — de zaak-status loopt mee met de pipeline-stap (move_case_to_step),
  alleen bij een eenduidige mapping én een bestaande status voor de tenant.
* Punt 3 — de 14-dagenbrief is de eerste pipeline-stap voor een B2C-dossier
  (in de seed én bij het automatisch toewijzen in create_case).
"""

import uuid
from datetime import date

import pytest
from sqlalchemy import select

from app.cases.schemas import CaseCreate
from app.cases.service import create_case
from app.incasso.models import CaseStepHistory, IncassoPipelineStep
from app.incasso.service import (
    mark_current_step_communication_sent,
    move_case_to_step,
    seed_default_steps,
)
from tests.helpers.incasso_fixtures import create_incasso_case, create_pipeline_steps

# ── Punt 2: verzending wordt gelogd op de huidige stap ──────────────────────


@pytest.mark.asyncio
async def test_mark_current_step_sets_sent_flags_on_open_history(
    db, test_tenant, test_user, test_company, test_person
):
    """De verzending hoort op de OPEN history-rij van de huidige stap (de stap waar
    de brief voor gold), zodat 'E-mail verzonden' in de staphistorie verschijnt."""
    steps = await create_pipeline_steps(db, test_tenant.id)
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    # move_case_to_step maakt de open history-rij voor de stap aan.
    await move_case_to_step(db, test_tenant.id, case, steps[0], user_id=test_user.id)

    hist = (
        await db.execute(
            select(CaseStepHistory).where(
                CaseStepHistory.case_id == case.id,
                CaseStepHistory.exited_at.is_(None),
            )
        )
    ).scalar_one()
    # Rood vóór de fix: deze vlaggen werden nooit gezet op het verzendpad.
    assert hist.email_sent is False
    assert hist.template_sent is False

    result = await mark_current_step_communication_sent(db, test_tenant.id, case)
    assert result is not None
    await db.refresh(hist)
    assert hist.email_sent is True
    assert hist.template_sent is True


@pytest.mark.asyncio
async def test_mark_current_step_without_active_step_returns_none(
    db, test_tenant, test_user, test_company, test_person
):
    """Zonder actieve stap valt er niets te markeren (geen crash)."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    result = await mark_current_step_communication_sent(db, test_tenant.id, case)
    assert result is None


# ── Punt 4 (B3, S198): de pijplijn stuurt de 4-status ───────────────────────


@pytest.mark.asyncio
async def test_move_to_working_step_sets_in_behandeling(
    db, test_tenant, test_user, test_company, test_person
):
    """Een werk-stap zet de zaak op 'in_behandeling' (B3, S198)."""
    steps = await create_pipeline_steps(db, test_tenant.id)  # Aanmaning = werk-stap
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user,
        step=None, status="nieuw",
    )
    await move_case_to_step(db, test_tenant.id, case, steps[0], user_id=test_user.id)
    await db.refresh(case)
    assert case.incasso_step_id == steps[0].id
    assert case.status == "in_behandeling"
    assert case.date_closed is None


@pytest.mark.asyncio
async def test_move_to_betaald_step_closes_case(
    db, test_tenant, test_user, test_company, test_person
):
    """De terminale eindstap 'Betaald' zet status 'betaald' + date_closed."""
    betaald_step = IncassoPipelineStep(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Betaald",
        sort_order=99,
        min_wait_days=0,
        max_wait_days=0,
        is_terminal=True,
    )
    db.add(betaald_step)
    await db.flush()
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user,
        step=None, status="in_behandeling",
    )
    await move_case_to_step(db, test_tenant.id, case, betaald_step, user_id=test_user.id)
    await db.refresh(case)
    assert case.status == "betaald"
    assert case.date_closed is not None


@pytest.mark.asyncio
async def test_move_back_to_working_step_reopens(
    db, test_tenant, test_user, test_company, test_person
):
    """Een gesloten zaak terug op een werk-stap = heropenen: in_behandeling,
    sluitdatum leeg."""
    steps = await create_pipeline_steps(db, test_tenant.id)
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user,
        step=None, status="afgesloten",
    )
    case.date_closed = date.today()
    await db.flush()
    await move_case_to_step(db, test_tenant.id, case, steps[0], user_id=test_user.id)
    await db.refresh(case)
    assert case.status == "in_behandeling"
    assert case.date_closed is None


# ── Punt 3: 14-dagenbrief als eerste B2C-stap ───────────────────────────────


@pytest.mark.asyncio
async def test_seed_includes_14dagenbrief_before_sommaties_for_b2c(db, test_tenant):
    steps = await seed_default_steps(db, test_tenant.id)
    by_name = {s.name: s for s in steps}
    assert "14-dagenbrief" in by_name
    veertien = by_name["14-dagenbrief"]
    assert veertien.debtor_type == "b2c"
    assert veertien.step_category == "minnelijk"
    assert veertien.sort_order < by_name["Eerste sommatie"].sort_order


@pytest.mark.asyncio
async def test_create_case_b2c_starts_on_14dagenbrief(
    db, test_tenant, test_user, test_company
):
    await seed_default_steps(db, test_tenant.id)
    case = await create_case(
        db,
        test_tenant.id,
        test_user.id,
        CaseCreate(
            case_type="incasso",
            debtor_type="b2c",
            client_id=test_company.id,
            date_opened=date.today(),
        ),
    )
    step = (
        await db.execute(
            select(IncassoPipelineStep).where(
                IncassoPipelineStep.id == case.incasso_step_id
            )
        )
    ).scalar_one()
    assert step.name == "14-dagenbrief"


@pytest.mark.asyncio
async def test_create_case_b2b_skips_14dagenbrief_starts_on_eerste_sommatie(
    db, test_tenant, test_user, test_company
):
    await seed_default_steps(db, test_tenant.id)
    case = await create_case(
        db,
        test_tenant.id,
        test_user.id,
        CaseCreate(
            case_type="incasso",
            debtor_type="b2b",
            client_id=test_company.id,
            date_opened=date.today(),
        ),
    )
    step = (
        await db.execute(
            select(IncassoPipelineStep).where(
                IncassoPipelineStep.id == case.incasso_step_id
            )
        )
    ).scalar_one()
    assert step.name == "Eerste sommatie"
