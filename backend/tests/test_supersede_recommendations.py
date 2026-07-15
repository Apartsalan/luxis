"""S220 punt 13 — stale follow-up-adviezen sluiten bij stap-wissel."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.followup_models import FollowupRecommendation, RecommendationStatus
from app.auth.models import Tenant, User
from app.cases.models import Case
from app.incasso.models import IncassoPipelineStep
from app.incasso.service import move_case_to_step
from app.relations.models import Contact


async def _step(db, tenant_id, name, order):
    s = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name=name, sort_order=order,
        min_wait_days=0, max_wait_days=4, debtor_type="both", step_category="minnelijk",
    )
    db.add(s)
    await db.flush()
    return s


@pytest.mark.asyncio
async def test_step_change_supersedes_pending_recommendation(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    client = Contact(id=uuid.uuid4(), tenant_id=test_tenant.id, contact_type="person", name="C")
    db.add(client)
    await db.flush()
    step_a = await _step(db, test_tenant.id, "Eerste sommatie", 1)
    step_b = await _step(db, test_tenant.id, "Tweede sommatie", 2)
    case = Case(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_number="2026-96700",
        case_type="incasso", status="in_behandeling", debtor_type="b2b",
        client_id=client.id, date_opened=date.today(), incasso_step_id=step_a.id,
    )
    db.add(case)
    await db.flush()

    rec = FollowupRecommendation(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        incasso_step_id=step_a.id, recommended_action="generate_document",
        reasoning="stap te lang open", days_in_step=10,
        outstanding_amount=Decimal("100.00"), urgency="normal",
        status=RecommendationStatus.PENDING,
    )
    db.add(rec)
    await db.flush()

    await move_case_to_step(db, test_tenant.id, case, step_b, user_id=test_user.id)
    await db.refresh(rec)

    assert rec.status == RecommendationStatus.SUPERSEDED
    assert rec.reviewed_at is not None
    assert "verouderd" in (rec.review_note or "")


@pytest.mark.asyncio
async def test_step_change_leaves_executed_recommendation(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Een al uitgevoerd advies blijft EXECUTED (historie) — alleen PENDING sluit."""
    client = Contact(id=uuid.uuid4(), tenant_id=test_tenant.id, contact_type="person", name="C")
    db.add(client)
    await db.flush()
    step_a = await _step(db, test_tenant.id, "Eerste sommatie", 1)
    step_b = await _step(db, test_tenant.id, "Tweede sommatie", 2)
    case = Case(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_number="2026-96701",
        case_type="incasso", status="in_behandeling", debtor_type="b2b",
        client_id=client.id, date_opened=date.today(), incasso_step_id=step_a.id,
    )
    db.add(case)
    await db.flush()
    rec = FollowupRecommendation(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        incasso_step_id=step_a.id, recommended_action="generate_document",
        reasoning="x", days_in_step=10, outstanding_amount=Decimal("100.00"),
        urgency="normal", status=RecommendationStatus.EXECUTED,
    )
    db.add(rec)
    await db.flush()

    await move_case_to_step(db, test_tenant.id, case, step_b, user_id=test_user.id)
    await db.refresh(rec)

    assert rec.status == RecommendationStatus.EXECUTED
