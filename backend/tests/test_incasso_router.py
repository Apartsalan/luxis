"""Tests for the incasso pipeline router — steps CRUD, pipeline overview, queues, seed."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User

# ── Helpers ──────────────────────────────────────────────────────────────────


def _step_payload(**overrides) -> dict:
    payload = {
        "name": "Herinnering",
        "sort_order": 10,
        "min_wait_days": 14,
        "max_wait_days": 21,
    }
    payload.update(overrides)
    return payload


# ── Pipeline Steps CRUD ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_pipeline_step(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/incasso/pipeline-steps",
        json=_step_payload(),
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Herinnering"
    assert data["min_wait_days"] == 14
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_pipeline_steps(client: AsyncClient, auth_headers: dict):
    await client.post("/api/incasso/pipeline-steps", json=_step_payload(), headers=auth_headers)
    await client.post(
        "/api/incasso/pipeline-steps",
        json=_step_payload(name="Aanmaning", sort_order=20),
        headers=auth_headers,
    )

    resp = await client.get("/api/incasso/pipeline-steps", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_update_pipeline_step(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/incasso/pipeline-steps", json=_step_payload(), headers=auth_headers
    )
    step_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/incasso/pipeline-steps/{step_id}",
        json={"name": "Eerste herinnering", "min_wait_days": 7},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Eerste herinnering"
    assert resp.json()["min_wait_days"] == 7


@pytest.mark.asyncio
async def test_delete_pipeline_step(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/incasso/pipeline-steps", json=_step_payload(), headers=auth_headers
    )
    step_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/incasso/pipeline-steps/{step_id}", headers=auth_headers)
    assert del_resp.status_code == 204


# ── Seed Default Steps ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_seed_default_steps(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/incasso/pipeline-steps/seed", headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) >= 1
    names = [s["name"] for s in data]
    assert any("erinnering" in n.lower() or "aanmaning" in n.lower() for n in names)


@pytest.mark.asyncio
async def test_seed_idempotent(client: AsyncClient, auth_headers: dict):
    """Seeding twice should not duplicate steps."""
    resp1 = await client.post("/api/incasso/pipeline-steps/seed", headers=auth_headers)
    resp2 = await client.post("/api/incasso/pipeline-steps/seed", headers=auth_headers)
    assert resp2.status_code == 201
    assert len(resp2.json()) == len(resp1.json())


# ── Pipeline Overview ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_overview(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/incasso/pipeline", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "columns" in data
    assert "total_cases" in data


# ── Queue Counts ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_queue_counts(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/incasso/queues/counts", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "ready_next_step" in data
    assert "action_required" in data


# ── Tenant isolation ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_steps_tenant_isolation(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
):
    """Steps from tenant A are not visible to tenant B."""
    await client.post(
        "/api/incasso/pipeline-steps",
        json=_step_payload(name="Tenant A stap"),
        headers=auth_headers,
    )

    resp = await client.get("/api/incasso/pipeline-steps", headers=second_auth_headers)
    assert resp.status_code == 200
    names = [s["name"] for s in resp.json()]
    assert "Tenant A stap" not in names


# ── Auth ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.get("/api/incasso/pipeline-steps")
    assert resp.status_code in (401, 403)
