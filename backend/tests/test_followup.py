"""Tests for Follow-up Recommendation Advisor (A2.2).

Covers: scanning, deduplication, approve, reject, execute, stats,
and API endpoints.
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
    approve_and_execute_recommendation,
    approve_recommendation,
    get_recommendation,
    get_recommendation_stats,
    list_recommendations,
    reject_recommendation,
    scan_for_followups,
)
from app.auth.models import Tenant, User
from app.cases.models import Case
from app.incasso.models import IncassoPipelineStep
from app.relations.models import Contact


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_step(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    name: str = "Sommatie",
    sort_order: int = 2,
    min_wait_days: int = 14,
    max_wait_days: int = 28,
    template_type: str | None = "sommatie",
) -> IncassoPipelineStep:
    """Create a pipeline step for testing."""
    step = IncassoPipelineStep(
        tenant_id=tenant_id,
        name=name,
        sort_order=sort_order,
        min_wait_days=min_wait_days,
        max_wait_days=max_wait_days,
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
    step: IncassoPipelineStep | None = None,
    *,
    days_in_step: int = 0,
    status: str = "nieuw",
    total_principal: float = 5000.00,
    total_paid: float = 0.00,
) -> Case:
    """Create a test incasso case with required client contact."""
    # Create a client contact (required FK)
    client = Contact(
        tenant_id=tenant_id,
        name=f"Test Client {uuid.uuid4().hex[:4]}",
        contact_type="company",
    )
    db.add(client)
    await db.flush()

    now = datetime.now(UTC)
    step_entered = now - timedelta(days=days_in_step)
    case = Case(
        tenant_id=tenant_id,
        case_number=f"2026-{uuid.uuid4().hex[:5]}",
        case_type="incasso",
        status=status,
        date_opened=date.today() - timedelta(days=days_in_step + 5),
        incasso_step_id=step.id if step else None,
        step_entered_at=step_entered if step else None,
        total_principal=total_principal,
        total_paid=total_paid,
        assigned_to_id=user_id,
        client_id=client.id,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


# ---------------------------------------------------------------------------
# Tests: Scanning
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scan_creates_recommendation_for_orange_case(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Case in step >= min_wait_days → recommendation created."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    await _create_case(
        db, test_tenant.id, test_user.id, step, days_in_step=16
    )
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    await db.commit()

    assert count == 1
    result = await db.execute(
        select(FollowupRecommendation).where(
            FollowupRecommendation.tenant_id == test_tenant.id
        )
    )
    rec = result.scalar_one()
    assert rec.recommended_action == RecommendedAction.GENERATE_DOCUMENT
    assert rec.urgency == "normal"
    assert rec.status == RecommendationStatus.PENDING
    assert rec.days_in_step == 16


@pytest.mark.asyncio
async def test_scan_skips_green_case(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Case in step < min_wait_days → no recommendation."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    await _create_case(
        db, test_tenant.id, test_user.id, step, days_in_step=5
    )
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 0


@pytest.mark.asyncio
async def test_scan_marks_overdue_as_red(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Case in step >= max_wait_days → urgency 'overdue'."""
    step = await _create_step(
        db, test_tenant.id, min_wait_days=14, max_wait_days=28
    )
    await _create_case(
        db, test_tenant.id, test_user.id, step, days_in_step=30
    )
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    await db.commit()

    assert count == 1
    result = await db.execute(
        select(FollowupRecommendation).where(
            FollowupRecommendation.tenant_id == test_tenant.id
        )
    )
    rec = result.scalar_one()
    assert rec.urgency == "overdue"


@pytest.mark.asyncio
async def test_scan_skips_existing_pending(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Already has pending recommendation → no duplicate."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    case = await _create_case(
        db, test_tenant.id, test_user.id, step, days_in_step=16
    )

    # Create existing pending recommendation
    rec = FollowupRecommendation(
        tenant_id=test_tenant.id,
        case_id=case.id,
        incasso_step_id=step.id,
        recommended_action=RecommendedAction.GENERATE_DOCUMENT,
        reasoning="test",
        days_in_step=14,
        outstanding_amount=Decimal("5000.00"),
        urgency="normal",
        status=RecommendationStatus.PENDING,
    )
    db.add(rec)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 0


@pytest.mark.asyncio
async def test_scan_skips_executed_same_step(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Already executed for this step → no duplicate."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    case = await _create_case(
        db, test_tenant.id, test_user.id, step, days_in_step=16
    )

    # Create existing executed recommendation for same step
    rec = FollowupRecommendation(
        tenant_id=test_tenant.id,
        case_id=case.id,
        incasso_step_id=step.id,
        recommended_action=RecommendedAction.GENERATE_DOCUMENT,
        reasoning="test",
        days_in_step=14,
        outstanding_amount=Decimal("5000.00"),
        urgency="normal",
        status=RecommendationStatus.EXECUTED,
        executed_at=datetime.now(UTC),
    )
    db.add(rec)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 0


@pytest.mark.asyncio
async def test_scan_creates_after_rejected(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Rejected recommendation doesn't block new recommendation."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    case = await _create_case(
        db, test_tenant.id, test_user.id, step, days_in_step=16
    )

    # Create rejected recommendation — should NOT block
    rec = FollowupRecommendation(
        tenant_id=test_tenant.id,
        case_id=case.id,
        incasso_step_id=step.id,
        recommended_action=RecommendedAction.GENERATE_DOCUMENT,
        reasoning="test",
        days_in_step=14,
        outstanding_amount=Decimal("5000.00"),
        urgency="normal",
        status=RecommendationStatus.REJECTED,
    )
    db.add(rec)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 1


@pytest.mark.asyncio
async def test_scan_escalate_for_step_without_template(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Step without template_type → ESCALATE action."""
    step = await _create_step(
        db, test_tenant.id, min_wait_days=14, template_type=None
    )
    await _create_case(
        db, test_tenant.id, test_user.id, step, days_in_step=16
    )
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    await db.commit()

    assert count == 1
    result = await db.execute(
        select(FollowupRecommendation).where(
            FollowupRecommendation.tenant_id == test_tenant.id
        )
    )
    rec = result.scalar_one()
    assert rec.recommended_action == RecommendedAction.ESCALATE


@pytest.mark.asyncio
async def test_scan_skips_betaald_case(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Case with status 'betaald' is not scanned."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    await _create_case(
        db, test_tenant.id, test_user.id, step,
        days_in_step=16, status="betaald"
    )
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 0


@pytest.mark.asyncio
async def test_scan_skips_case_without_step(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Case without pipeline step is not scanned."""
    await _create_case(
        db, test_tenant.id, test_user.id, None, days_in_step=30
    )
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 0


# ---------------------------------------------------------------------------
# Tests: Approve / Reject
# ---------------------------------------------------------------------------


async def _create_pending_rec(
    db: AsyncSession, tenant_id: uuid.UUID, case_id: uuid.UUID,
    step_id: uuid.UUID,
) -> FollowupRecommendation:
    """Create a pending recommendation for testing."""
    rec = FollowupRecommendation(
        tenant_id=tenant_id,
        case_id=case_id,
        incasso_step_id=step_id,
        recommended_action=RecommendedAction.GENERATE_DOCUMENT,
        reasoning="Test recommendation",
        days_in_step=16,
        outstanding_amount=Decimal("5000.00"),
        urgency="normal",
        status=RecommendationStatus.PENDING,
    )
    db.add(rec)
    await db.flush()
    await db.refresh(rec)
    return rec


@pytest.mark.asyncio
async def test_approve_recommendation(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Approve changes status to APPROVED."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    rec = await _create_pending_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    result = await approve_recommendation(
        db, test_tenant.id, rec.id, test_user.id
    )
    await db.commit()

    assert result is not None
    assert result.status == RecommendationStatus.APPROVED
    assert result.reviewed_by_id == test_user.id
    assert result.reviewed_at is not None


@pytest.mark.asyncio
async def test_reject_recommendation(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Reject changes status to REJECTED with note."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    rec = await _create_pending_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    result = await reject_recommendation(
        db, test_tenant.id, rec.id, test_user.id, "Niet nodig"
    )
    await db.commit()

    assert result is not None
    assert result.status == RecommendationStatus.REJECTED
    assert result.review_note == "Niet nodig"


@pytest.mark.asyncio
async def test_approve_nonexistent_returns_none(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Approve of nonexistent recommendation returns None."""
    result = await approve_recommendation(
        db, test_tenant.id, uuid.uuid4(), test_user.id
    )
    assert result is None


# ---------------------------------------------------------------------------
# Tests: List / Stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_with_status_filter(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """List recommendations with status filter."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)

    # Create one pending and one rejected
    rec1 = FollowupRecommendation(
        tenant_id=test_tenant.id,
        case_id=case.id,
        incasso_step_id=step.id,
        recommended_action=RecommendedAction.GENERATE_DOCUMENT,
        reasoning="test",
        days_in_step=14,
        outstanding_amount=Decimal("5000.00"),
        urgency="normal",
        status=RecommendationStatus.PENDING,
    )
    rec2 = FollowupRecommendation(
        tenant_id=test_tenant.id,
        case_id=case.id,
        incasso_step_id=step.id,
        recommended_action=RecommendedAction.GENERATE_DOCUMENT,
        reasoning="test 2",
        days_in_step=20,
        outstanding_amount=Decimal("5000.00"),
        urgency="overdue",
        status=RecommendationStatus.REJECTED,
    )
    db.add_all([rec1, rec2])
    await db.commit()

    # Filter pending only
    result = await list_recommendations(
        db, test_tenant.id, status_filter="pending"
    )
    assert result.total == 1
    assert result.items[0].status == "pending"

    # All
    result_all = await list_recommendations(db, test_tenant.id)
    assert result_all.total == 2


@pytest.mark.asyncio
async def test_stats_counts(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Stats endpoint returns correct counts per status."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)

    for status_val in ["pending", "pending", "executed", "rejected"]:
        rec = FollowupRecommendation(
            tenant_id=test_tenant.id,
            case_id=case.id,
            incasso_step_id=step.id,
            recommended_action=RecommendedAction.GENERATE_DOCUMENT,
            reasoning="test",
            days_in_step=14,
            outstanding_amount=Decimal("5000.00"),
            urgency="normal",
            status=status_val,
        )
        db.add(rec)
    await db.commit()

    stats = await get_recommendation_stats(db, test_tenant.id)
    assert stats.pending == 2
    assert stats.executed == 1
    assert stats.rejected == 1
    assert stats.approved == 0


# ---------------------------------------------------------------------------
# Tests: Financial precision
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_financial_precision(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Outstanding amount uses Decimal, not float."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    await _create_case(
        db, test_tenant.id, test_user.id, step,
        days_in_step=16, total_principal=1234.56, total_paid=100.00
    )
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    await db.commit()

    assert count == 1
    result = await db.execute(
        select(FollowupRecommendation).where(
            FollowupRecommendation.tenant_id == test_tenant.id
        )
    )
    rec = result.scalar_one()
    assert rec.outstanding_amount == Decimal("1134.56")


# ---------------------------------------------------------------------------
# Tests: Get single recommendation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_recommendation(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Get a single recommendation with enriched data."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    rec = await _create_pending_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    result = await get_recommendation(db, test_tenant.id, rec.id)
    assert result is not None
    assert result.case_number == case.case_number
    assert result.step_name == "Sommatie"
    assert result.action_label == "Document genereren & versturen"
    assert result.urgency_label == "Klaar voor actie"


# ---------------------------------------------------------------------------
# Tests: API endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_list_followups(
    client, db: AsyncSession, test_tenant, test_user
):
    """GET /api/followup returns paginated recommendations."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await _create_pending_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    from app.auth.service import create_access_token

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.get(
        "/api/followup",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["status"] == "pending"


@pytest.mark.asyncio
async def test_api_stats(
    client, db: AsyncSession, test_tenant, test_user
):
    """GET /api/followup/stats returns counts."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await _create_pending_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    from app.auth.service import create_access_token

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.get(
        "/api/followup/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pending"] >= 1


@pytest.mark.asyncio
async def test_api_approve_and_reject(
    client, db: AsyncSession, test_tenant, test_user
):
    """POST approve and reject endpoints work."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    rec = await _create_pending_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    from app.auth.service import create_access_token

    token = create_access_token(str(test_user.id), str(test_tenant.id))

    # Approve
    resp = await client.post(
        f"/api/followup/{rec.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    # Reject a second one
    rec2 = await _create_pending_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    resp2 = await client.post(
        f"/api/followup/{rec2.id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"note": "Niet nodig"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "rejected"
    assert resp2.json()["review_note"] == "Niet nodig"
