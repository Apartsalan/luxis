"""Tests for Follow-up Recommendation Advisor (A2.2).

Covers: scanning, deduplication, approve, reject, execute, stats,
and API endpoints.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.followup_models import (
    FollowupRecommendation,
    RecommendationStatus,
    RecommendedAction,
)
from app.ai_agent.followup_service import (
    approve_recommendation,
    execute_recommendation,
    get_recommendation,
    get_recommendation_stats,
    list_recommendations,
    preview_recommendation,
    reject_recommendation,
    scan_for_followups,
)
from app.auth.models import Tenant, User
from app.cases.models import Case
from app.incasso.models import IncassoPipelineStep
from app.relations.models import Contact
from app.shared.exceptions import BadRequestError

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
    await _create_case(db, test_tenant.id, test_user.id, step, days_in_step=16)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    await db.commit()

    assert count == 1
    result = await db.execute(
        select(FollowupRecommendation).where(FollowupRecommendation.tenant_id == test_tenant.id)
    )
    rec = result.scalar_one()
    assert rec.recommended_action == RecommendedAction.GENERATE_DOCUMENT
    assert rec.urgency == "normal"
    assert rec.status == RecommendationStatus.PENDING
    assert rec.days_in_step == 16


@pytest.mark.asyncio
async def test_scan_skips_green_case(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Case in step < min_wait_days → no recommendation."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    await _create_case(db, test_tenant.id, test_user.id, step, days_in_step=5)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 0


@pytest.mark.asyncio
async def test_scan_marks_overdue_as_red(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Case in step >= max_wait_days → urgency 'overdue'."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14, max_wait_days=28)
    await _create_case(db, test_tenant.id, test_user.id, step, days_in_step=30)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    await db.commit()

    assert count == 1
    result = await db.execute(
        select(FollowupRecommendation).where(FollowupRecommendation.tenant_id == test_tenant.id)
    )
    rec = result.scalar_one()
    assert rec.urgency == "overdue"


@pytest.mark.asyncio
async def test_scan_skips_existing_pending(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Already has pending recommendation → no duplicate."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    case = await _create_case(db, test_tenant.id, test_user.id, step, days_in_step=16)

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
    case = await _create_case(db, test_tenant.id, test_user.id, step, days_in_step=16)

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
async def test_scan_creates_after_rejected(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Rejected recommendation doesn't block new recommendation."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    case = await _create_case(db, test_tenant.id, test_user.id, step, days_in_step=16)

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
    step = await _create_step(db, test_tenant.id, min_wait_days=14, template_type=None)
    await _create_case(db, test_tenant.id, test_user.id, step, days_in_step=16)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    await db.commit()

    assert count == 1
    result = await db.execute(
        select(FollowupRecommendation).where(FollowupRecommendation.tenant_id == test_tenant.id)
    )
    rec = result.scalar_one()
    assert rec.recommended_action == RecommendedAction.ESCALATE


@pytest.mark.asyncio
async def test_scan_skips_betaald_case(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Case with status 'betaald' is not scanned."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    await _create_case(db, test_tenant.id, test_user.id, step, days_in_step=16, status="betaald")
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 0


@pytest.mark.asyncio
async def test_scan_skips_case_without_step(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Case without pipeline step is not scanned."""
    await _create_case(db, test_tenant.id, test_user.id, None, days_in_step=30)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 0


@pytest.mark.asyncio
async def test_scan_skips_hold_step(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Case on a hold-step (e.g. Verweer beantwoorden / Bijhouden regeling) gets
    no calendar-driven recommendation, even long past min_wait_days (S182)."""
    step = await _create_step(
        db, test_tenant.id, name="Verweer beantwoorden", min_wait_days=0, max_wait_days=0
    )
    step.is_hold_step = True
    await db.flush()
    await _create_case(db, test_tenant.id, test_user.id, step, days_in_step=30)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 0


@pytest.mark.asyncio
async def test_scan_skips_terminal_step(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Case on a terminal step is never recommended (S182)."""
    step = await _create_step(
        db, test_tenant.id, name="Afgesloten", min_wait_days=0, max_wait_days=0
    )
    step.is_terminal = True
    await db.flush()
    await _create_case(db, test_tenant.id, test_user.id, step, days_in_step=30)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 0


@pytest.mark.asyncio
async def test_scan_still_recommends_normal_step(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """A normal (non-hold, non-terminal) step still gets a recommendation —
    the guard must not over-skip (S182)."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    await _create_case(db, test_tenant.id, test_user.id, step, days_in_step=16)
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    assert count == 1


# ---------------------------------------------------------------------------
# Tests: Approve / Reject
# ---------------------------------------------------------------------------


async def _create_pending_rec(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
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
async def test_approve_recommendation(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Approve changes status to APPROVED."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    rec = await _create_pending_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    result = await approve_recommendation(db, test_tenant.id, rec.id, test_user.id)
    await db.commit()

    assert result is not None
    assert result.status == RecommendationStatus.APPROVED
    assert result.reviewed_by_id == test_user.id
    assert result.reviewed_at is not None


@pytest.mark.asyncio
async def test_reject_recommendation(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Reject changes status to REJECTED with note."""
    step = await _create_step(db, test_tenant.id)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    rec = await _create_pending_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    result = await reject_recommendation(db, test_tenant.id, rec.id, test_user.id, "Niet nodig")
    await db.commit()

    assert result is not None
    assert result.status == RecommendationStatus.REJECTED
    assert result.review_note == "Niet nodig"


@pytest.mark.asyncio
async def test_approve_nonexistent_returns_none(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Approve of nonexistent recommendation returns None."""
    result = await approve_recommendation(db, test_tenant.id, uuid.uuid4(), test_user.id)
    assert result is None


# ---------------------------------------------------------------------------
# Tests: List / Stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_with_status_filter(db: AsyncSession, test_tenant: Tenant, test_user: User):
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
    result = await list_recommendations(db, test_tenant.id, status_filter="pending")
    assert result.total == 1
    assert result.items[0].status == "pending"

    # All
    result_all = await list_recommendations(db, test_tenant.id)
    assert result_all.total == 2


@pytest.mark.asyncio
async def test_stats_counts(db: AsyncSession, test_tenant: Tenant, test_user: User):
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
async def test_financial_precision(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Outstanding amount uses Decimal, not float."""
    step = await _create_step(db, test_tenant.id, min_wait_days=14)
    await _create_case(
        db,
        test_tenant.id,
        test_user.id,
        step,
        days_in_step=16,
        total_principal=1234.56,
        total_paid=100.00,
    )
    await db.commit()

    count = await scan_for_followups(db, test_tenant.id)
    await db.commit()

    assert count == 1
    result = await db.execute(
        select(FollowupRecommendation).where(FollowupRecommendation.tenant_id == test_tenant.id)
    )
    rec = result.scalar_one()
    assert rec.outstanding_amount == Decimal("1134.56")


# ---------------------------------------------------------------------------
# Tests: Get single recommendation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_recommendation(db: AsyncSession, test_tenant: Tenant, test_user: User):
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
async def test_api_list_followups(client, db: AsyncSession, test_tenant, test_user):
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
async def test_api_stats(client, db: AsyncSession, test_tenant, test_user):
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


# ---------------------------------------------------------------------------
# Tests: Execute (B1 — verstuurpad + geen maskering)
# ---------------------------------------------------------------------------


async def _add_opposing_with_email(
    db: AsyncSession, tenant_id: uuid.UUID, case: Case, email: str = "debiteur@example.com"
) -> Contact:
    """Attach an opposing party with an e-mail address to a case."""
    opp = Contact(
        tenant_id=tenant_id,
        name="Debiteur BV",
        contact_type="company",
        email=email,
    )
    db.add(opp)
    await db.flush()
    # Zet de relatie zelf (niet alleen de FK) — anders blijft de al-geladen lege
    # opposing_party in de sessie-cache hangen bij de her-select in execute.
    case.opposing_party = opp
    await db.flush()
    return opp


async def _create_approved_rec(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    step_id: uuid.UUID,
) -> FollowupRecommendation:
    rec = FollowupRecommendation(
        tenant_id=tenant_id,
        case_id=case_id,
        incasso_step_id=step_id,
        recommended_action=RecommendedAction.GENERATE_DOCUMENT,
        reasoning="Test",
        days_in_step=16,
        outstanding_amount=Decimal("5000.00"),
        urgency="normal",
        status=RecommendationStatus.APPROVED,
    )
    db.add(rec)
    await db.flush()
    await db.refresh(rec)
    return rec


@pytest.mark.asyncio
@patch("app.ai_agent.followup_service.build_base_context", new_callable=AsyncMock)
@patch("app.ai_agent.followup_service.render_incasso_email")
@patch("app.ai_agent.followup_service.send_with_attachment", new_callable=AsyncMock)
async def test_execute_email_template_sends_via_email_route(
    mock_send, mock_render, mock_ctx, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Een e-mailsjabloonstap (sommatie_drukte) verstuurt via de e-mailroute:
    de brief ís de e-mailtekst (geen PDF-bijlage) en de aanbeveling wordt pas
    daarna als 'Uitgevoerd' gemarkeerd."""
    mock_ctx.return_value = {}
    mock_render.return_value = "<p>Sommatie (drukte)</p>"
    mock_send.return_value = SimpleNamespace(status="sent", error_message=None)

    step = await _create_step(db, test_tenant.id, name="Eerste sommatie",
                              template_type="sommatie_drukte")
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await _add_opposing_with_email(db, test_tenant.id, case)
    rec = await _create_approved_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    result = await execute_recommendation(db, test_tenant.id, rec.id, test_user.id)
    await db.commit()

    assert result is not None
    assert result.status == RecommendationStatus.EXECUTED
    assert result.generated_document_id is not None
    # E-mailroute → geen bijlage, brief ís de body
    mock_send.assert_called_once()
    assert mock_send.call_args.kwargs["attachments"] == []
    assert mock_send.call_args.kwargs["body_html"] == "<p>Sommatie (drukte)</p>"


@pytest.mark.asyncio
@patch("app.ai_agent.followup_service.build_base_context", new_callable=AsyncMock)
@patch("app.ai_agent.followup_service.render_incasso_email")
@patch("app.ai_agent.followup_service.send_with_attachment", new_callable=AsyncMock)
async def test_execute_marks_send_on_step_history(
    mock_send, mock_render, mock_ctx, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """S207 (review S205): een via 'Uitvoeren' verstuurde brief moet — net als op
    het batch- en conceptpad — als verzonden op de open staphistorie-rij landen
    (email_sent + verzendmoment + document). Zonder dit telt een écht via Luxis
    verstuurde 14-dagenbrief niet als verstuurd en blijft de gate blokkeren."""
    from app.incasso.models import CaseStepHistory

    mock_ctx.return_value = {}
    mock_render.return_value = "<p>Brief</p>"
    mock_send.return_value = SimpleNamespace(status="sent", error_message=None)

    step = await _create_step(db, test_tenant.id, name="Eerste sommatie",
                              template_type="sommatie_drukte")
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await _add_opposing_with_email(db, test_tenant.id, case)
    # Open staphistorie-rij van de huidige stap (zoals move_case_to_step die maakt).
    hist = CaseStepHistory(
        tenant_id=test_tenant.id, case_id=case.id, step_id=step.id,
        entered_at=datetime.now(UTC), trigger_type="manual",
    )
    db.add(hist)
    rec = await _create_approved_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    result = await execute_recommendation(db, test_tenant.id, rec.id, test_user.id)
    await db.commit()

    assert result is not None
    await db.refresh(hist)
    assert hist.email_sent is True
    assert hist.email_sent_at is not None
    assert hist.document_id == result.generated_document_id


@pytest.mark.asyncio
@patch("app.ai_agent.followup_service.build_base_context", new_callable=AsyncMock)
@patch("app.ai_agent.followup_service.render_incasso_email")
@patch("app.ai_agent.followup_service.send_with_attachment", new_callable=AsyncMock)
async def test_execute_failed_send_is_never_marked_executed(
    mock_send, mock_render, mock_ctx, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Kernfix B1: als de verzending mislukt, mag de aanbeveling NOOIT als
    'Uitgevoerd' worden geregistreerd (de oude code maskeerde de fout en zette
    'm tóch op Uitgevoerd)."""
    mock_ctx.return_value = {}
    mock_render.return_value = "<p>Sommatie (drukte)</p>"
    mock_send.return_value = SimpleNamespace(status="failed", error_message="SMTP dicht")

    step = await _create_step(db, test_tenant.id, name="Eerste sommatie",
                              template_type="sommatie_drukte")
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await _add_opposing_with_email(db, test_tenant.id, case)
    rec = await _create_approved_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    with pytest.raises(BadRequestError):
        await execute_recommendation(db, test_tenant.id, rec.id, test_user.id)

    # execute muteert hetzelfde aanbeveling-object; het is nooit op EXECUTED gezet.
    assert rec.status != RecommendationStatus.EXECUTED
    assert rec.executed_at is None


@pytest.mark.asyncio
@patch("app.ai_agent.followup_service.build_base_context", new_callable=AsyncMock)
@patch("app.ai_agent.followup_service.render_incasso_email")
async def test_preview_shows_email_without_sending(
    mock_render, mock_ctx, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """B13 — preview rendert wat eruit gaat (onderwerp, ontvanger, tekst) en laat
    de aanbeveling ongemoeid: er wordt niets verstuurd of uitgevoerd."""
    mock_ctx.return_value = {}
    mock_render.return_value = "<p>Sommatie (drukte)</p>"

    step = await _create_step(db, test_tenant.id, name="Eerste sommatie",
                              template_type="sommatie_drukte")
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await _add_opposing_with_email(db, test_tenant.id, case)
    rec = await _create_pending_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    preview = await preview_recommendation(db, test_tenant.id, rec.id, test_user.id)

    assert preview is not None
    assert preview.body_html == "<p>Sommatie (drukte)</p>"
    assert preview.recipient_email == "debiteur@example.com"
    assert preview.has_attachment is False
    assert preview.can_send is True
    # Niets verstuurd/uitgevoerd — aanbeveling blijft PENDING.
    assert rec.status == RecommendationStatus.PENDING


@pytest.mark.asyncio
async def test_execute_without_opposing_email_fails_loud(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Geen e-mailadres wederpartij → fout opwerpen, niet stilletjes 'Uitgevoerd'."""
    step = await _create_step(db, test_tenant.id, name="Eerste sommatie",
                              template_type="sommatie_drukte")
    case = await _create_case(db, test_tenant.id, test_user.id, step)  # geen wederpartij
    rec = await _create_approved_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    with pytest.raises(BadRequestError):
        await execute_recommendation(db, test_tenant.id, rec.id, test_user.id)

    assert rec.status != RecommendationStatus.EXECUTED


@pytest.mark.asyncio
async def test_execute_generate_without_template_never_executed(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Codex-review: een GENERATE_DOCUMENT-aanbeveling waarvan de stap geen
    sjabloon (meer) heeft, mag NOOIT stil op 'Uitgevoerd' belanden."""
    step = await _create_step(db, test_tenant.id, name="Losse stap", template_type=None)
    case = await _create_case(db, test_tenant.id, test_user.id, step)
    await _add_opposing_with_email(db, test_tenant.id, case)
    rec = await _create_approved_rec(db, test_tenant.id, case.id, step.id)
    await db.commit()

    with pytest.raises(BadRequestError):
        await execute_recommendation(db, test_tenant.id, rec.id, test_user.id)

    assert rec.status != RecommendationStatus.EXECUTED
    assert rec.executed_at is None


@pytest.mark.asyncio
@patch("app.ai_agent.followup_service.build_base_context", new_callable=AsyncMock)
@patch("app.ai_agent.followup_service.render_incasso_email")
@patch("app.ai_agent.followup_service.send_with_attachment", new_callable=AsyncMock)
async def test_execute_b2c_blocked_without_dagenbrief(
    mock_send, mock_render, mock_ctx, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """S205 zijdeur 1: 'Uitvoeren' bij een B2C-sommatie zónder verstuurde 14-dagenbrief
    → hard geblokkeerd (art. 6:96 lid 6 BW). Niets verstuurd, aanbeveling niet Uitgevoerd."""
    mock_ctx.return_value = {}
    mock_render.return_value = "<p>Sommatie</p>"
    mock_send.return_value = SimpleNamespace(status="sent", error_message=None)

    sommatie = await _create_step(
        db, test_tenant.id, name="Eerste sommatie", template_type="sommatie_drukte"
    )
    case = await _create_case(db, test_tenant.id, test_user.id, sommatie)
    case.debtor_type = "b2c"
    await _add_opposing_with_email(db, test_tenant.id, case)
    rec = await _create_approved_rec(db, test_tenant.id, case.id, sommatie.id)
    await db.commit()

    with pytest.raises(BadRequestError) as exc:
        await execute_recommendation(db, test_tenant.id, rec.id, test_user.id)
    assert "14-dagenbrief" in str(exc.value.detail)
    mock_send.assert_not_called()  # er ging niets de deur uit
    assert rec.status != RecommendationStatus.EXECUTED
    assert rec.executed_at is None


@pytest.mark.asyncio
@patch("app.ai_agent.followup_service.build_base_context", new_callable=AsyncMock)
@patch("app.ai_agent.followup_service.render_incasso_email")
@patch("app.ai_agent.followup_service.send_with_attachment", new_callable=AsyncMock)
async def test_execute_b2c_allowed_after_dagenbrief_sent(
    mock_send, mock_render, mock_ctx, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Ná een aantoonbaar verstuurde 14-dagenbrief (>15 dagen) mag 'Uitvoeren' de
    B2C-sommatie wél versturen."""
    mock_ctx.return_value = {}
    mock_render.return_value = "<p>Sommatie</p>"
    mock_send.return_value = SimpleNamespace(status="sent", error_message=None)

    dagenbrief = await _create_step(
        db, test_tenant.id, name="14-dagenbrief", sort_order=0, template_type=None
    )
    sommatie = await _create_step(
        db, test_tenant.id, name="Eerste sommatie", template_type="sommatie_drukte"
    )
    case = await _create_case(db, test_tenant.id, test_user.id, sommatie)
    case.debtor_type = "b2c"
    await _add_opposing_with_email(db, test_tenant.id, case)
    # Aantoonbaar verstuurde 14-dagenbrief, 20 dagen geleden.
    from app.incasso.models import CaseStepHistory

    db.add(CaseStepHistory(
        tenant_id=test_tenant.id, case_id=case.id, step_id=dagenbrief.id,
        entered_at=datetime.now(UTC) - timedelta(days=20), email_sent=True,
        trigger_type="manual",
    ))
    rec = await _create_approved_rec(db, test_tenant.id, case.id, sommatie.id)
    await db.commit()

    result = await execute_recommendation(db, test_tenant.id, rec.id, test_user.id)
    await db.commit()

    assert result is not None
    assert result.status == RecommendationStatus.EXECUTED
    mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_api_approve_and_reject(client, db: AsyncSession, test_tenant, test_user):
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
