"""Tests for AI Agent email classification — Fase 4.

All tests mock _call_classification_ai() to avoid real API calls.
Covers: classification flow, idempotency, approve/reject/execute,
multi-tenant isolation, pending count, templates, and API endpoints.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.models import ClassificationStatus
from app.ai_agent.service import (
    approve_classification,
    classify_email,
    classify_new_emails,
    execute_classification,
    get_classification_by_email,
    get_classification_by_id,
    get_classifications,
    get_pending_count,
    get_templates,
    reject_classification,
    seed_default_templates,
)
from app.auth.models import Tenant, User
from app.cases.models import Case
from app.email.oauth_models import EmailAccount
from app.email.synced_email_models import SyncedEmail
from app.workflow.models import WorkflowTask

# Fake AI response that _call_classification_ai returns
FAKE_AI_RESPONSE = {
    "category": "belofte_tot_betaling",
    "confidence": 0.92,
    "reasoning": "Debiteur belooft volgende week te betalen.",
    "suggested_action": "wait_and_remind",
    "suggested_template_key": "bevestiging_betaalbelofte",
    "suggested_reminder_days": 7,
}

FAKE_AI_RESPONSE_BETWISTING = {
    "category": "betwisting",
    "confidence": 0.88,
    "reasoning": "Debiteur betwist de vordering inhoudelijk.",
    "suggested_action": "escalate",
    "suggested_template_key": "ontvangst_betwisting",
    "suggested_reminder_days": None,
}

FAKE_AI_RESPONSE_DISMISS = {
    "category": "niet_gerelateerd",
    "confidence": 0.95,
    "reasoning": "Email is spam / niet gerelateerd aan de zaak.",
    "suggested_action": "dismiss",
    "suggested_template_key": None,
    "suggested_reminder_days": None,
}

FAKE_AI_RESPONSE_SEND_TEMPLATE = {
    "category": "beweert_betaald",
    "confidence": 0.90,
    "reasoning": "Debiteur beweert al betaald te hebben.",
    "suggested_action": "send_template",
    "suggested_template_key": "verzoek_betalingsbewijs",
    "suggested_reminder_days": None,
}


# ── Helpers ──────────────────────────────────────────────────────────────


async def _create_email_account(
    db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> EmailAccount:
    account = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        provider="gmail",
        email_address="test@example.com",
        access_token_enc=b"fake",
        refresh_token_enc=b"fake",
    )
    db.add(account)
    await db.flush()
    return account


async def _create_incasso_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    client_id: uuid.UUID,
    opposing_id: uuid.UUID | None = None,
    case_number: str = "2026-00099",
) -> Case:
    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number=case_number,
        case_type="incasso",
        status="sommatie",
        client_id=client_id,
        opposing_party_id=opposing_id,
        total_principal=Decimal("1500.00"),
        total_paid=Decimal("0.00"),
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()
    return case


async def _create_inbound_email(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    account_id: uuid.UUID,
    case_id: uuid.UUID,
    body_text: str = "Ik zal volgende week betalen.",
    subject: str = "Re: Openstaande factuur",
) -> SyncedEmail:
    email = SyncedEmail(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email_account_id=account_id,
        case_id=case_id,
        provider_message_id=f"msg-{uuid.uuid4().hex[:8]}",
        subject=subject,
        from_email="debiteur@example.com",
        from_name="Jan Debiteur",
        to_emails="[]",
        cc_emails="[]",
        body_text=body_text,
        body_html="",
        direction="inbound",
        is_dismissed=False,
        email_date=datetime.now(UTC),
    )
    db.add(email)
    await db.flush()
    return email


# ── Service layer tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_classify_email_creates_record(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """classify_email() should create an EmailClassification record."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    await db.commit()

    assert c is not None
    assert c.category == "belofte_tot_betaling"
    assert c.confidence == pytest.approx(0.92)
    assert c.suggested_action == "wait_and_remind"
    assert c.suggested_reminder_days == 7
    assert c.status == ClassificationStatus.PENDING
    mock_ai.assert_called_once()


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_classify_email_idempotent(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """Classifying the same email twice should only create one record."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    c1 = await classify_email(db, email.id, test_tenant.id)
    await db.commit()
    c2 = await classify_email(db, email.id, test_tenant.id)

    assert c1 is not None
    assert c2 is None  # Idempotent — second call returns None
    assert mock_ai.call_count == 1


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_classify_email_skips_empty_body(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """Emails with empty body should be skipped."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id, body_text="")
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    assert c is None
    mock_ai.assert_not_called()


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_classify_new_emails_batch(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """classify_new_emails() should process multiple emails in a batch."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    # Create 3 inbound emails
    for i in range(3):
        await _create_inbound_email(
            db,
            test_tenant.id,
            account.id,
            case.id,
            body_text=f"Bericht {i}",
            subject=f"Email {i}",
        )
    await db.commit()

    count = await classify_new_emails(db, test_tenant.id)
    assert count == 3
    assert mock_ai.call_count == 3


# ── Approve / Reject / Execute ──────────────────────────────────────────


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_approve_classification(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """Approving a pending classification sets status to APPROVED."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    await db.commit()

    approved = await approve_classification(db, c.id, test_tenant.id, test_user.id, note="Akkoord")
    await db.commit()

    assert approved is not None
    assert approved.status == ClassificationStatus.APPROVED
    assert approved.reviewed_by_id == test_user.id
    assert approved.review_note == "Akkoord"
    assert approved.reviewed_at is not None


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_reject_classification(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """Rejecting a pending classification sets status to REJECTED."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    await db.commit()

    rejected = await reject_classification(db, c.id, test_tenant.id, test_user.id, note="Verkeerd")
    await db.commit()

    assert rejected is not None
    assert rejected.status == ClassificationStatus.REJECTED
    assert rejected.review_note == "Verkeerd"


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_execute_classification(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """Executing an approved classification sets status to EXECUTED."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    await db.commit()

    await approve_classification(db, c.id, test_tenant.id, test_user.id)
    await db.commit()

    executed = await execute_classification(db, c.id, test_tenant.id, test_user.id)
    await db.commit()

    assert executed is not None
    assert executed.status == ClassificationStatus.EXECUTED
    assert executed.executed_at is not None
    assert executed.execution_result is not None
    assert "herinnering" in executed.execution_result.lower()


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_execute_wait_and_remind_creates_task(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """wait_and_remind creates a WorkflowTask with correct due_date."""
    mock_ai.return_value = FAKE_AI_RESPONSE  # action=wait_and_remind, days=7

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    await db.commit()
    await approve_classification(db, c.id, test_tenant.id, test_user.id)
    await db.commit()
    await execute_classification(db, c.id, test_tenant.id, test_user.id)
    await db.commit()

    # Verify WorkflowTask was created
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.tenant_id == test_tenant.id,
            WorkflowTask.case_id == case.id,
            WorkflowTask.task_type == "check_payment",
        )
    )
    task = result.scalar_one_or_none()
    assert task is not None
    assert task.due_date == date.today() + timedelta(days=7)
    assert task.status == "pending"
    assert task.assigned_to_id == test_user.id
    assert task.action_config["source"] == "ai_classification"


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_execute_dismiss_sets_is_dismissed(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """dismiss sets SyncedEmail.is_dismissed = True."""
    mock_ai.return_value = FAKE_AI_RESPONSE_DISMISS

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(
        db,
        test_tenant.id,
        account.id,
        case.id,
        body_text="Win a free iPhone!",
    )
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    await db.commit()
    await approve_classification(db, c.id, test_tenant.id, test_user.id)
    await db.commit()

    executed = await execute_classification(db, c.id, test_tenant.id, test_user.id)
    await db.commit()

    assert executed is not None
    assert "weggezet" in executed.execution_result.lower()

    # Verify SyncedEmail.is_dismissed was set
    await db.refresh(email)
    assert email.is_dismissed is True


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_execute_escalate_creates_urgent_task(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """escalate creates an urgent WorkflowTask with due_date=today."""
    mock_ai.return_value = FAKE_AI_RESPONSE_BETWISTING

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(
        db,
        test_tenant.id,
        account.id,
        case.id,
        body_text="Ik betwist deze vordering volledig.",
    )
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    await db.commit()
    await approve_classification(db, c.id, test_tenant.id, test_user.id)
    await db.commit()
    await execute_classification(db, c.id, test_tenant.id, test_user.id)
    await db.commit()

    # Verify urgent WorkflowTask was created
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.tenant_id == test_tenant.id,
            WorkflowTask.case_id == case.id,
            WorkflowTask.task_type == "manual_review",
        )
    )
    task = result.scalar_one_or_none()
    assert task is not None
    assert task.due_date == date.today()
    assert task.status == "pending"
    assert task.action_config["urgent"] is True
    assert task.action_config["source"] == "ai_classification"
    assert "URGENT" in task.title


@pytest.mark.asyncio
@patch("app.ai_agent.service.send_with_attachment", new_callable=AsyncMock)
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_execute_send_template_sends_email(
    mock_ai,
    mock_send,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    test_company,
):
    """send_template renders template and sends email."""
    mock_ai.return_value = FAKE_AI_RESPONSE_SEND_TEMPLATE

    # Mock send_with_attachment to return a successful EmailLog-like object
    mock_email_log = AsyncMock()
    mock_email_log.status = "sent"
    mock_send.return_value = mock_email_log

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(
        db,
        test_tenant.id,
        account.id,
        case.id,
        body_text="Ik heb al betaald vorige week.",
    )
    await db.commit()

    # Seed templates first
    await seed_default_templates(db, test_tenant.id)
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    await db.commit()
    await approve_classification(db, c.id, test_tenant.id, test_user.id)
    await db.commit()

    executed = await execute_classification(db, c.id, test_tenant.id, test_user.id)
    await db.commit()

    assert executed is not None
    assert "verzonden" in executed.execution_result.lower()

    # Verify send_with_attachment was called correctly
    mock_send.assert_called_once()
    call_kwargs = mock_send.call_args
    assert call_kwargs.kwargs["to"] == "debiteur@example.com"
    assert "betalingsbewijs" in call_kwargs.kwargs["subject"].lower()
    assert case.case_number in call_kwargs.kwargs["subject"]


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_execute_not_approved_returns_none(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """Executing a PENDING classification should return None (must be approved first)."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    await db.commit()

    result = await execute_classification(db, c.id, test_tenant.id, test_user.id)
    assert result is None  # Can't execute without approval


# ── Multi-tenant isolation ───────────────────────────────────────────────


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_multi_tenant_isolation(
    mock_ai,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    test_company,
    second_tenant: Tenant,
    second_user: User,
):
    """Classifications from tenant A should not be visible to tenant B."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    # Create data for tenant A
    account_a = await _create_email_account(db, test_tenant.id, test_user.id)
    case_a = await _create_incasso_case(
        db,
        test_tenant.id,
        test_company.id,
        test_company.id,
        case_number="2026-00001",
    )
    email_a = await _create_inbound_email(db, test_tenant.id, account_a.id, case_a.id)

    # Create client contact for tenant B
    from app.relations.models import Contact

    client_b = Contact(
        id=uuid.uuid4(),
        tenant_id=second_tenant.id,
        contact_type="company",
        name="Other B.V.",
        email="other@example.com",
    )
    db.add(client_b)
    await db.flush()

    # Create data for tenant B
    account_b = await _create_email_account(db, second_tenant.id, second_user.id)
    case_b = await _create_incasso_case(
        db,
        second_tenant.id,
        client_b.id,
        client_b.id,
        case_number="2026-00002",
    )
    email_b = await _create_inbound_email(db, second_tenant.id, account_b.id, case_b.id)
    await db.commit()

    # Classify both
    c_a = await classify_email(db, email_a.id, test_tenant.id)
    c_b = await classify_email(db, email_b.id, second_tenant.id)
    await db.commit()

    assert c_a is not None
    assert c_b is not None

    # Tenant A can see their own, not tenant B's
    results_a, total_a = await get_classifications(db, test_tenant.id)
    results_b, total_b = await get_classifications(db, second_tenant.id)

    assert total_a == 1
    assert total_b == 1
    assert results_a[0].id == c_a.id
    assert results_b[0].id == c_b.id

    # Tenant A cannot access tenant B's classification
    cross = await get_classification_by_id(db, c_b.id, test_tenant.id)
    assert cross is None


# ── Query helpers ────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_pending_count(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """get_pending_count() should return the number of pending classifications."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)

    # Create 2 emails
    e1 = await _create_inbound_email(
        db,
        test_tenant.id,
        account.id,
        case.id,
        body_text="Bericht 1",
        subject="Email 1",
    )
    e2 = await _create_inbound_email(
        db,
        test_tenant.id,
        account.id,
        case.id,
        body_text="Bericht 2",
        subject="Email 2",
    )
    await db.commit()

    await classify_email(db, e1.id, test_tenant.id)
    await classify_email(db, e2.id, test_tenant.id)
    await db.commit()

    count = await get_pending_count(db, test_tenant.id)
    assert count == 2


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_get_classification_by_email(
    mock_ai, db: AsyncSession, test_tenant: Tenant, test_user: User, test_company
):
    """get_classification_by_email() should find classification by synced_email_id."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    await classify_email(db, email.id, test_tenant.id)
    await db.commit()

    found = await get_classification_by_email(db, email.id, test_tenant.id)
    assert found is not None
    assert found.synced_email_id == email.id


# ── Templates ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_seed_default_templates(db: AsyncSession, test_tenant: Tenant):
    """seed_default_templates() should create the default templates."""
    created = await seed_default_templates(db, test_tenant.id)
    await db.commit()

    assert created == 6  # 6 default templates

    templates = await get_templates(db, test_tenant.id)
    assert len(templates) == 6

    keys = {t.key for t in templates}
    assert "bevestiging_betaalbelofte" in keys
    assert "verzoek_betalingsbewijs" in keys


@pytest.mark.asyncio
async def test_seed_templates_idempotent(db: AsyncSession, test_tenant: Tenant):
    """Seeding templates twice should not create duplicates."""
    first = await seed_default_templates(db, test_tenant.id)
    await db.commit()
    second = await seed_default_templates(db, test_tenant.id)
    await db.commit()

    assert first == 6
    assert second == 0  # All already exist


# ── API endpoint tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_api_pending_count(
    mock_ai, client, db, test_tenant, test_user, test_company, auth_headers
):
    """GET /api/ai-agent/pending-count should return the count."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    await classify_email(db, email.id, test_tenant.id)
    await db.commit()

    resp = await client.get("/api/ai-agent/pending-count", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_api_list_classifications(
    mock_ai, client, db, test_tenant, test_user, test_company, auth_headers
):
    """GET /api/ai-agent/classifications should return classifications."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    await classify_email(db, email.id, test_tenant.id)
    await db.commit()

    resp = await client.get("/api/ai-agent/classifications", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["category"] == "belofte_tot_betaling"
    assert data[0]["category_label"] == "Belofte tot betaling"
    assert data[0]["suggested_action"] == "wait_and_remind"


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_api_approve_and_execute(
    mock_ai, client, db, test_tenant, test_user, test_company, auth_headers
):
    """POST approve → POST execute flow via API."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    await db.commit()

    # Approve
    resp = await client.post(
        f"/api/ai-agent/classifications/{c.id}/approve",
        headers=auth_headers,
        json={"note": "Ziet er goed uit"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    # Execute
    resp = await client.post(
        f"/api/ai-agent/classifications/{c.id}/execute",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "executed"
    assert resp.json()["execution_result"] is not None


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_api_reject(mock_ai, client, db, test_tenant, test_user, test_company, auth_headers):
    """POST reject via API should set status to rejected."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    c = await classify_email(db, email.id, test_tenant.id)
    await db.commit()

    resp = await client.post(
        f"/api/ai-agent/classifications/{c.id}/reject",
        headers=auth_headers,
        json={"note": "Onjuist geclassificeerd"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_api_templates(client, db, test_tenant, test_user, auth_headers):
    """GET /api/ai-agent/templates should list seeded templates."""
    await seed_default_templates(db, test_tenant.id)
    await db.commit()

    resp = await client.get("/api/ai-agent/templates", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 6
    assert all("key" in t for t in data)


@pytest.mark.asyncio
async def test_api_seed_templates(client, db, test_tenant, test_user, auth_headers):
    """POST /api/ai-agent/templates/seed should seed templates."""
    resp = await client.post("/api/ai-agent/templates/seed", headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["created"] == 6


@pytest.mark.asyncio
@patch("app.ai_agent.service._call_classification_ai", new_callable=AsyncMock)
async def test_api_get_email_classification(
    mock_ai, client, db, test_tenant, test_user, test_company, auth_headers
):
    """GET /api/ai-agent/email/{id}/classification returns the classification."""
    mock_ai.return_value = FAKE_AI_RESPONSE

    account = await _create_email_account(db, test_tenant.id, test_user.id)
    case = await _create_incasso_case(db, test_tenant.id, test_company.id, test_company.id)
    email = await _create_inbound_email(db, test_tenant.id, account.id, case.id)
    await db.commit()

    await classify_email(db, email.id, test_tenant.id)
    await db.commit()

    resp = await client.get(
        f"/api/ai-agent/email/{email.id}/classification",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["synced_email_id"] == str(email.id)


@pytest.mark.asyncio
async def test_api_get_email_classification_none(client, db, test_tenant, test_user, auth_headers):
    """GET /api/ai-agent/email/{id}/classification returns null for unclassified."""
    random_id = uuid.uuid4()
    resp = await client.get(
        f"/api/ai-agent/email/{random_id}/classification",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_api_classification_not_found(client, db, test_tenant, test_user, auth_headers):
    """GET /api/ai-agent/classifications/{id} returns 404 for non-existent."""
    random_id = uuid.uuid4()
    resp = await client.get(
        f"/api/ai-agent/classifications/{random_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 404
