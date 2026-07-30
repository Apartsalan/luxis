"""Wachter (S254, waarheid "gesloten dossier verstuurt nooit meer automatisch iets").

Eén gedrag ("er gaat een brief naar de debiteur") is via meerdere automatische
routes bereikbaar. De wachtrij van 'Verstuur later' controleerde sinds S246-nacht
of het dossier intussen betaald/afgesloten is; de batch-knop en de follow-up-knop
'Uitvoeren' deden dat NIET — precies dezelfde zijdeur-fout die de 14-dagenbrief-gate
twee keer maakte (S204: twee open zijdeuren, S224: de .eml-knop).

Een sommatie naar iemand die al betaald heeft is de duurste soort fout die dit
systeem kan maken: reputatieschade met Lisannes naam eronder, en onomkeerbaar.

Deze wachter test het GEDRAG per route. De soort-wachter die een TOEKOMSTIGE route
betrapt staat in `test_send_route_drift_guard.py` (AST, leest de broncode uit).
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.followup_models import (
    FollowupRecommendation,
    RecommendationStatus,
    RecommendedAction,
)
from app.auth.models import Tenant
from app.cases.models import Case
from app.cases.schemas import TERMINAL_STATUSES
from app.collections.compliance import check_case_closed_gate
from app.incasso.models import IncassoPipelineStep
from app.relations.models import Contact

# ── De gedeelde poort zelf ───────────────────────────────────────────────────


@pytest.mark.parametrize("status", TERMINAL_STATUSES)
def test_gate_blocks_every_terminal_status(status):
    case = Case(status=status, case_number="IN100001")
    reason = check_case_closed_gate(case, case_number="IN100001")
    assert reason is not None
    assert status in reason


@pytest.mark.parametrize("status", ["nieuw", "in_behandeling", "verweer"])
def test_gate_allows_open_case(status):
    assert check_case_closed_gate(Case(status=status), case_number="IN100001") is None


# ── Route-opzet ──────────────────────────────────────────────────────────────


async def _incasso_case(
    db: AsyncSession, tenant_id: uuid.UUID, *, status: str
) -> tuple[Case, IncassoPipelineStep]:
    """Een incassodossier op een stap mét briefsjabloon — alles staat klaar om te
    versturen; alleen de status moet het tegenhouden."""
    client = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="company", name="Cliënt B.V."
    )
    debtor = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contact_type="company",
        name="Debiteur B.V.",
        email="debiteur@example.com",
    )
    db.add_all([client, debtor])
    await db.flush()

    step = IncassoPipelineStep(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Eerste sommatie",
        sort_order=1,
        min_wait_days=0,
        max_wait_days=4,
        step_category="minnelijk",
        debtor_type="both",
        template_type="sommatie_drukte",
    )
    db.add(step)
    await db.flush()

    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number=f"IN{uuid.uuid4().hex[:6]}",
        case_type="incasso",
        status=status,
        debtor_type="b2b",
        client_id=client.id,
        opposing_party_id=debtor.id,
        incasso_step_id=step.id,
        date_opened=date.today(),
        is_active=True,
    )
    db.add(case)
    await db.flush()
    return case, step


# ── Route 1: de batch-knop ("Verstuur brief" over meerdere dossiers) ─────────


@pytest.mark.parametrize("status", TERMINAL_STATUSES)
async def test_batch_refuses_closed_case(
    db: AsyncSession, test_tenant: Tenant, test_user, status
):
    """De batch mag op een betaald/afgesloten dossier geen brief genereren en
    zeker niets versturen — overslaan mét reden, niet stil."""
    from app.incasso.service import batch_execute

    case, _ = await _incasso_case(db, test_tenant.id, status=status)

    result = await batch_execute(
        db,
        test_tenant.id,
        test_user.id,
        [case.id],
        action="generate_document",
        send_email=True,
    )

    assert result.processed == 0, "gesloten dossier werd tóch verwerkt"
    assert result.skipped == 1
    assert any(status in e for e in result.errors), (
        f"geen begrijpelijke reden teruggegeven: {result.errors}"
    )
    assert getattr(result, "emails_sent", 0) == 0, "er ging een mail de deur uit"


# ── Route 2: de follow-up-knop "Uitvoeren" ───────────────────────────────────


@pytest.mark.parametrize("status", TERMINAL_STATUSES)
async def test_followup_execute_refuses_closed_case(
    db: AsyncSession, test_tenant: Tenant, test_user, status
):
    """Een advies kan uren tot dagen oud zijn (goedkeuren nu, uitvoeren later).
    Is het dossier intussen dicht, dan mag 'Uitvoeren' niets versturen."""
    from app.shared.exceptions import BadRequestError

    case, step = await _incasso_case(db, test_tenant.id, status=status)
    rec = FollowupRecommendation(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_id=case.id,
        incasso_step_id=step.id,
        recommended_action=RecommendedAction.GENERATE_DOCUMENT,
        status=RecommendationStatus.APPROVED,
        reasoning="test",
        days_in_step=5,
        outstanding_amount=Decimal("100.00"),
        urgency="normal",
        created_at=datetime.now(UTC),
    )
    db.add(rec)
    await db.flush()

    from app.ai_agent.followup_service import execute_recommendation

    with pytest.raises(BadRequestError) as exc:
        await execute_recommendation(db, test_tenant.id, rec.id, test_user.id)

    assert status in str(exc.value.detail)
    await db.refresh(rec)
    assert rec.status != RecommendationStatus.EXECUTED, (
        "advies kwam op 'uitgevoerd' terwijl er niets verstuurd is"
    )
