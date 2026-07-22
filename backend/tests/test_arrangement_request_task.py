"""Wachters (S235, Gat B): regeling-mail → direct een taak 'Betalingsregeling vastleggen'.

De classificatie-wachtrij (goedkeuren + uitvoeren) wordt in de praktijk niet
afgewerkt, dus de taak ontstaat op het moment van herkennen (orchestrator-handler
op het classified-event). Kruispunt: als de wachtrij later alsnog wordt afgewerkt,
maakt de escalate-tak GEEN tweede taak zolang de gerichte taak open staat.
"""

import json
import uuid
from datetime import UTC, datetime, date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.ai_agent.models import ClassificationStatus, EmailClassification
from app.ai_agent.orchestrator import handle_email_classified_arrangement
from app.ai_agent.service import execute_classification
from app.collections.schemas import ArrangementCreate
from app.collections.service import create_arrangement
from app.email.oauth_models import EmailAccount
from app.email.synced_email_models import SyncedEmail
from app.workflow.models import WorkflowTask
from tests.helpers.incasso_fixtures import create_incasso_case


async def _fire_handler(db, tenant_id, case_id, category) -> None:
    await handle_email_classified_arrangement(
        db=db, tenant_id=tenant_id, classification_id=uuid.uuid4(),
        case_id=case_id, category=category, confidence=0.9,
        synced_email_id=uuid.uuid4(),
    )


async def _tasks(db, tenant_id, case_id, source) -> list[WorkflowTask]:
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.case_id == case_id,
            WorkflowTask.action_config["source"].astext == source,
        )
    )
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_regeling_verzoek_creates_task_once(
    db, test_tenant, test_user, test_company
):
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09701"
    )

    await _fire_handler(db, test_tenant.id, case.id, "betalingsregeling_verzoek")
    tasks = await _tasks(db, test_tenant.id, case.id, "arrangement_request")
    assert len(tasks) == 1
    assert "Betalingsregeling vastleggen" in tasks[0].title

    # Tweede herkende regeling-mail → geen tweede taak zolang de eerste open staat
    await _fire_handler(db, test_tenant.id, case.id, "betalingsregeling_verzoek")
    assert len(await _tasks(db, test_tenant.id, case.id, "arrangement_request")) == 1


@pytest.mark.asyncio
async def test_other_category_creates_no_task(
    db, test_tenant, test_user, test_company
):
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09702"
    )
    await _fire_handler(db, test_tenant.id, case.id, "betwisting")
    assert await _tasks(db, test_tenant.id, case.id, "arrangement_request") == []


@pytest.mark.asyncio
async def test_no_task_when_arrangement_already_active(
    db, test_tenant, test_user, test_company
):
    """Er loopt al een regeling → de mail is opvolging, geen nieuw vastleg-werk."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09703"
    )
    await create_arrangement(
        db, test_tenant.id, case.id,
        ArrangementCreate(
            total_amount=Decimal("900.00"), num_installments=3,
            frequency="monthly", start_date=date.today() + timedelta(days=7),
        ),
    )
    await _fire_handler(db, test_tenant.id, case.id, "betalingsregeling_verzoek")
    assert await _tasks(db, test_tenant.id, case.id, "arrangement_request") == []


@pytest.mark.asyncio
async def test_no_task_on_closed_case(db, test_tenant, test_user, test_company):
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user,
        case_number="2026-09704", status="afgesloten",
    )
    await _fire_handler(db, test_tenant.id, case.id, "betalingsregeling_verzoek")
    assert await _tasks(db, test_tenant.id, case.id, "arrangement_request") == []


@pytest.mark.asyncio
async def test_escalate_route_skips_duplicate_task(
    db, test_tenant, test_user, test_company
):
    """Kruispunt: wachtrij later alsnog afgewerkt → geen tweede taak op die mail."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user, case_number="2026-09705"
    )

    account = EmailAccount(
        id=uuid.uuid4(), tenant_id=test_tenant.id, user_id=test_user.id,
        provider="outlook", email_address="kantoor@test.nl",
        access_token_enc=b"x", refresh_token_enc=b"y",
    )
    db.add(account)
    await db.flush()
    email = SyncedEmail(
        id=uuid.uuid4(), tenant_id=test_tenant.id, email_account_id=account.id,
        case_id=case.id, provider_message_id="m1",
        subject="Regeling?", from_email="debiteur@test.nl", from_name="Debiteur",
        to_emails=json.dumps(["kantoor@test.nl"]), cc_emails=json.dumps([]),
        snippet="Ik wil een regeling", body_text="Ik wil een betalingsregeling.",
        body_html="", direction="inbound", email_date=datetime.now(UTC),
    )
    db.add(email)
    classification = EmailClassification(
        id=uuid.uuid4(), tenant_id=test_tenant.id, synced_email_id=email.id,
        case_id=case.id, category="betalingsregeling_verzoek", confidence=0.9,
        reasoning="", suggested_action="escalate",
        status=ClassificationStatus.APPROVED,
    )
    db.add(classification)
    await db.flush()

    # De gerichte taak bestaat al (gemaakt op het moment van classificeren)
    await _fire_handler(db, test_tenant.id, case.id, "betalingsregeling_verzoek")
    assert len(await _tasks(db, test_tenant.id, case.id, "arrangement_request")) == 1

    # Wachtrij wordt alsnog afgewerkt → escalatie-taak wordt overgeslagen
    result = await execute_classification(
        db, classification.id, test_tenant.id, test_user.id
    )
    assert result is not None
    assert "staat al open" in (result.execution_result or "")
    assert await _tasks(db, test_tenant.id, case.id, "ai_classification") == []

    # De gerichte taak is er nog steeds precies één keer
    assert len(await _tasks(db, test_tenant.id, case.id, "arrangement_request")) == 1
