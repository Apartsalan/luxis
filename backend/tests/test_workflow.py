"""Tests for the workflow module — statuses, transitions, tasks, rules, calendar."""

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


# ── Statuses ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_statuses(client: AsyncClient, auth_headers: dict, workflow_data: dict):
    """List statuses should return all seeded statuses."""
    resp = await client.get("/api/workflow/statuses", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 10  # We seeded 15 statuses
    slugs = [s["slug"] for s in data]
    assert "nieuw" in slugs
    assert "betaald" in slugs


@pytest.mark.asyncio
async def test_create_status(client: AsyncClient, auth_headers: dict, workflow_data: dict):
    """Creating a new status should return 201."""
    payload = {
        "slug": "test_status",
        "label": "Test Status",
        "phase": "minnelijk",
        "sort_order": 99,
        "color": "#ff0000",
    }
    resp = await client.post("/api/workflow/statuses", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["slug"] == "test_status"
    assert resp.json()["label"] == "Test Status"


@pytest.mark.asyncio
async def test_create_duplicate_slug_fails(
    client: AsyncClient, auth_headers: dict, workflow_data: dict
):
    """Creating a status with existing slug should fail (409)."""
    payload = {
        "slug": "nieuw",
        "label": "Duplicate",
        "phase": "minnelijk",
    }
    resp = await client.post("/api/workflow/statuses", json=payload, headers=auth_headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_status(client: AsyncClient, auth_headers: dict, workflow_data: dict):
    """Updating a status should change the specified fields."""
    status_id = str(workflow_data["herinnering"])
    resp = await client.put(
        f"/api/workflow/statuses/{status_id}",
        json={"label": "Herinnering (aangepast)", "color": "#00ff00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["label"] == "Herinnering (aangepast)"
    assert resp.json()["color"] == "#00ff00"


@pytest.mark.asyncio
async def test_delete_unused_status(client: AsyncClient, auth_headers: dict, workflow_data: dict):
    """Deleting an unused status should succeed (204)."""
    # Create a status that's not used by any case
    create_resp = await client.post(
        "/api/workflow/statuses",
        json={"slug": "temp_status", "label": "Temp", "phase": "minnelijk"},
        headers=auth_headers,
    )
    temp_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/workflow/statuses/{temp_id}", headers=auth_headers)
    assert resp.status_code == 204


# ── Transitions ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_transitions(client: AsyncClient, auth_headers: dict, workflow_data: dict):
    """List transitions should return seeded transitions."""
    resp = await client.get("/api/workflow/transitions", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 10  # Many transitions seeded


@pytest.mark.asyncio
async def test_allowed_transitions_from_nieuw(
    client: AsyncClient, auth_headers: dict, workflow_data: dict
):
    """Allowed transitions from 'nieuw' should include herinnering and betaald."""
    resp = await client.get(
        "/api/workflow/transitions/allowed?from_status=nieuw&debtor_type=b2b",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    slugs = [t["to_slug"] for t in resp.json()]
    assert "herinnering" in slugs
    assert "betaald" in slugs


@pytest.mark.asyncio
async def test_b2c_transitions_include_14_dagenbrief(
    client: AsyncClient, auth_headers: dict, workflow_data: dict
):
    """B2C transitions from 'nieuw' should include 14_dagenbrief."""
    resp = await client.get(
        "/api/workflow/transitions/allowed?from_status=nieuw&debtor_type=b2c",
        headers=auth_headers,
    )
    slugs = [t["to_slug"] for t in resp.json()]
    assert "14_dagenbrief" in slugs


@pytest.mark.asyncio
async def test_b2b_transitions_include_sommatie(
    client: AsyncClient, auth_headers: dict, workflow_data: dict
):
    """B2B transitions from 'nieuw' should include direct sommatie."""
    resp = await client.get(
        "/api/workflow/transitions/allowed?from_status=nieuw&debtor_type=b2b",
        headers=auth_headers,
    )
    slugs = [t["to_slug"] for t in resp.json()]
    assert "sommatie" in slugs


# ── Tasks ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_task(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    workflow_data: dict,
):
    """Creating a task should return 201 with correct fields."""
    case = await _create_case(db, test_tenant.id)

    payload = {
        "case_id": str(case.id),
        "task_type": "manual_review",
        "title": "Controleer betalingsbewijs",
        "description": "Debiteur claimt betaald te hebben",
        "due_date": "2026-03-15",
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
    workflow_data: dict,
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
    workflow_data: dict,
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
    workflow_data: dict,
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
    workflow_data: dict,
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


# ── Rules ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_rule(client: AsyncClient, auth_headers: dict, workflow_data: dict):
    """Creating a rule should return 201."""
    payload = {
        "name": "Auto-herinnering",
        "trigger_status_id": str(workflow_data["herinnering"]),
        "action_type": "send_letter",
        "days_delay": 7,
    }
    resp = await client.post("/api/workflow/rules", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Auto-herinnering"
    assert resp.json()["days_delay"] == 7


@pytest.mark.asyncio
async def test_list_rules(client: AsyncClient, auth_headers: dict, workflow_data: dict):
    """Listing rules after creating one should return it."""
    await client.post(
        "/api/workflow/rules",
        json={
            "name": "Test rule",
            "trigger_status_id": str(workflow_data["sommatie"]),
            "action_type": "check_payment",
        },
        headers=auth_headers,
    )

    resp = await client.get("/api/workflow/rules", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_delete_rule(client: AsyncClient, auth_headers: dict, workflow_data: dict):
    """Deleting a rule should soft-delete it (204)."""
    create_resp = await client.post(
        "/api/workflow/rules",
        json={
            "name": "To delete",
            "trigger_status_id": str(workflow_data["nieuw"]),
            "action_type": "manual_review",
        },
        headers=auth_headers,
    )
    rule_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/workflow/rules/{rule_id}", headers=auth_headers)
    assert resp.status_code == 204


# ── Calendar ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_calendar_events(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    workflow_data: dict,
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
    workflow_data: dict,
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
        status="sommatie",
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
