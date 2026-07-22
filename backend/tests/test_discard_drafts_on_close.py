"""Wachter (S223, huisregel P3): een zaak sluiten laat GEEN open AI-concept achter.

S224 (veegsessie): uitgebreid met follow-up-ADVIEZEN — een pending advies op een
gesloten zaak wordt bij heropenen weer zichtbaar (dubbel-verstuur-risico, gemeten
op IN100613: gesloten 15/7 mét pending advies van 13/7).

Dit is bewust een route-brede wachter, geen test voor één geval: hij sluit een
zaak via ELKE sluit-route (handmatig, pijplijn-eindstap, betaling-hook) en eist
dat een open concept én een open advies telkens vervallen. Een toekomstige vierde
sluit-route die de opruiming vergeet, valt hier rood — precies het patroon van de
auth/RLS-drift-guards.
"""

import uuid
from decimal import Decimal

import pytest

from app.ai_agent.followup_models import FollowupRecommendation, RecommendationStatus
from app.ai_agent.models import AIDraft, DraftStatus
from app.cases.schemas import CaseStatusUpdate
from app.cases.service import update_case_status
from app.incasso.models import IncassoPipelineStep
from app.incasso.service import move_case_to_step
from app.workflow.hooks import on_payment_received
from tests.helpers.incasso_fixtures import create_incasso_case


async def _open_draft(db, tenant_id, case_id, *, intent="reply_to_email") -> AIDraft:
    draft = AIDraft(
        tenant_id=tenant_id, case_id=case_id,
        subject="Concept", body="Tekst.",
        status=DraftStatus.GENERATED, intent=intent,
    )
    db.add(draft)
    await db.flush()
    await db.refresh(draft)
    return draft


async def _pending_recommendation(db, tenant_id, case_id) -> FollowupRecommendation:
    step = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name="Eerste sommatie",
        sort_order=1, min_wait_days=0, max_wait_days=4,
    )
    db.add(step)
    await db.flush()
    rec = FollowupRecommendation(
        tenant_id=tenant_id, case_id=case_id, incasso_step_id=step.id,
        recommended_action="generate_document", reasoning="Test-advies.",
        days_in_step=5, outstanding_amount=Decimal("100.00"),
        urgency="normal", status=RecommendationStatus.PENDING,
    )
    db.add(rec)
    await db.flush()
    await db.refresh(rec)
    return rec


@pytest.mark.asyncio
async def test_manual_close_discards_open_drafts(
    db, test_tenant, test_user, test_company
):
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09401"
    )
    draft = await _open_draft(db, test_tenant.id, case.id)
    rec = await _pending_recommendation(db, test_tenant.id, case.id)

    await update_case_status(
        db, test_tenant.id, case.id, test_user.id,
        CaseStatusUpdate(new_status="afgesloten", note="dicht"),
    )

    await db.refresh(draft)
    assert draft.status == DraftStatus.DISCARDED
    await db.refresh(rec)
    assert rec.status == RecommendationStatus.SUPERSEDED


@pytest.mark.asyncio
async def test_manual_reopen_leaves_drafts_untouched(
    db, test_tenant, test_user, test_company
):
    """Regressie: een NIET-sluitende statuswissel (heropenen) raakt concepten niet."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09402"
    )
    draft = await _open_draft(db, test_tenant.id, case.id)

    await update_case_status(
        db, test_tenant.id, case.id, test_user.id,
        CaseStatusUpdate(new_status="in_behandeling", note="heropend"),
    )

    await db.refresh(draft)
    assert draft.status == DraftStatus.GENERATED


@pytest.mark.asyncio
async def test_pipeline_terminal_step_discards_open_drafts(
    db, test_tenant, test_user, test_company
):
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09403"
    )
    terminal = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=test_tenant.id, name="Afgesloten",
        sort_order=99, min_wait_days=0, max_wait_days=0, is_terminal=True,
    )
    db.add(terminal)
    await db.flush()
    draft = await _open_draft(db, test_tenant.id, case.id, intent="free_compose")
    rec = await _pending_recommendation(db, test_tenant.id, case.id)

    await move_case_to_step(db, test_tenant.id, case, terminal)

    await db.refresh(draft)
    assert draft.status == DraftStatus.DISCARDED
    await db.refresh(rec)
    assert rec.status == RecommendationStatus.SUPERSEDED


@pytest.mark.asyncio
async def test_payment_autoclose_discards_open_drafts(
    db, test_tenant, test_user, test_company
):
    """Volledige betaling → hook sluit de zaak op 'betaald' → concepten vervallen.
    Zaak zonder vorderingen = €0 openstaand, dus de hook sluit direct."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09404"
    )
    draft = await _open_draft(db, test_tenant.id, case.id)
    rec = await _pending_recommendation(db, test_tenant.id, case.id)

    result = await on_payment_received(
        db, test_tenant.id, case.id, Decimal("100.00")
    )
    assert result is not None  # hook sloot de zaak

    await db.refresh(draft)
    assert draft.status == DraftStatus.DISCARDED
    await db.refresh(rec)
    assert rec.status == RecommendationStatus.SUPERSEDED


# ── S239: een vervallen concept laat GEEN open nakijk-taak achter ────────────
# Uitbreiding van P3: op prod stonden 8 open 'Review concept-email'-taken die
# naar een al-weggegooid concept wezen. Route-brede wachter over alle plekken
# waar een concept DISCARDED wordt.


async def _review_task(db, tenant_id, case_id, draft_id):
    from datetime import UTC, datetime

    from app.workflow.models import WorkflowTask

    task = WorkflowTask(
        tenant_id=tenant_id, case_id=case_id,
        task_type="review_ai_draft",
        title="Review concept-email: Eerste sommatie",
        description="test", due_date=datetime.now(UTC).date(),
        status="pending",
        action_config={"draft_id": str(draft_id), "step_name": "Eerste sommatie"},
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


@pytest.mark.asyncio
async def test_manual_discard_skips_review_task(db, test_tenant, test_user, test_company):
    """Route 1: handmatig weggooien via update_draft_status."""
    from app.ai_agent.draft_service import update_draft_status

    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09405"
    )
    draft = await _open_draft(db, test_tenant.id, case.id)
    task = await _review_task(db, test_tenant.id, case.id, draft.id)

    await update_draft_status(db, test_tenant.id, draft.id, DraftStatus.DISCARDED)

    await db.refresh(task)
    assert task.status == "skipped"


@pytest.mark.asyncio
async def test_close_case_skips_review_task(db, test_tenant, test_user, test_company):
    """Route 2: zaak sluiten → discard_open_drafts_on_close → taak dicht."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09406"
    )
    draft = await _open_draft(db, test_tenant.id, case.id)
    task = await _review_task(db, test_tenant.id, case.id, draft.id)

    await update_case_status(
        db, test_tenant.id, case.id, test_user.id,
        CaseStatusUpdate(new_status="afgesloten", note="dicht"),
    )

    await db.refresh(draft)
    assert draft.status == DraftStatus.DISCARDED
    await db.refresh(task)
    assert task.status == "skipped"


@pytest.mark.asyncio
async def test_step_change_stale_draft_skips_review_task(
    db, test_tenant, test_user, test_company
):
    """Route 3: stap-wissel gooit stale next_step-concepten weg → taak dicht."""
    from app.incasso.service import discard_stale_step_drafts

    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09407"
    )
    old_step = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=test_tenant.id, name="Eerste sommatie",
        sort_order=1, min_wait_days=0, max_wait_days=4,
    )
    new_step = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=test_tenant.id, name="Tweede sommatie",
        sort_order=2, min_wait_days=0, max_wait_days=4,
    )
    db.add_all([old_step, new_step])
    await db.flush()
    draft = await _open_draft(db, test_tenant.id, case.id, intent="next_step")
    draft.step_id = old_step.id
    await db.flush()
    task = await _review_task(db, test_tenant.id, case.id, draft.id)

    n = await discard_stale_step_drafts(
        db, test_tenant.id, case.id, keep_step_id=new_step.id
    )
    assert n == 1

    await db.refresh(task)
    assert task.status == "skipped"


@pytest.mark.asyncio
async def test_sent_draft_review_task_untouched_by_other_discard(
    db, test_tenant, test_user, test_company
):
    """Tegenproef: de taak van een ÁNDER (nog open) concept blijft gewoon staan."""
    from app.ai_agent.draft_service import update_draft_status

    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09408"
    )
    draft_a = await _open_draft(db, test_tenant.id, case.id)
    draft_b = await _open_draft(db, test_tenant.id, case.id)
    task_b = await _review_task(db, test_tenant.id, case.id, draft_b.id)

    await update_draft_status(db, test_tenant.id, draft_a.id, DraftStatus.DISCARDED)

    await db.refresh(task_b)
    assert task_b.status == "pending"
