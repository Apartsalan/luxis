"""Unit tests for notification service helpers added in S146 (BUG-84).

Covers the three new create_* functions used by CaseActionFeed:
  - create_email_received_notification
  - create_draft_ready_notification
  - create_classification_done_notification

Each test verifies (a) a notification is created, (b) dedup behavior prevents
duplicates within the configured window.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.notifications.models import Notification
from app.notifications.schemas import NotificationCreate
from app.notifications.service import (
    NOTIF_AI_DRAFT_READY,
    NOTIF_CLASSIFICATION_DONE,
    NOTIF_EMAIL_RECEIVED,
    create_classification_done_notification,
    create_draft_ready_notification,
    create_email_received_notification,
    create_notification_if_not_exists,
)
from app.relations.models import Contact


async def _make_case(
    db: AsyncSession, tenant_id: uuid.UUID, case_number: str = "2026-00099"
) -> Case:
    """Minimal Case row + client contact so notifications FK is satisfied."""
    client = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name=f"Cliënt voor {case_number}",
    )
    db.add(client)
    await db.flush()

    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number=case_number,
        case_type="incasso",
        status="sommatie",
        client_id=client.id,
        total_principal=Decimal("1500.00"),
        total_paid=Decimal("0.00"),
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()
    return case


async def _count(db: AsyncSession, tenant_id, type_: str) -> int:
    result = await db.execute(
        select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.type == type_,
        )
    )
    return len(list(result.scalars().all()))


@pytest.mark.asyncio
async def test_create_email_received_notification(
    db: AsyncSession, test_user: User, test_tenant: Tenant
):
    """Single inbound email creates exactly one notification per active user."""
    case = await _make_case(db, test_tenant.id, "2026-00001")
    created = await create_email_received_notification(
        db,
        test_tenant.id,
        case.id,
        case.case_number,
        "Jan de Vries",
        "Antwoord op aanmaning",
    )
    await db.flush()

    assert created == 1
    count = await _count(db, test_tenant.id, NOTIF_EMAIL_RECEIVED)
    assert count == 1


@pytest.mark.asyncio
async def test_email_received_dedup_within_window(
    db: AsyncSession, test_user: User, test_tenant: Tenant
):
    """Calling twice with the same case + subject inside the dedup window
    must not produce a second notification."""
    case = await _make_case(db, test_tenant.id, "2026-00002")
    subject = "Re: factuur 2026-00002"

    first = await create_email_received_notification(
        db, test_tenant.id, case.id, case.case_number, "Jan", subject
    )
    second = await create_email_received_notification(
        db, test_tenant.id, case.id, case.case_number, "Jan", subject
    )
    await db.flush()

    assert first == 1
    assert second == 0  # deduped
    count = await _count(db, test_tenant.id, NOTIF_EMAIL_RECEIVED)
    assert count == 1


@pytest.mark.asyncio
async def test_create_draft_ready_notification(
    db: AsyncSession, test_user: User, test_tenant: Tenant
):
    """Draft-ready notification is created with intent label in the title."""
    case = await _make_case(db, test_tenant.id, "2026-00003")
    created = await create_draft_ready_notification(
        db,
        test_tenant.id,
        case.id,
        case.case_number,
        "next_step",
        "Geachte heer, hierbij verzoeken wij u ...",
    )
    await db.flush()

    assert created == 1
    result = await db.execute(
        select(Notification).where(
            Notification.tenant_id == test_tenant.id,
            Notification.type == NOTIF_AI_DRAFT_READY,
        )
    )
    notif = result.scalar_one()
    assert "volgende stap" in notif.title.lower()
    assert "Geachte heer" in notif.message


@pytest.mark.asyncio
async def test_create_classification_done_notification(
    db: AsyncSession, test_user: User, test_tenant: Tenant
):
    """Classification notification includes sentiment-driven tone label."""
    case = await _make_case(db, test_tenant.id, "2026-00004")
    created = await create_classification_done_notification(
        db,
        test_tenant.id,
        case.id,
        case.case_number,
        category="dispute",
        sentiment="streng",
        from_label="Pietersen",
    )
    await db.flush()

    assert created == 1
    result = await db.execute(
        select(Notification).where(
            Notification.tenant_id == test_tenant.id,
            Notification.type == NOTIF_CLASSIFICATION_DONE,
        )
    )
    notif = result.scalar_one()
    assert "streng" in notif.title
    assert "Pietersen" in notif.message


@pytest.mark.asyncio
async def test_dedup_distinguishes_tasks_on_same_case(
    db: AsyncSession, test_user: User, test_tenant: Tenant
):
    """Two overdue tasks on the same case must yield two notifications.

    Before the S146 fix, dedup only matched on (tenant, user, type, case_id),
    so different tasks collapsed into one notification.
    """
    case = await _make_case(db, test_tenant.id, "2026-00050")
    task_a = uuid.uuid4()
    task_b = uuid.uuid4()

    first = await create_notification_if_not_exists(
        db,
        test_tenant.id,
        test_user.id,
        NotificationCreate(
            type="deadline_overdue",
            title="Taak te laat: A",
            message="Deadline was 15-05-2026",
            case_id=case.id,
            task_id=task_a,
        ),
        dedup_hours=24 * 30,
    )
    second = await create_notification_if_not_exists(
        db,
        test_tenant.id,
        test_user.id,
        NotificationCreate(
            type="deadline_overdue",
            title="Taak te laat: B",
            message="Deadline was 16-05-2026",
            case_id=case.id,
            task_id=task_b,
        ),
        dedup_hours=24 * 30,
    )
    # Same task again — must dedup
    duplicate = await create_notification_if_not_exists(
        db,
        test_tenant.id,
        test_user.id,
        NotificationCreate(
            type="deadline_overdue",
            title="Taak te laat: A",
            message="Deadline was 15-05-2026",
            case_id=case.id,
            task_id=task_a,
        ),
        dedup_hours=24 * 30,
    )
    await db.flush()

    assert first is not None
    assert second is not None
    assert duplicate is None
    count = await _count(db, test_tenant.id, "deadline_overdue")
    assert count == 2


@pytest.mark.asyncio
async def test_tenant_isolation_between_users(
    db: AsyncSession,
    test_user: User,
    test_tenant: Tenant,
    second_user: User,
    second_tenant: Tenant,
):
    """Notifications for tenant A do not leak to tenant B."""
    case = await _make_case(db, test_tenant.id, "2026-00010")
    await create_email_received_notification(
        db, test_tenant.id, case.id, case.case_number, "X", "Subj"
    )
    await db.flush()

    a_count = await _count(db, test_tenant.id, NOTIF_EMAIL_RECEIVED)
    b_count = await _count(db, second_tenant.id, NOTIF_EMAIL_RECEIVED)
    assert a_count == 1
    assert b_count == 0
