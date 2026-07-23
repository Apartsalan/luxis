"""Wachters (S240): betaalbelofte herkend → taak op de beloofde datum.

S239 vondst 9: de classificatie haalt promise_date + promise_amount al perfect
uit de mail (live bewezen), maar níets bewaakte die datum — een verlopen
belofte gaf geen enkel signaal. Nu: taak 'Betaalbelofte controleren' met
due = promise_date bij de classificatie (orchestrator-handler, S235-recept),
automatisch dicht zodra de zaak volledig betaald raakt (on_payment_received).
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.ai_agent.models import EmailClassification
from app.ai_agent.orchestrator import handle_email_classified_promise
from app.collections.models import Claim
from app.workflow.models import WorkflowTask
from tests.helpers.incasso_fixtures import create_incasso_case


async def _add_claim(db, tenant_id, case_id, amount="100.00") -> None:
    from app.collections.models import InterestRate

    # Minimale rentetarief-seed zodat de betaal-berekening werkt (globale tabel).
    db.add(
        InterestRate(
            id=uuid.uuid4(), rate_type="statutory", rate=Decimal("4.00"),
            effective_from=date(2024, 1, 1),
        )
    )
    db.add(
        Claim(
            id=uuid.uuid4(), tenant_id=tenant_id, case_id=case_id,
            description="Factuur", principal_amount=Decimal(amount),
            invoice_date=date.today(), default_date=date.today(),
        )
    )
    await db.flush()


async def _make_classification(
    db, tenant_id, case_id, user_id, *, category="belofte_tot_betaling",
    promise_date=None, promise_amount=None,
) -> EmailClassification:
    """Classificatie-rij zoals classify_email die achterlaat (zonder AI-call)."""
    import json
    from datetime import UTC, datetime

    from app.email.oauth_models import EmailAccount
    from app.email.synced_email_models import SyncedEmail

    account = EmailAccount(
        id=uuid.uuid4(), tenant_id=tenant_id, user_id=user_id,
        provider="outlook", email_address=f"acc-{uuid.uuid4().hex[:8]}@test.nl",
        access_token_enc=b"x", refresh_token_enc=b"y",
    )
    db.add(account)
    await db.flush()
    email = SyncedEmail(
        id=uuid.uuid4(), tenant_id=tenant_id, email_account_id=account.id,
        case_id=case_id, provider_message_id=f"m-{uuid.uuid4().hex[:8]}",
        subject="Ik betaal", from_email="debiteur@test.nl", from_name="Debiteur",
        to_emails=json.dumps(["kantoor@test.nl"]), cc_emails=json.dumps([]),
        snippet="", body_text="Ik betaal eind van de maand.", body_html="",
        direction="inbound", email_date=datetime.now(UTC),
    )
    db.add(email)
    await db.flush()
    classification = EmailClassification(
        id=uuid.uuid4(), tenant_id=tenant_id, synced_email_id=email.id,
        case_id=case_id, category=category, confidence=0.95,
        reasoning="", suggested_action="wait_and_remind",
        promise_date=promise_date, promise_amount=promise_amount,
    )
    db.add(classification)
    await db.flush()
    return classification


async def _fire(db, tenant_id, case_id, classification) -> None:
    await handle_email_classified_promise(
        db=db, tenant_id=tenant_id, classification_id=classification.id,
        case_id=case_id, category=classification.category,
        confidence=0.95, synced_email_id=classification.synced_email_id,
    )


async def _tasks(db, tenant_id, case_id) -> list[WorkflowTask]:
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.case_id == case_id,
            WorkflowTask.action_config["source"].astext == "payment_promise",
        )
    )
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_promise_creates_task_with_due_date(
    db, test_tenant, test_user, test_company
):
    """Belofte-classificatie → taak met due = promise_date + bedrag in tekst."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09801"
    )
    promised = date.today() + timedelta(days=8)
    c = await _make_classification(
        db, test_tenant.id, case.id, test_user.id,
        promise_date=promised, promise_amount=Decimal("250.00"),
    )
    await _fire(db, test_tenant.id, case.id, c)

    tasks = await _tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1
    assert tasks[0].title == f"Betaalbelofte controleren — {case.case_number}"
    assert tasks[0].due_date == promised
    assert tasks[0].status == "pending"  # toekomstige datum → pending, job zet due
    assert "250.00" in (tasks[0].description or "")


@pytest.mark.asyncio
async def test_promise_today_or_past_is_due(db, test_tenant, test_user, test_company):
    """Beloofde datum vandaag/verstreken → taak staat direct op 'due'."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09802"
    )
    c = await _make_classification(
        db, test_tenant.id, case.id, test_user.id, promise_date=date.today()
    )
    await _fire(db, test_tenant.id, case.id, c)

    tasks = await _tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1
    assert tasks[0].status == "due"


@pytest.mark.asyncio
async def test_second_promise_mail_no_duplicate_task(
    db, test_tenant, test_user, test_company
):
    """Tweede belofte-mail terwijl de taak open staat → geen tweede taak."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09803"
    )
    c1 = await _make_classification(
        db, test_tenant.id, case.id, test_user.id, promise_date=date.today() + timedelta(days=5)
    )
    await _fire(db, test_tenant.id, case.id, c1)
    c2 = await _make_classification(
        db, test_tenant.id, case.id, test_user.id, promise_date=date.today() + timedelta(days=12)
    )
    await _fire(db, test_tenant.id, case.id, c2)

    assert len(await _tasks(db, test_tenant.id, case.id)) == 1


@pytest.mark.asyncio
async def test_no_task_on_closed_case(db, test_tenant, test_user, test_company):
    """Gesloten/betaalde zaak → geen taak."""
    for status, nr in (("afgesloten", "2026-09804"), ("betaald", "2026-09805")):
        case = await create_incasso_case(
            db, test_tenant.id, test_company, None, test_user,
            case_number=nr, status=status,
        )
        c = await _make_classification(
            db, test_tenant.id, case.id, test_user.id, promise_date=date.today()
        )
        await _fire(db, test_tenant.id, case.id, c)
        assert await _tasks(db, test_tenant.id, case.id) == []


@pytest.mark.asyncio
async def test_no_task_without_promise_date(db, test_tenant, test_user, test_company):
    """Belofte zonder herkende datum → niets op datum te bewaken → geen taak
    (bewuste keuze S240; de mail geeft al een email_received-melding)."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09806"
    )
    c = await _make_classification(db, test_tenant.id, case.id, test_user.id, promise_date=None)
    await _fire(db, test_tenant.id, case.id, c)
    assert await _tasks(db, test_tenant.id, case.id) == []


@pytest.mark.asyncio
async def test_other_category_creates_no_task(db, test_tenant, test_user, test_company):
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09807"
    )
    c = await _make_classification(
        db, test_tenant.id, case.id, test_user.id, category="betwisting", promise_date=date.today()
    )
    await _fire(db, test_tenant.id, case.id, c)
    assert await _tasks(db, test_tenant.id, case.id) == []


@pytest.mark.asyncio
async def test_full_payment_closes_promise_task(
    db, test_tenant, test_user, test_company
):
    """Zaak volledig betaald → betaalbelofte-taak automatisch completed
    (via on_payment_received, het gedeelde punt van alle betaalroutes)."""
    from app.collections.schemas import PaymentCreate
    from app.collections.service import create_payment, get_case_outstanding

    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09808"
    )
    await _add_claim(db, test_tenant.id, case.id)
    c = await _make_classification(
        db, test_tenant.id, case.id, test_user.id, promise_date=date.today() + timedelta(days=3)
    )
    await _fire(db, test_tenant.id, case.id, c)
    assert len(await _tasks(db, test_tenant.id, case.id)) == 1

    outstanding = await get_case_outstanding(db, test_tenant.id, case)
    assert outstanding > Decimal("0")
    await create_payment(
        db, test_tenant.id, case.id,
        PaymentCreate(
            amount=outstanding, payment_date=date.today(),
            description="Volledige betaling", payment_method="bank",
        ),
        user_id=test_user.id,
    )

    await db.refresh(case)
    assert case.status == "betaald"
    tasks = await _tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1
    assert tasks[0].status == "completed"
    assert tasks[0].completed_at is not None


@pytest.mark.asyncio
async def test_partial_payment_keeps_promise_task_open(
    db, test_tenant, test_user, test_company
):
    """Deelbetaling (zaak niet vol) → taak blijft open (er valt nog te bewaken)."""
    from app.collections.schemas import PaymentCreate
    from app.collections.service import create_payment

    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09809"
    )
    await _add_claim(db, test_tenant.id, case.id)
    c = await _make_classification(
        db, test_tenant.id, case.id, test_user.id, promise_date=date.today() + timedelta(days=3)
    )
    await _fire(db, test_tenant.id, case.id, c)

    await create_payment(
        db, test_tenant.id, case.id,
        PaymentCreate(
            amount=Decimal("10.00"), payment_date=date.today(),
            description="Deelbetaling", payment_method="bank",
        ),
        user_id=test_user.id,
    )

    tasks = await _tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1
    assert tasks[0].status in ("pending", "due")


@pytest.mark.asyncio
async def test_manual_close_skips_promise_task(
    db, test_tenant, test_user, test_company
):
    """S240 Fable-review: zaak handmatig afgesloten (cliënt trekt in, debiteur
    betaalde rechtstreeks) → open betaalbelofte-taak wordt 'skipped' — er valt
    niets meer te bewaken. Zonder dit blijft de taak eeuwig open op een gesloten
    dossier (het S239-spooktaken-patroon)."""
    from app.cases.schemas import CaseStatusUpdate
    from app.cases.service import update_case_status

    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09810"
    )
    c = await _make_classification(
        db, test_tenant.id, case.id, test_user.id,
        promise_date=date.today() + timedelta(days=5),
    )
    await _fire(db, test_tenant.id, case.id, c)
    assert len(await _tasks(db, test_tenant.id, case.id)) == 1

    await update_case_status(
        db, test_tenant.id, case.id, test_user.id,
        CaseStatusUpdate(new_status="afgesloten", note="S240-test"),
    )

    tasks = await _tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1
    assert tasks[0].status == "skipped"


@pytest.mark.asyncio
async def test_promise_with_active_arrangement_makes_no_task(
    db, test_tenant, test_user, test_company
):
    """S242 (S241 voorstel 2): belofte-mail op een zaak met lopende regeling →
    géén belofte-taak. De termijn-bewaking bewaakt die betaling al (te-laat-
    termijnen → wanprestatie-route → taak 'Regeling verbroken'); een tweede
    bewakingstaak op dezelfde betaling is dubbel werk (S241 live bewezen:
    zelfde datum, twee taken). Zelfde poort als de regeling-verzoek-taak."""
    from app.collections.schemas import ArrangementCreate
    from app.collections.service import create_arrangement

    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09811"
    )
    await create_arrangement(
        db, test_tenant.id, case.id,
        ArrangementCreate(
            total_amount=Decimal("900.00"), num_installments=3,
            frequency="monthly", start_date=date.today() + timedelta(days=7),
        ),
    )
    c = await _make_classification(
        db, test_tenant.id, case.id, test_user.id,
        promise_date=date.today() + timedelta(days=7),
        promise_amount=Decimal("300.00"),
    )
    await _fire(db, test_tenant.id, case.id, c)

    assert await _tasks(db, test_tenant.id, case.id) == []


@pytest.mark.asyncio
async def test_promise_after_ended_arrangement_still_makes_task(
    db, test_tenant, test_user, test_company
):
    """Tegenproef: een geannuleerde/verbroken regeling bewaakt niets meer —
    dan moet een nieuwe belofte wél gewoon een taak geven."""
    from app.collections.schemas import ArrangementCreate
    from app.collections.service import cancel_arrangement, create_arrangement

    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09812"
    )
    arrangement = await create_arrangement(
        db, test_tenant.id, case.id,
        ArrangementCreate(
            total_amount=Decimal("900.00"), num_installments=3,
            frequency="monthly", start_date=date.today() + timedelta(days=7),
        ),
    )
    await cancel_arrangement(db, test_tenant.id, arrangement.id)

    c = await _make_classification(
        db, test_tenant.id, case.id, test_user.id,
        promise_date=date.today() + timedelta(days=7),
    )
    await _fire(db, test_tenant.id, case.id, c)

    assert len(await _tasks(db, test_tenant.id, case.id)) == 1


@pytest.mark.asyncio
async def test_new_arrangement_skips_open_promise_task(
    db, test_tenant, test_user, test_company
):
    """S242 — omgekeerde volgorde van hetzelfde dubbel-werk: de belofte-taak
    staat al open en dáárna wordt de regeling vastgelegd (de gewone gang:
    debiteur belooft → vraagt regeling → Lisanne legt vast). De regeling
    neemt de bewaking over → open belofte-taak wordt 'skipped'
    (S236-conventie: achterhaald, niet volbracht)."""
    from app.collections.schemas import ArrangementCreate
    from app.collections.service import create_arrangement

    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09813"
    )
    c = await _make_classification(
        db, test_tenant.id, case.id, test_user.id,
        promise_date=date.today() + timedelta(days=5),
    )
    await _fire(db, test_tenant.id, case.id, c)
    assert len(await _tasks(db, test_tenant.id, case.id)) == 1

    await create_arrangement(
        db, test_tenant.id, case.id,
        ArrangementCreate(
            total_amount=Decimal("900.00"), num_installments=3,
            frequency="monthly", start_date=date.today() + timedelta(days=7),
        ),
    )

    tasks = await _tasks(db, test_tenant.id, case.id)
    assert len(tasks) == 1
    assert tasks[0].status == "skipped"
