"""Wachters (S235, Gat C): de pijplijn schuift mee met de betalingsregeling.

- Regeling aangemaakt → zaak naar hold-stap 'Bijhouden regeling' (beide
  aanmaak-wegen: gelijke termijnen én flexibel schema).
- Géén zet bij een gesloten zaak of openstaand verweer (de checks die hier
  gelden; de hold-blokkade van advance_guard_reason geldt hier bewust NIET).
- Stap bestaat niet → regeling ontstaat gewoon, zaak blijft staan (geen crash).
- Regeling verbroken (wanprestatie) → eenmalige taak 'vervolg bepalen', via
  BEIDE routes (default_arrangement én update_arrangement) — gededuped.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.collections.schemas import ArrangementCreate, ArrangementUpdate
from app.collections.service import (
    create_arrangement,
    default_arrangement,
    update_arrangement,
)
from app.incasso.models import IncassoPipelineStep
from app.workflow.models import WorkflowTask
from tests.helpers.incasso_fixtures import create_incasso_case


async def _regeling_step(db, tenant_id) -> IncassoPipelineStep:
    step = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name="Bijhouden regeling",
        sort_order=50, min_wait_days=0, max_wait_days=0,
        step_category="regeling", is_hold_step=True,
    )
    db.add(step)
    await db.flush()
    return step


def _equal_schedule() -> ArrangementCreate:
    return ArrangementCreate(
        total_amount=Decimal("900.00"),
        num_installments=3,
        frequency="monthly",
        start_date=date.today() + timedelta(days=7),
    )


def _flexible_schedule() -> ArrangementCreate:
    return ArrangementCreate(
        total_amount=Decimal("1400.00"),
        start_date=date.today() + timedelta(days=7),
        installments=[
            {"due_date": date.today() + timedelta(days=7), "amount": Decimal("200.00")},
            {"due_date": date.today() + timedelta(days=37), "amount": Decimal("200.00")},
            {"due_date": date.today() + timedelta(days=67), "amount": Decimal("1000.00")},
        ],
    )


async def _defaulted_tasks(db, tenant_id, case_id) -> list[WorkflowTask]:
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.case_id == case_id,
            WorkflowTask.action_config["source"].astext == "arrangement_defaulted",
        )
    )
    return list(result.scalars().all())


@pytest.mark.asyncio
@pytest.mark.parametrize("schedule_factory", [_equal_schedule, _flexible_schedule])
async def test_new_arrangement_moves_case_to_hold_step(
    db, test_tenant, test_user, test_company, schedule_factory
):
    step = await _regeling_step(db, test_tenant.id)
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user,
        case_number=f"2026-096{'01' if schedule_factory is _equal_schedule else '02'}",
    )

    await create_arrangement(db, test_tenant.id, case.id, schedule_factory())

    await db.refresh(case)
    assert case.incasso_step_id == step.id


@pytest.mark.asyncio
async def test_no_move_for_closed_case_or_verweer(
    db, test_tenant, test_user, test_company
):
    step = await _regeling_step(db, test_tenant.id)

    closed = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user,
        case_number="2026-09603", status="afgesloten",
    )
    await create_arrangement(db, test_tenant.id, closed.id, _equal_schedule())
    await db.refresh(closed)
    assert closed.incasso_step_id != step.id
    assert closed.status == "afgesloten"

    verweer = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09604"
    )
    verweer.has_verweer = True
    await db.flush()
    await create_arrangement(db, test_tenant.id, verweer.id, _equal_schedule())
    await db.refresh(verweer)
    assert verweer.incasso_step_id != step.id


@pytest.mark.asyncio
async def test_missing_step_is_harmless(db, test_tenant, test_user, test_company):
    """Geen 'Bijhouden regeling'-stap → regeling ontstaat gewoon, geen crash."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09605"
    )
    arr = await create_arrangement(db, test_tenant.id, case.id, _equal_schedule())
    assert arr.status == "active"
    await db.refresh(case)
    assert case.incasso_step_id is None


@pytest.mark.asyncio
async def test_defaulted_creates_task_via_both_routes_deduped(
    db, test_tenant, test_user, test_company
):
    """Wanprestatie → taak 'vervolg bepalen'; beide routes, nooit dubbel."""
    await _regeling_step(db, test_tenant.id)

    # Route 1: de dedicated wanprestatie-knop
    case1 = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09606"
    )
    arr1 = await create_arrangement(db, test_tenant.id, case1.id, _equal_schedule())
    await default_arrangement(db, test_tenant.id, arr1.id)
    tasks = await _defaulted_tasks(db, test_tenant.id, case1.id)
    assert len(tasks) == 1
    assert "Regeling verbroken" in tasks[0].title

    # Route 2: de generieke update-route
    case2 = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09607"
    )
    arr2 = await create_arrangement(db, test_tenant.id, case2.id, _equal_schedule())
    await update_arrangement(
        db, test_tenant.id, arr2.id, ArrangementUpdate(status="defaulted")
    )
    tasks = await _defaulted_tasks(db, test_tenant.id, case2.id)
    assert len(tasks) == 1

    # Dedupe: nogmaals defaulted zetten via de update-route → geen tweede taak
    await update_arrangement(
        db, test_tenant.id, arr2.id, ArrangementUpdate(status="defaulted")
    )
    tasks = await _defaulted_tasks(db, test_tenant.id, case2.id)
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_cancel_or_complete_creates_no_task(
    db, test_tenant, test_user, test_company
):
    """Alleen wanprestatie krijgt een taak — annuleren/afronden niet."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09608"
    )
    arr = await create_arrangement(db, test_tenant.id, case.id, _equal_schedule())
    await update_arrangement(
        db, test_tenant.id, arr.id, ArrangementUpdate(status="cancelled")
    )
    assert await _defaulted_tasks(db, test_tenant.id, case.id) == []
