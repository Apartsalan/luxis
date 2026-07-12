"""Tests for workflow tasks, calendar, payments, and verjaring."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.cases.models import Case
from app.relations.models import Contact

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_contact(db: AsyncSession, tenant_id: uuid.UUID) -> Contact:
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Test Client B.V.",
        email="test@testclient.nl",
    )
    db.add(contact)
    await db.flush()
    return contact


async def _create_case(
    db: AsyncSession, tenant_id: uuid.UUID, case_number: str = "2026-00001"
) -> Case:
    client = await _create_contact(db, tenant_id)
    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number=case_number,
        case_type="incasso",
        status="nieuw",
        debtor_type="b2b",
        date_opened=date(2026, 1, 15),
        client_id=client.id,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


# ── Tasks ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_task(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Creating a task should return 201 with correct fields."""
    case = await _create_case(db, test_tenant.id)

    payload = {
        "case_id": str(case.id),
        "task_type": "manual_review",
        "title": "Controleer betalingsbewijs",
        "description": "Debiteur claimt betaald te hebben",
        "due_date": (date.today() + timedelta(days=30)).isoformat(),
    }
    resp = await client.post("/api/workflow/tasks", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Controleer betalingsbewijs"
    assert data["task_type"] == "manual_review"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_tasks_filter_by_case(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Filtering tasks by case_id should return only that case's tasks."""
    case_a = await _create_case(db, test_tenant.id, "2026-00001")
    case_b = await _create_case(db, test_tenant.id, "2026-00002")

    for case in [case_a, case_a, case_b]:
        await client.post(
            "/api/workflow/tasks",
            json={
                "case_id": str(case.id),
                "task_type": "check_payment",
                "title": f"Task for {case.case_number}",
                "due_date": "2026-03-15",
            },
            headers=auth_headers,
        )

    resp = await client.get(f"/api/workflow/tasks?case_id={case_a.id}", headers=auth_headers)
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_update_task_to_completed(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Completing a task should set completed_at."""
    case = await _create_case(db, test_tenant.id)

    create_resp = await client.post(
        "/api/workflow/tasks",
        json={
            "case_id": str(case.id),
            "task_type": "check_payment",
            "title": "Check payment",
            "due_date": "2026-03-15",
        },
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/workflow/tasks/{task_id}",
        json={"status": "completed"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["completed_at"] is not None


@pytest.mark.asyncio
async def test_delete_task(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Deleting a task should soft-delete it (204)."""
    case = await _create_case(db, test_tenant.id)

    create_resp = await client.post(
        "/api/workflow/tasks",
        json={
            "case_id": str(case.id),
            "task_type": "manual_review",
            "title": "To be deleted",
            "due_date": "2026-03-15",
        },
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/workflow/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 204

    # Should not appear in list
    list_resp = await client.get(f"/api/workflow/tasks?case_id={case.id}", headers=auth_headers)
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_invalid_task_type_rejected(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Invalid task_type should be rejected (400)."""
    case = await _create_case(db, test_tenant.id)

    resp = await client.post(
        "/api/workflow/tasks",
        json={
            "case_id": str(case.id),
            "task_type": "invalid_type",
            "title": "Bad task",
            "due_date": "2026-03-15",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ── Calendar ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_calendar_events(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Calendar should return tasks within the date range."""
    case = await _create_case(db, test_tenant.id)

    # Create task due March 15
    await client.post(
        "/api/workflow/tasks",
        json={
            "case_id": str(case.id),
            "task_type": "check_payment",
            "title": "Check betaling",
            "due_date": "2026-03-15",
        },
        headers=auth_headers,
    )

    resp = await client.get(
        "/api/workflow/calendar?date_from=2026-03-01&date_to=2026-03-31",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 1
    assert events[0]["event_type"] == "task"
    assert events[0]["title"] == "Check betaling"


# ── Verjaring ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verjaring_check(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """Verjaring check should flag cases approaching 5-year deadline."""
    contact = await _create_contact(db, test_tenant.id)

    # Create a case opened almost 5 years ago (within 90-day warning)
    old_date = date.today() - timedelta(days=5 * 365 - 30)
    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2021-00001",
        case_type="incasso",
        status="in_behandeling",
        debtor_type="b2b",
        date_opened=old_date,
        client_id=contact.id,
    )
    db.add(case)
    await db.commit()

    resp = await client.get("/api/workflow/verjaring", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["case_number"] == "2021-00001"
    assert data[0]["days_remaining"] <= 90


# ── S198-review: handmatig 'betaald' + symmetrische heropening ────────────────


def _case_with_open_claim(tenant_id, client_id, case_number, status="nieuw"):
    """Case + rente + openstaande vordering van €5000 (geen betaling)."""
    from decimal import Decimal

    from app.collections.models import Claim, InterestRate

    rate = InterestRate(
        id=uuid.uuid4(), rate_type="statutory",
        effective_from=date(2024, 1, 1), rate=Decimal("6.00"), source="Test fixture",
    )
    case = Case(
        id=uuid.uuid4(), tenant_id=tenant_id, case_number=case_number,
        case_type="incasso", debtor_type="b2b", status=status, is_active=True,
        client_id=client_id, date_opened=date.today(),
        total_principal=Decimal("5000.00"), total_paid=Decimal("0.00"),
    )
    claim = Claim(
        id=uuid.uuid4(), tenant_id=tenant_id, case_id=case.id, description="Factuur",
        principal_amount=Decimal("5000.00"), default_date=date.today() - timedelta(days=60),
    )
    return rate, case, claim


@pytest.mark.asyncio
async def test_manual_betaald_blocked_when_outstanding(
    db: AsyncSession, test_tenant: Tenant, test_user, test_company: Contact
):
    """Codex #2: de status-API mag een zaak niet handmatig op 'betaald' zetten
    zolang er nog een saldo openstaat — dat hoort via 'Afsluiten' (afgesloten)."""
    from app.cases.schemas import CaseStatusUpdate
    from app.cases.service import update_case_status
    from app.shared.exceptions import BadRequestError

    rate, case, claim = _case_with_open_claim(
        test_tenant.id, test_company.id, "2026-08050"
    )
    db.add_all([rate, case, claim])
    await db.commit()

    with pytest.raises(BadRequestError, match="open"):
        await update_case_status(
            db, test_tenant.id, case.id, test_user.id,
            CaseStatusUpdate(new_status="betaald"),
        )


@pytest.mark.asyncio
async def test_reopen_helper_reopens_paid_case_when_balance_returns(
    db: AsyncSession, test_tenant: Tenant, test_company: Contact
):
    """Codex #4: draait een betaling terug (saldo weer open) terwijl de zaak op
    'betaald' stond, dan heropent de helper de zaak (in_behandeling, sluitdatum leeg)."""
    from app.collections.service import _reopen_case_if_no_longer_paid

    rate, case, claim = _case_with_open_claim(
        test_tenant.id, test_company.id, "2026-08051", status="betaald"
    )
    case.date_closed = date.today()
    db.add_all([rate, case, claim])
    await db.commit()

    await _reopen_case_if_no_longer_paid(db, test_tenant.id, case.id)
    await db.refresh(case)
    assert case.status == "in_behandeling"
    assert case.date_closed is None


# ── Effective task status (AUDIT-H22) ────────────────────────────────────────


def test_effective_task_status_helper():
    """Open tasks derive status from due_date; terminal statuses are kept."""
    from app.workflow.schemas import effective_task_status

    today = date(2026, 6, 2)
    assert effective_task_status("pending", today - timedelta(days=1), today) == "overdue"
    assert effective_task_status("due", today - timedelta(days=5), today) == "overdue"
    assert effective_task_status("pending", today, today) == "due"
    assert effective_task_status("pending", today + timedelta(days=3), today) == "pending"
    # Terminal statuses stay authoritative even when past due.
    assert effective_task_status("completed", today - timedelta(days=10), today) == "completed"
    assert effective_task_status("skipped", today - timedelta(days=10), today) == "skipped"


@pytest.mark.asyncio
async def test_task_response_status_overdue_when_past_due(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """A past-due task still stored as 'pending' (daily batch not run) must
    serialize as 'overdue' in the takenlijst response (AUDIT-H22)."""
    case = await _create_case(db, test_tenant.id, "2026-09001")
    resp = await client.post(
        "/api/workflow/tasks",
        json={
            "case_id": str(case.id),
            "task_type": "manual_review",
            "title": "Verlopen taak",
            "due_date": (date.today() - timedelta(days=3)).isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    # Stored status is 'pending' (column default); the response derives 'overdue'.
    assert resp.json()["status"] == "overdue"

    listed = await client.get(
        f"/api/workflow/tasks?case_id={case.id}", headers=auth_headers
    )
    assert listed.status_code == 200
    assert listed.json()[0]["status"] == "overdue"


@pytest.mark.asyncio
async def test_calendar_event_overdue_status_and_color_from_due_date(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """A past-due task on the agenda must be 'overdue' + red, not 'pending' +
    blue, even when the daily batch hasn't materialized the status (AUDIT-H22)."""
    case = await _create_case(db, test_tenant.id, "2026-09002")
    due = date.today() - timedelta(days=2)
    await client.post(
        "/api/workflow/tasks",
        json={
            "case_id": str(case.id),
            "task_type": "check_payment",
            "title": "Verlopen agenda-taak",
            "due_date": due.isoformat(),
        },
        headers=auth_headers,
    )
    date_from = (due - timedelta(days=1)).isoformat()
    date_to = (date.today() + timedelta(days=1)).isoformat()
    resp = await client.get(
        f"/api/workflow/calendar?date_from={date_from}&date_to={date_to}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    events = [e for e in resp.json() if e["title"] == "Verlopen agenda-taak"]
    assert len(events) == 1
    assert events[0]["status"] == "overdue"
    assert events[0]["color"] == "#ef4444"


# ── Verjaring leap-day crash (AUDIT-MEDIUM) ──────────────────────────────────


@pytest.mark.asyncio
async def test_check_verjaring_handles_leap_day_date_opened(
    db: AsyncSession,
    test_tenant: Tenant,
    test_company: Contact,
):
    """check_verjaring must not crash on a leap-day date_opened. date_opened +5y
    landed on 29 Feb of a non-leap year, and date.replace(year=...) raised
    ValueError — verjaring-checks crashed for any case opened on 29 Feb."""
    from decimal import Decimal

    from app.workflow.service import check_verjaring

    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-LEAP1",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        is_active=True,
        client_id=test_company.id,
        date_opened=date(2020, 2, 29),  # 2025 has no 29 Feb
        date_closed=None,
        total_principal=Decimal("0.00"),
        total_paid=Decimal("0.00"),
    )
    db.add(case)
    await db.commit()

    warnings = await check_verjaring(db, test_tenant.id)
    mine = [w for w in warnings if w["case_number"] == "2026-LEAP1"]
    assert len(mine) == 1
    assert mine[0]["verjaring_date"] == "2025-02-28"
    assert mine[0]["is_expired"] is True


@pytest.mark.asyncio
async def test_check_verjaring_uses_oldest_claim_default_date(
    db: AsyncSession,
    test_tenant: Tenant,
    test_company: Contact,
):
    """Audit #83: verjaring (art. 3:307 BW) loopt vanaf opeisbaarheid van de
    vordering (oudste claims.default_date), niet vanaf dossier-opening. Een
    recent geopend dossier met een bijna-verjaarde vordering moet dus wél
    een waarschuwing geven."""
    from decimal import Decimal

    from dateutil.relativedelta import relativedelta

    from app.collections.models import Claim
    from app.workflow.service import check_verjaring

    almost_expired = date.today() - relativedelta(years=5) + timedelta(days=30)
    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-VERJ1",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        is_active=True,
        client_id=test_company.id,
        date_opened=date.today() - timedelta(days=10),  # net geopend
        date_closed=None,
        total_principal=Decimal("1000.00"),
        total_paid=Decimal("0.00"),
    )
    db.add(case)
    db.add(
        Claim(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_id=case.id,
            description="Oude vordering",
            principal_amount=Decimal("1000.00"),
            default_date=almost_expired,
        )
    )
    await db.commit()

    warnings = await check_verjaring(db, test_tenant.id)
    mine = [w for w in warnings if w["case_number"] == "2026-VERJ1"]
    assert len(mine) == 1, "bijna-verjaarde vordering moet waarschuwen, ook op vers dossier"
    assert mine[0]["basis_date"] == almost_expired.isoformat()
    assert 0 < mine[0]["days_remaining"] <= 90
    assert mine[0]["is_expired"] is False


@pytest.mark.asyncio
async def test_check_verjaring_includes_reopened_case_with_date_closed(
    db: AsyncSession, test_tenant: Tenant, test_company: Contact
):
    """B2 — een heropende zaak draagt een oude `date_closed` uit de BaseNet-import
    maar is inhoudelijk actief (status is niet terminaal). De monitor moet 'm meenemen."""
    from decimal import Decimal

    from dateutil.relativedelta import relativedelta

    from app.collections.models import Claim
    from app.workflow.service import check_verjaring

    almost_expired = date.today() - relativedelta(years=5) + timedelta(days=30)
    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-VERJREOPEN",
        case_type="incasso",
        debtor_type="b2b",
        status="in_behandeling",  # actief, niet afgesloten
        is_active=True,
        client_id=test_company.id,
        date_opened=date.today() - timedelta(days=2000),
        date_closed=date.today() - timedelta(days=400),  # oude sluitdatum uit import
        total_principal=Decimal("1000.00"),
        total_paid=Decimal("0.00"),
    )
    db.add(case)
    db.add(
        Claim(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_id=case.id,
            description="Oude vordering",
            principal_amount=Decimal("1000.00"),
            default_date=almost_expired,
        )
    )
    await db.commit()

    warnings = await check_verjaring(db, test_tenant.id)
    assert any(w["case_number"] == "2026-VERJREOPEN" for w in warnings), (
        "heropende zaak met oude date_closed moet gemonitord worden"
    )


@pytest.mark.asyncio
async def test_check_verjaring_skips_paid_and_closed_status(
    db: AsyncSession, test_tenant: Tenant, test_company: Contact
):
    """B2 — betaalde/afgesloten zaken geven géén verjaringswaarschuwing, ook al
    is er een bijna-verjaarde vordering."""
    from decimal import Decimal

    from dateutil.relativedelta import relativedelta

    from app.collections.models import Claim
    from app.workflow.service import check_verjaring

    almost_expired = date.today() - relativedelta(years=5) + timedelta(days=30)
    for status_val, nr in (("betaald", "2026-VERJPAID"), ("afgesloten", "2026-VERJCLOSED")):
        case = Case(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_number=nr,
            case_type="incasso",
            debtor_type="b2b",
            status=status_val,
            is_active=True,
            client_id=test_company.id,
            date_opened=date.today() - timedelta(days=2000),
            date_closed=None,
            total_principal=Decimal("1000.00"),
            total_paid=Decimal("1000.00"),
        )
        db.add(case)
        db.add(
            Claim(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                case_id=case.id,
                description="Oude vordering",
                principal_amount=Decimal("1000.00"),
                default_date=almost_expired,
            )
        )
    await db.commit()

    warnings = await check_verjaring(db, test_tenant.id)
    nrs = {w["case_number"] for w in warnings}
    assert "2026-VERJPAID" not in nrs
    assert "2026-VERJCLOSED" not in nrs


def test_compute_verjaring_date_clamps_leap_day():
    """Codex-review portie 2: 29 feb + 5 jaar = 28 feb (dateutil klemt), zodat
    badge en monitor exact dezelfde datum tonen."""
    from app.cases.service import compute_verjaring_date

    assert compute_verjaring_date(date(2024, 2, 29)) == date(2029, 2, 28)
    assert compute_verjaring_date(date(2024, 3, 1)) == date(2029, 3, 1)


@pytest.mark.asyncio
async def test_list_tasks_include_unassigned(
    db: AsyncSession, test_tenant: Tenant, test_user: User, test_company: Contact
):
    """A1 — met include_unassigned komen óók eigenaarloze tenant-taken mee
    (zoals de verjaring-alarmen van de monitor)."""
    from app.workflow.models import WorkflowTask
    from app.workflow.service import list_tasks

    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-TASKS",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        is_active=True,
        client_id=test_company.id,
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()

    mine = WorkflowTask(
        tenant_id=test_tenant.id, case_id=case.id, assigned_to_id=test_user.id,
        task_type="manual_review", title="Mijn taak", due_date=date.today(), status="due",
    )
    ownerless = WorkflowTask(
        tenant_id=test_tenant.id, case_id=case.id, assigned_to_id=None,
        task_type="verjaring_warning", title="VERJARING: eigenaarloos",
        due_date=date.today(), status="overdue",
    )
    db.add_all([mine, ownerless])
    await db.commit()

    only_mine = await list_tasks(db, test_tenant.id, assigned_to_id=test_user.id)
    titles_mine = {t.title for t in only_mine}
    assert "Mijn taak" in titles_mine
    assert "VERJARING: eigenaarloos" not in titles_mine

    with_unassigned = await list_tasks(
        db, test_tenant.id, assigned_to_id=test_user.id, include_unassigned=True
    )
    titles_both = {t.title for t in with_unassigned}
    assert "Mijn taak" in titles_both
    assert "VERJARING: eigenaarloos" in titles_both


@pytest.mark.asyncio
async def test_get_verjaring_basis_date_uses_oldest_claim(
    db: AsyncSession, test_tenant: Tenant, test_company: Contact
):
    """B2 — badge-basisdatum = verzuimdatum oudste actieve vordering; terugval op
    de openingsdatum als er geen vorderingen zijn."""
    from decimal import Decimal

    from app.cases.service import get_verjaring_basis_date
    from app.collections.models import Claim

    opened = date(2024, 1, 1)
    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-BASIS",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        is_active=True,
        client_id=test_company.id,
        date_opened=opened,
    )
    db.add(case)
    await db.flush()

    # Geen vorderingen → terugval openingsdatum
    assert await get_verjaring_basis_date(db, test_tenant.id, case) == opened

    older = date(2022, 3, 5)
    db.add_all([
        Claim(id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
              description="Nieuwere", principal_amount=Decimal("100.00"),
              default_date=date(2023, 6, 1)),
        Claim(id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
              description="Oudste", principal_amount=Decimal("100.00"),
              default_date=older),
    ])
    await db.commit()

    assert await get_verjaring_basis_date(db, test_tenant.id, case) == older


# ── System task types in canonical TASK_TYPES (AUDIT-MEDIUM) ──────────────────


def test_system_created_task_types_are_canonical():
    """Task types the scheduler/automation persist directly must be in TASK_TYPES.

    workflow/scheduler.py creates 'verjaring_warning' and
    incasso/automation_service.py creates 'review_ai_draft' via WorkflowTask(...).
    If they are absent from TASK_TYPES, create_task / create_rule validation
    rejects them as 'Ongeldig taaktype' (AUDIT-MEDIUM)."""
    from app.workflow.schemas import TASK_TYPES

    assert "verjaring_warning" in TASK_TYPES
    assert "review_ai_draft" in TASK_TYPES


@pytest.mark.asyncio
async def test_create_review_ai_draft_task_accepted(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    """A 'review_ai_draft' task must be accepted by create_task (AUDIT-MEDIUM).

    The incasso automation creates these; the manual API path used the same
    TASK_TYPES guard, so before the fix this returned 400 'Ongeldig taaktype'."""
    case = await _create_case(db, test_tenant.id, "2026-09010")
    resp = await client.post(
        "/api/workflow/tasks",
        json={
            "case_id": str(case.id),
            "task_type": "review_ai_draft",
            "title": "Review concept-email",
            "due_date": (date.today() + timedelta(days=2)).isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["task_type"] == "review_ai_draft"
