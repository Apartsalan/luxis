"""S236 — de Taken-pagina is dé werklijst (keuze Arsalan).

Wachters over de gespiegelde verstuur-taak: elk openstaand verstuur-advies van
de follow-up-adviseur krijgt een taak "{stap} versturen — {zaaknummer}" op de
Taken-pagina, en die taak gaat dicht op precies de momenten dat het advies
zelf afgehandeld raakt:
- brief van de stap écht verstuurd (gedeelde doorschuif-motor, álle routes) → completed
- advies afgewezen of vervallen (stap-wissel/supersede) → skipped

Foutsoort die dit dekt: werk dat wél op de Follow-up-pagina staat maar
onzichtbaar is op de werklijst — of andersom: een taak die blijft nazeuren
voor een brief die al weg is.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.followup_models import (
    FollowupRecommendation,
    RecommendationStatus,
    RecommendedAction,
)
from app.ai_agent.followup_service import (
    reject_recommendation,
    scan_for_followups,
)
from app.auth.models import Tenant, User
from app.cases.models import Case
from app.incasso.models import IncassoPipelineStep
from app.incasso.service import advance_after_step_send, move_case_to_step
from app.relations.models import Contact
from app.workflow.models import WorkflowTask

# ---------------------------------------------------------------------------
# Helpers (zelfde patroon als test_followup.py)
# ---------------------------------------------------------------------------


async def _create_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    name: str = "Eerste sommatie",
    sort_order: int = 2,
    min_wait_days: int = 14,
    template_type: str | None = "sommatie_drukte",
) -> IncassoPipelineStep:
    step = IncassoPipelineStep(
        tenant_id=tenant_id,
        name=name,
        sort_order=sort_order,
        min_wait_days=min_wait_days,
        max_wait_days=min_wait_days * 2,
        template_type=template_type,
    )
    db.add(step)
    await db.flush()
    await db.refresh(step)
    return step


async def _create_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    step: IncassoPipelineStep,
    *,
    days_in_step: int = 16,
) -> Case:
    client = Contact(
        tenant_id=tenant_id,
        name=f"Test Client {uuid.uuid4().hex[:4]}",
        contact_type="company",
    )
    db.add(client)
    await db.flush()

    case = Case(
        tenant_id=tenant_id,
        case_number=f"2026-{uuid.uuid4().hex[:5]}",
        case_type="incasso",
        status="nieuw",
        date_opened=date.today() - timedelta(days=days_in_step + 5),
        incasso_step_id=step.id,
        step_entered_at=datetime.now(UTC) - timedelta(days=days_in_step),
        total_principal=5000.00,
        total_paid=0.00,
        assigned_to_id=user_id,
        client_id=client.id,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


async def _send_tasks(db: AsyncSession, tenant_id: uuid.UUID, case_id: uuid.UUID):
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.case_id == case_id,
            WorkflowTask.task_type == "send_letter",
            WorkflowTask.action_config["source"].astext == "followup_send",
        )
    )
    return list(result.scalars().all())


async def _escalate_tasks(db: AsyncSession, tenant_id: uuid.UUID, case_id: uuid.UUID):
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.case_id == case_id,
            WorkflowTask.task_type == "manual_review",
            WorkflowTask.action_config["source"].astext == "followup_escalate",
        )
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Aanmaak
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scan_creates_send_task_for_new_advice(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Nieuw verstuur-advies → taak "{stap} versturen — {zaaknummer}" op de werklijst."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    await db.commit()

    assert count == 1
    tasks = await _send_tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1
    task = tasks[0]
    assert task.title == f"Eerste sommatie versturen — {case.case_number}"
    assert task.status == "due"
    assert task.due_date == date.today()
    assert task.assigned_to_id == test_user.id
    assert task.action_config["step_id"] == str(step.id)


@pytest.mark.asyncio
async def test_second_scan_does_not_duplicate_task(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Tweede scan (advies staat nog open) → géén tweede taak."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()

    await scan_for_followups(db, test_tenant.id)
    await db.commit()
    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    tasks = await _send_tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_scan_backfills_task_for_preexisting_advice(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Advies van vóór deze wijziging (pending, nog geen taak) → scan maakt de
    taak alsnog aan, ook al maakt hij geen nieuw advies."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    db.add(
        FollowupRecommendation(
            tenant_id=test_tenant.id,
            case_id=case.id,
            incasso_step_id=step.id,
            recommended_action=RecommendedAction.GENERATE_DOCUMENT,
            reasoning="bestaand advies",
            days_in_step=16,
            outstanding_amount=Decimal("5000.00"),
            urgency="normal",
            status=RecommendationStatus.PENDING,
        )
    )
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    await db.commit()

    assert count == 0  # geen nieuw advies (dedupe)
    tasks = await _send_tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1  # maar wél de ontbrekende taak


@pytest.mark.asyncio
async def test_no_task_for_escalate_advice(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Stap zonder sjabloon → escalatie-advies: géén verstuur-taak, maar (S237)
    wél een gespiegelde 'Vervolg bepalen'-taak op de werklijst."""
    step = await _create_step(db, test_tenant.id, template_type=None)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    await db.commit()

    assert count == 1
    tasks = await _send_tasks(db, test_tenant.id, case.id)
    assert tasks == []
    esc = await _escalate_tasks(db, test_tenant.id, case.id)
    assert len(esc) == 1
    assert esc[0].title == f"Vervolg bepalen — {case.case_number}"
    assert esc[0].status == "due"
    assert esc[0].action_config["step_id"] == str(step.id)


# ---------------------------------------------------------------------------
# Sluiten
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_motor_completes_task_when_letter_sent(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Brief van de stap verstuurd (gedeelde motor, record_send=True) → taak
    afgevinkt. Dekt álle verzendroutes: compose/send, AI-concept, batch, follow-up."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()
    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    await advance_after_step_send(db, test_tenant.id, case, test_user.id)
    await db.commit()

    tasks = await _send_tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1
    assert tasks[0].status == "completed"
    assert tasks[0].completed_at is not None


@pytest.mark.asyncio
async def test_generate_without_send_leaves_task_open(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Batch-generatie zónder verzending (record_send=False): er ging niets de
    deur uit → de verstuur-taak blijft open."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()
    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    await advance_after_step_send(
        db, test_tenant.id, case, test_user.id, record_send=False
    )
    await db.commit()

    tasks = await _send_tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1
    assert tasks[0].status == "due"


@pytest.mark.asyncio
async def test_reject_advice_skips_task(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Advies afgewezen → de gespiegelde taak vervalt (skipped, niet completed)."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()
    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    rec = (
        await db.execute(
            select(FollowupRecommendation).where(
                FollowupRecommendation.tenant_id == test_tenant.id,
                FollowupRecommendation.case_id == case.id,
            )
        )
    ).scalar_one()
    await reject_recommendation(db, test_tenant.id, rec.id, test_user.id, "Niet nodig")
    await db.commit()

    tasks = await _send_tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1
    assert tasks[0].status == "skipped"


@pytest.mark.asyncio
async def test_step_change_skips_task(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Stap-wissel (advies wordt superseded) → taak vervalt mee. Anders blijft
    er een taak staan voor een brief die niet meer aan de beurt is."""
    step = await _create_step(db, test_tenant.id)
    other = await _create_step(
        db, test_tenant.id, name="Tweede sommatie", sort_order=3,
        template_type="wederom_sommatie",
    )
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()
    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    await move_case_to_step(
        db, test_tenant.id, case, other, user_id=test_user.id, trigger_type="manual"
    )
    await db.commit()

    tasks = await _send_tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1
    assert tasks[0].status == "skipped"


@pytest.mark.asyncio
async def test_no_send_task_for_stale_escalate_advice_on_templated_step(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """S236-review — een oud escalatie-advies op een stap die inmiddels wél een
    sjabloon heeft (S234 gaf de derde/laatste sommatie een brief) mag GEEN
    'versturen'-taak krijgen: 'Uitvoeren' van dat advies verstuurt niets maar
    maakt een beoordeel-taak. Live gevonden: 10 misleidende taken op prod."""
    step = await _create_step(db, test_tenant.id)  # stap MET sjabloon
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    db.add(
        FollowupRecommendation(
            tenant_id=test_tenant.id,
            case_id=case.id,
            incasso_step_id=step.id,
            recommended_action=RecommendedAction.ESCALATE,  # oud advies-type
            reasoning="advies van vóór de briefkoppeling",
            days_in_step=16,
            outstanding_amount=Decimal("5000.00"),
            urgency="normal",
            status=RecommendationStatus.PENDING,
        )
    )
    await db.commit()

    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    tasks = await _send_tasks(db, test_tenant.id, case.id)
    assert tasks == []
    # S237: het escalatie-advies krijgt nu wél een eerlijke beoordeel-taak
    # (i.p.v. de misleidende verstuur-taak van vóór de S236-fix).
    esc = await _escalate_tasks(db, test_tenant.id, case.id)
    assert len(esc) == 1
    assert "Vervolg bepalen" in esc[0].title


@pytest.mark.asyncio
async def test_scan_no_task_when_case_already_moved_on(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Pending advies waarvan de zaak al op een ándere stap staat → geen taak
    (de taak zou naar een verouderde brief wijzen)."""
    step_a = await _create_step(db, test_tenant.id, name="Stap A")
    step_b = await _create_step(db, test_tenant.id, name="Stap B", sort_order=3)
    case = await _create_case(db, test_tenant.id, test_user.id, step_b, days_in_step=3)
    db.add(
        FollowupRecommendation(
            tenant_id=test_tenant.id,
            case_id=case.id,
            incasso_step_id=step_a.id,
            recommended_action=RecommendedAction.GENERATE_DOCUMENT,
            reasoning="verouderd advies",
            days_in_step=20,
            outstanding_amount=Decimal("5000.00"),
            urgency="normal",
            status=RecommendationStatus.PENDING,
        )
    )
    await db.commit()

    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    tasks = await _send_tasks(db, test_tenant.id, case.id)
    assert tasks == []


# ---------------------------------------------------------------------------
# S237 — gespiegelde escalatie-taken
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_second_scan_does_not_duplicate_escalate_task(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Tweede scan (escalatie-advies staat nog open) → géén tweede taak."""
    step = await _create_step(db, test_tenant.id, template_type=None)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()

    await scan_for_followups(db, test_tenant.id)
    await db.commit()
    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    esc = await _escalate_tasks(db, test_tenant.id, case.id)
    assert len(esc) == 1


@pytest.mark.asyncio
async def test_reject_escalate_advice_skips_mirror_task(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Escalatie-advies afgewezen → de gespiegelde taak vervalt (skipped)."""
    step = await _create_step(db, test_tenant.id, template_type=None)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()
    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    rec = (
        await db.execute(
            select(FollowupRecommendation).where(
                FollowupRecommendation.tenant_id == test_tenant.id,
                FollowupRecommendation.case_id == case.id,
            )
        )
    ).scalar_one()
    await reject_recommendation(db, test_tenant.id, rec.id, test_user.id, "Niet nodig")
    await db.commit()

    esc = await _escalate_tasks(db, test_tenant.id, case.id)
    assert len(esc) == 1
    assert esc[0].status == "skipped"


@pytest.mark.asyncio
async def test_step_change_skips_escalate_mirror_task(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Stap-wissel (advies superseded) → escalatie-spiegel vervalt mee."""
    step = await _create_step(db, test_tenant.id, template_type=None)
    other = await _create_step(
        db, test_tenant.id, name="Tweede sommatie", sort_order=3,
        template_type="wederom_sommatie",
    )
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()
    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    await move_case_to_step(
        db, test_tenant.id, case, other, user_id=test_user.id, trigger_type="manual"
    )
    await db.commit()

    esc = await _escalate_tasks(db, test_tenant.id, case.id)
    assert len(esc) == 1
    assert esc[0].status == "skipped"


@pytest.mark.asyncio
async def test_motor_send_close_leaves_escalate_task_alone(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Een verzonden brief zegt niets over een escalatie-beslissing: de
    completed-sluiting van de doorschuif-motor raakt alleen verstuur-taken."""
    from app.incasso.service import close_followup_send_tasks

    step = await _create_step(db, test_tenant.id, template_type=None)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()
    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    # Zelfde aanroep als de motor doet (default sources = alleen followup_send).
    closed = await close_followup_send_tasks(
        db, test_tenant.id, case.id, step_id=step.id, status="completed"
    )
    await db.commit()

    assert closed == 0
    esc = await _escalate_tasks(db, test_tenant.id, case.id)
    assert len(esc) == 1
    assert esc[0].status == "due"


@pytest.mark.asyncio
async def test_execute_escalate_does_not_duplicate_mirror_task(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """'Uitvoeren' van een escalatie-advies waarvan de spiegel-taak al op de
    werklijst staat → geen tweede review-taak."""
    from app.ai_agent.followup_service import (
        approve_recommendation,
        execute_recommendation,
    )

    step = await _create_step(db, test_tenant.id, template_type=None)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await db.commit()
    await scan_for_followups(db, test_tenant.id)
    await db.commit()

    rec = (
        await db.execute(
            select(FollowupRecommendation).where(
                FollowupRecommendation.tenant_id == test_tenant.id,
                FollowupRecommendation.case_id == case.id,
            )
        )
    ).scalar_one()
    await approve_recommendation(db, test_tenant.id, rec.id, test_user.id)
    await db.commit()
    result = await execute_recommendation(db, test_tenant.id, rec.id, test_user.id)
    await db.commit()

    assert result is not None
    assert "stond al op de werklijst" in (result.execution_result or "")
    # Eén open review-taak in totaal: de spiegel; geen extra followup_advisor-taak.
    all_reviews = (
        await db.execute(
            select(WorkflowTask).where(
                WorkflowTask.tenant_id == test_tenant.id,
                WorkflowTask.case_id == case.id,
                WorkflowTask.task_type == "manual_review",
            )
        )
    ).scalars().all()
    assert len(all_reviews) == 1
    assert all_reviews[0].action_config["source"] == "followup_escalate"
