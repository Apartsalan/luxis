"""Wachters (S242, S241 voorstel 3): wie krijgt de te-laat-melding van een taak.

De dagelijkse meldingen-job stuurde de melding voor een taak zónder eigenaar
naar de 'eerste' gebruiker van het kantoor — willekeurige volgorde, dus de
melding kon stil bij de verkeerde landen. Nu: eigenaarloze taken worden bij
álle actieve gebruikers gemeld, consistent met de werklijst (die eigenaarloze
taken ook aan iedereen toont). Taken mét eigenaar blijven alleen bij die
eigenaar; de 30-dagen-dedup per (gebruiker, zaak, taak) blijft gelden.
"""

import uuid
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.auth.models import User
from app.auth.service import hash_password
from app.notifications.models import Notification
from app.workflow.models import WorkflowTask
from app.workflow.scheduler import daily_deadline_notifications
from tests.helpers.incasso_fixtures import create_incasso_case


async def _second_user(db, tenant_id) -> User:
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="tweede@kestinglegal.nl",
        hashed_password=hash_password("testpassword123"),
        full_name="Tweede Gebruiker",
        role="advocaat",
    )
    db.add(user)
    await db.flush()
    return user


async def _overdue_task(db, tenant_id, case_id, *, assigned_to_id=None) -> WorkflowTask:
    task = WorkflowTask(
        tenant_id=tenant_id,
        case_id=case_id,
        assigned_to_id=assigned_to_id,
        task_type="manual_review",
        title="Te late taak",
        due_date=date.today() - timedelta(days=2),
        status="overdue",
        auto_execute=False,
        action_config={"source": "test"},
    )
    db.add(task)
    await db.flush()
    return task


async def _notified_user_ids(db, task_id) -> set:
    result = await db.execute(
        select(Notification.user_id).where(
            Notification.task_id == task_id,
            Notification.type == "deadline_overdue",
        )
    )
    return {row[0] for row in result.all()}


@pytest.mark.asyncio
async def test_ownerless_overdue_task_notifies_all_active_users(
    db, test_tenant, test_user, test_company, session_factory
):
    """Taak zonder eigenaar → melding bij álle actieve gebruikers (was: users[0])."""
    other = await _second_user(db, test_tenant.id)
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09831"
    )
    task = await _overdue_task(db, test_tenant.id, case.id, assigned_to_id=None)
    await db.commit()  # job draait op eigen sessies

    with patch("app.workflow.scheduler.async_session", session_factory):
        await daily_deadline_notifications()

    assert await _notified_user_ids(db, task.id) == {test_user.id, other.id}


@pytest.mark.asyncio
async def test_owned_overdue_task_notifies_only_owner(
    db, test_tenant, test_user, test_company, session_factory
):
    """Tegenproef: taak mét eigenaar → alleen die eigenaar krijgt de melding."""
    other = await _second_user(db, test_tenant.id)
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09832"
    )
    task = await _overdue_task(db, test_tenant.id, case.id, assigned_to_id=other.id)
    await db.commit()

    with patch("app.workflow.scheduler.async_session", session_factory):
        await daily_deadline_notifications()

    assert await _notified_user_ids(db, task.id) == {other.id}


@pytest.mark.asyncio
async def test_ownerless_notification_dedup_holds(
    db, test_tenant, test_user, test_company, session_factory
):
    """De 30-dagen-dedup per (gebruiker, zaak, taak) blijft gelden: de job twee
    keer draaien geeft nog steeds precies één melding per gebruiker."""
    other = await _second_user(db, test_tenant.id)
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09833"
    )
    task = await _overdue_task(db, test_tenant.id, case.id, assigned_to_id=None)
    await db.commit()

    with patch("app.workflow.scheduler.async_session", session_factory):
        await daily_deadline_notifications()
        await daily_deadline_notifications()

    result = await db.execute(
        select(Notification.user_id).where(
            Notification.task_id == task.id,
            Notification.type == "deadline_overdue",
        )
    )
    per_user: dict = {}
    for (user_id,) in result.all():
        per_user[user_id] = per_user.get(user_id, 0) + 1
    assert per_user == {test_user.id: 1, other.id: 1}
