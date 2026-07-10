"""Tests for the incasso pipeline — P1 QA coverage.

Covers: deadline colors, batch preview, batch execute (with mocked DOCX/PDF/email),
auto-complete tasks, auto-advance pipeline, queue counts, pipeline overview,
and email template building.

Total: 36 test cases.
"""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from sqlalchemy import select

from app.cases.models import CaseActivity
from app.collections.models import Claim, InterestRate, Payment
from app.documents.models import GeneratedDocument
from app.email.models import EmailLog
from app.incasso.models import IncassoPipelineStep
from app.incasso.service import (
    _auto_complete_tasks,
    _build_step_email,
    _compute_deadline_status,
    _create_tasks_for_step,
    _try_auto_advance,
)
from app.workflow.models import WorkflowTask
from tests.helpers.incasso_fixtures import (
    create_incasso_case,
    create_manual_task,
    create_pipeline_steps,
    create_pipeline_task,
)

# ── Helpers ──────────────────────────────────────────────────────────────


class _FakeStep:
    """Lightweight step-like object for unit tests (avoids SQLAlchemy instrumentation)."""

    def __init__(
        self,
        min_wait: int = 0,
        max_wait: int = 0,
        template_type: str | None = None,
        name: str = "TestStep",
        email_subject_template: str | None = None,
        email_body_template: str | None = None,
    ):
        self.min_wait_days = min_wait
        self.max_wait_days = max_wait
        self.template_type = template_type
        self.name = name
        self.email_subject_template = email_subject_template
        self.email_body_template = email_body_template


def _make_step(
    min_wait: int = 0,
    max_wait: int = 0,
    template_type: str | None = None,
    email_subject_template: str | None = None,
    email_body_template: str | None = None,
):
    """Create a lightweight step object for unit tests (no DB)."""
    return _FakeStep(
        min_wait=min_wait,
        max_wait=max_wait,
        template_type=template_type,
        email_subject_template=email_subject_template,
        email_body_template=email_body_template,
    )


# Helper to create a fake send_with_attachment that creates a real EmailLog
async def _fake_send_with_attachment(db, user_id, tenant_id, **kwargs):
    """Fake send_with_attachment that creates a real EmailLog record."""
    log = EmailLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_id=kwargs.get("case_id"),
        document_id=kwargs.get("document_id"),
        template="batch_document_send",
        recipient=kwargs["to"],
        subject=kwargs["subject"],
        status="sent",
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: Deadline Status (pure unit tests — no DB, no mocks)
# ═══════════════════════════════════════════════════════════════════════════


class TestDeadlineStatus:
    """Tests for _compute_deadline_status — 6 tests."""

    def test_green_within_min_wait(self):
        """Case is within min_wait_days → green (still waiting)."""
        assert _compute_deadline_status(3, _make_step(7, 14)) == "green"

    def test_orange_past_min_wait(self):
        """Case past min_wait_days but below max → orange (ready for action)."""
        assert _compute_deadline_status(8, _make_step(7, 14)) == "orange"

    def test_red_past_max_wait(self):
        """Case past max_wait_days → red (overdue)."""
        assert _compute_deadline_status(15, _make_step(7, 14)) == "red"

    def test_gray_no_step(self):
        """No step assigned → gray."""
        assert _compute_deadline_status(10, None) == "gray"

    def test_zero_max_uses_double_min(self):
        """When max_wait_days=0, max becomes min*2. days=15 >= 14 → red."""
        assert _compute_deadline_status(15, _make_step(7, 0)) == "red"

    def test_boundary_exactly_min(self):
        """days == min_wait_days → orange (>= comparison)."""
        assert _compute_deadline_status(7, _make_step(7, 14)) == "orange"


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: Email Template Building (unit-ish, needs case with relationships)
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildStepEmail:
    """Tests for _build_step_email — 2 tests."""

    async def test_custom_template_renders_jinja2(
        self, db, test_tenant, test_user, test_company, test_person
    ):
        """When step has email templates, Jinja2 renders case data."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        await db.commit()
        await db.refresh(case)

        subject, body = _build_step_email(steps[0], case, db, test_tenant.id)

        assert case.case_number in subject
        assert "Aanmaning" in subject
        assert test_person.name in body  # wederpartij naam

    async def test_fallback_to_generic_template(
        self, db, test_tenant, test_user, test_company, test_person
    ):
        """When step has no email templates, falls back to document_sent()."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        # Dagvaarding (steps[2]) has no email templates
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[2],
        )
        await db.commit()
        await db.refresh(case)

        subject, body = _build_step_email(steps[2], case, db, test_tenant.id)

        # Fallback subject format: "{step.name} — {case_number}"
        assert steps[2].name in subject
        assert case.case_number in subject
        assert "Bijgaand" in body  # generic template text


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: Task Automation (DB tests, no external mocks)
# ═══════════════════════════════════════════════════════════════════════════


class TestCreateTasksForStep:
    """Tests for _create_tasks_for_step — 2 tests."""

    async def test_step_with_template_creates_generate_document_task(
        self, db, test_tenant, test_user, test_company, test_person
    ):
        """Step with template_type creates a generate_document task."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        await db.commit()

        tasks = await _create_tasks_for_step(db, test_tenant.id, case, steps[0])
        await db.commit()

        assert len(tasks) == 1
        assert tasks[0].task_type == "generate_document"
        assert tasks[0].action_config["source"] == "pipeline"
        assert tasks[0].action_config["step_id"] == str(steps[0].id)
        # min_wait_days=0, so status should be "due"
        assert tasks[0].status == "due"

        # CaseActivity should be created
        result = await db.execute(
            select(CaseActivity).where(
                CaseActivity.case_id == case.id,
                CaseActivity.activity_type == "automation",
            )
        )
        activities = list(result.scalars().all())
        assert len(activities) == 1

    async def test_step_without_template_creates_manual_review_task(
        self, db, test_tenant, test_user, test_company, test_person
    ):
        """Step without template_type creates a manual_review task."""
        step = IncassoPipelineStep(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            name="Handmatige review",
            sort_order=10,
            min_wait_days=7,
            max_wait_days=14,
            template_type=None,
        )
        db.add(step)
        await db.flush()

        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=step,
        )
        await db.commit()

        tasks = await _create_tasks_for_step(db, test_tenant.id, case, step)
        await db.commit()

        assert len(tasks) == 1
        assert tasks[0].task_type == "manual_review"
        # min_wait_days=7, so status should be "pending"
        assert tasks[0].status == "pending"


class TestAutoCompleteTasks:
    """Tests for _auto_complete_tasks — 3 tests. BUG-29 regression coverage."""

    async def test_completes_only_pipeline_tasks_for_step(
        self, db, test_tenant, test_user, test_company, test_person
    ):
        """Only completes pipeline tasks for the given step. Manual tasks untouched."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        # Create pipeline task for step 0 (should be completed)
        pipeline_task = await create_pipeline_task(db, test_tenant.id, case, steps[0])
        # Create manual task (should NOT be completed)
        manual_task = await create_manual_task(db, test_tenant.id, case)
        await db.commit()

        count = await _auto_complete_tasks(db, test_tenant.id, case.id, steps[0].id)
        await db.commit()

        assert count == 1
        await db.refresh(pipeline_task)
        await db.refresh(manual_task)
        assert pipeline_task.status == "completed"
        assert manual_task.status == "pending"  # Untouched!

    async def test_different_step_not_completed(
        self, db, test_tenant, test_user, test_company, test_person
    ):
        """Pipeline tasks for a different step are NOT completed."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        # Task for step 1 (Sommatie), but we auto-complete for step 0 (Aanmaning)
        other_step_task = await create_pipeline_task(db, test_tenant.id, case, steps[1])
        await db.commit()

        count = await _auto_complete_tasks(db, test_tenant.id, case.id, steps[0].id)
        await db.commit()

        assert count == 0
        await db.refresh(other_step_task)
        assert other_step_task.status == "pending"

    async def test_none_matching_returns_zero(
        self, db, test_tenant, test_user, test_company, test_person
    ):
        """No matching tasks → returns 0."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        await db.commit()

        count = await _auto_complete_tasks(db, test_tenant.id, case.id, steps[0].id)

        assert count == 0


class TestTryAutoAdvance:
    """Tests for _try_auto_advance — 4 tests."""

    async def test_advances_when_all_tasks_done(
        self, db, test_tenant, test_user, test_company, test_person
    ):
        """When all pipeline tasks for current step are completed, case advances."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        # Create a completed pipeline task (no open tasks remain)
        await create_pipeline_task(db, test_tenant.id, case, steps[0], status="completed")
        await db.commit()

        advanced = await _try_auto_advance(db, test_tenant.id, case, test_user.id, step_list=steps)
        await db.commit()

        assert advanced is True
        await db.refresh(case)
        assert case.incasso_step_id == steps[1].id  # Moved to Sommatie

        # New task created for Sommatie
        result = await db.execute(
            select(WorkflowTask).where(
                WorkflowTask.case_id == case.id,
                WorkflowTask.action_config["step_id"].astext == str(steps[1].id),
            )
        )
        new_tasks = list(result.scalars().all())
        assert len(new_tasks) == 1

        # CaseActivity for pipeline advance
        result = await db.execute(
            select(CaseActivity).where(
                CaseActivity.case_id == case.id,
                CaseActivity.activity_type == "pipeline_change",
            )
        )
        assert result.scalar_one_or_none() is not None

    async def test_stays_when_open_pipeline_tasks(
        self, db, test_tenant, test_user, test_company, test_person
    ):
        """Open pipeline tasks block auto-advance."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        # Create an open (pending) pipeline task
        await create_pipeline_task(db, test_tenant.id, case, steps[0], status="pending")
        await db.commit()

        advanced = await _try_auto_advance(db, test_tenant.id, case, test_user.id, step_list=steps)

        assert advanced is False
        await db.refresh(case)
        assert case.incasso_step_id == steps[0].id  # Still on Aanmaning

    async def test_last_step_cannot_advance(
        self, db, test_tenant, test_user, test_company, test_person
    ):
        """Case on the last step cannot advance further."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[2],  # Dagvaarding = last step
        )
        await db.commit()

        advanced = await _try_auto_advance(db, test_tenant.id, case, test_user.id, step_list=steps)

        assert advanced is False

    async def test_manual_tasks_dont_block_advance(
        self, db, test_tenant, test_user, test_company, test_person
    ):
        """Open manual tasks (source=manual) do NOT block auto-advance."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        # Only a manual task open — no pipeline tasks
        await create_manual_task(db, test_tenant.id, case, title="Bel debiteur", status="pending")
        await db.commit()

        advanced = await _try_auto_advance(db, test_tenant.id, case, test_user.id, step_list=steps)
        await db.commit()

        assert advanced is True  # Manual tasks don't block!
        await db.refresh(case)
        assert case.incasso_step_id == steps[1].id


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: Batch Preview (API endpoint tests)
# ═══════════════════════════════════════════════════════════════════════════


class TestBatchPreview:
    """Tests for POST /api/incasso/batch/preview — 5 tests."""

    async def test_generate_document_ready(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Case with step + template → ready=1."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        await db.commit()

        resp = await client.post(
            "/api/incasso/batch/preview",
            json={
                "case_ids": [str(case.id)],
                "action": "generate_document",
            },
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] == 1
        assert data["total_selected"] == 1
        assert len(data["blocked"]) == 0

    async def test_generate_document_no_step_needs_assignment(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Case without pipeline step → needs_step_assignment."""
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=None,
        )
        await db.commit()

        resp = await client.post(
            "/api/incasso/batch/preview",
            json={
                "case_ids": [str(case.id)],
                "action": "generate_document",
            },
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] == 0
        assert len(data["needs_step_assignment"]) == 1

    async def test_generate_document_no_template_blocked(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Step without template_type → blocked."""
        step = IncassoPipelineStep(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            name="Geen template",
            sort_order=99,
            min_wait_days=0,
            max_wait_days=0,
            template_type=None,
        )
        db.add(step)
        await db.flush()

        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=step,
        )
        await db.commit()

        resp = await client.post(
            "/api/incasso/batch/preview",
            json={
                "case_ids": [str(case.id)],
                "action": "generate_document",
            },
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] == 0
        assert len(data["blocked"]) == 1
        # AUDIT-H13: the reason must point to the AI-draft flow, not dead-end on
        # "geen briefsjabloon" — AI/HTML steps have no fixed DOCX template.
        reason = data["blocked"][0]["reason"]
        assert "AI-concept" in reason

    async def test_email_readiness_check(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Opposing party with email → email_ready; without → email_blocked."""
        steps = await create_pipeline_steps(db, test_tenant.id)

        # Case with email on opposing party
        case_with_email = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
            case_number="2026-00010",
        )
        # Case without email on opposing party
        no_email_person = Contact(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            contact_type="person",
            name="Piet Zonder Email",
            email=None,
        )
        db.add(no_email_person)
        await db.flush()
        case_no_email = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            no_email_person,
            test_user,
            step=steps[0],
            case_number="2026-00011",
        )
        await db.commit()

        resp = await client.post(
            "/api/incasso/batch/preview",
            json={
                "case_ids": [str(case_with_email.id), str(case_no_email.id)],
                "action": "generate_document",
            },
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] == 2
        assert data["email_ready"] == 1
        assert len(data["email_blocked"]) == 1

    async def test_advance_step_skips_closed(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Case with status 'betaald' is blocked for advance_step."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
            status="betaald",
        )
        await db.commit()

        resp = await client.post(
            "/api/incasso/batch/preview",
            json={
                "case_ids": [str(case.id)],
                "action": "advance_step",
                "target_step_id": str(steps[1].id),
            },
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] == 0
        assert len(data["blocked"]) == 1
        assert "betaald" in data["blocked"][0]["reason"]


# Need Contact import for email_readiness test
from app.relations.models import Contact  # noqa: E402

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: Batch Execute (API tests with mocked external services)
# ═══════════════════════════════════════════════════════════════════════════


# Standard mock returns for render_docx and docx_to_pdf
_MOCK_DOCX = (b"PK-fake-docx", "aanmaning_2026-00001.docx", "aanmaning", b"snapshot")
_MOCK_PDF = b"%PDF-1.4-fake"


class TestBatchExecute:
    """Tests for POST /api/incasso/batch — 8 tests."""

    @staticmethod
    async def _seed_rates(db):
        """Seed interest rates needed for financial summary in document generation."""
        for rate_type in ("statutory", "commercial"):
            db.add(
                InterestRate(
                    id=uuid.uuid4(),
                    rate_type=rate_type,
                    rate=Decimal("7.00"),
                    effective_from=date(2024, 1, 1),
                )
            )
        await db.flush()

    async def test_generate_document_without_email(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Generate document only (send_email=false).

        Document created, tasks completed, case advanced.
        """
        await self._seed_rates(db)
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        await create_pipeline_task(db, test_tenant.id, case, steps[0])
        await db.commit()

        with (
            patch(
                "app.incasso.service.render_docx",
                new_callable=AsyncMock,
                return_value=_MOCK_DOCX,
            ),
            patch(
                "app.incasso.service.docx_to_pdf",
                new_callable=AsyncMock,
                return_value=_MOCK_PDF,
            ),
        ):
            resp = await client.post(
                "/api/incasso/batch",
                json={
                    "case_ids": [str(case.id)],
                    "action": "generate_document",
                    "send_email": False,
                },
                headers=auth_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["processed"] == 1
        assert data["emails_sent"] == 0
        assert data["tasks_auto_completed"] == 1
        assert data["cases_auto_advanced"] == 1
        assert len(data["generated_document_ids"]) == 1

        # Verify document in DB
        result = await db.execute(
            select(GeneratedDocument).where(GeneratedDocument.case_id == case.id)
        )
        assert result.scalar_one_or_none() is not None

    async def test_generate_document_with_email(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Generate doc + send email. EmailLog created, emails_sent=1."""
        await self._seed_rates(db)
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        await create_pipeline_task(db, test_tenant.id, case, steps[0])
        await db.commit()

        with (
            patch(
                "app.incasso.service.render_docx",
                new_callable=AsyncMock,
                return_value=_MOCK_DOCX,
            ),
            patch(
                "app.incasso.service.docx_to_pdf",
                new_callable=AsyncMock,
                return_value=_MOCK_PDF,
            ),
            patch(
                "app.incasso.service.send_with_attachment",
                side_effect=_fake_send_with_attachment,
            ),
        ):
            resp = await client.post(
                "/api/incasso/batch",
                json={
                    "case_ids": [str(case.id)],
                    "action": "generate_document",
                    "send_email": True,
                },
                headers=auth_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["processed"] == 1
        assert data["emails_sent"] == 1
        assert data["emails_failed"] == 0

        # EmailLog should exist
        result = await db.execute(select(EmailLog).where(EmailLog.case_id == case.id))
        email_log = result.scalar_one_or_none()
        assert email_log is not None
        assert email_log.status == "sent"

    async def test_advance_step(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Advance step moves case to target step and creates tasks."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        await db.commit()

        resp = await client.post(
            "/api/incasso/batch",
            json={
                "case_ids": [str(case.id)],
                "action": "advance_step",
                "target_step_id": str(steps[1].id),
            },
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["processed"] == 1

        # Case should be on Sommatie now
        await db.refresh(case)
        assert case.incasso_step_id == steps[1].id

        # Tasks created for new step
        result = await db.execute(
            select(WorkflowTask).where(
                WorkflowTask.case_id == case.id,
                WorkflowTask.action_config["step_id"].astext == str(steps[1].id),
            )
        )
        assert result.scalar_one_or_none() is not None

    async def test_advance_step_skips_closed(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Closed/paid cases are skipped with error."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
            status="betaald",
        )
        await db.commit()

        resp = await client.post(
            "/api/incasso/batch",
            json={
                "case_ids": [str(case.id)],
                "action": "advance_step",
                "target_step_id": str(steps[1].id),
            },
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["processed"] == 0
        assert data["skipped"] == 1
        assert any("betaald" in e for e in data["errors"])

    async def test_multiple_cases_all_processed(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Batch of 3 cases — all processed and auto-advanced."""
        await self._seed_rates(db)
        steps = await create_pipeline_steps(db, test_tenant.id)
        cases = []
        for i in range(3):
            c = await create_incasso_case(
                db,
                test_tenant.id,
                test_company,
                test_person,
                test_user,
                step=steps[0],
                case_number=f"2026-0010{i}",
            )
            await create_pipeline_task(db, test_tenant.id, c, steps[0])
            cases.append(c)
        await db.commit()

        with (
            patch(
                "app.incasso.service.render_docx",
                new_callable=AsyncMock,
                return_value=_MOCK_DOCX,
            ),
            patch(
                "app.incasso.service.docx_to_pdf",
                new_callable=AsyncMock,
                return_value=_MOCK_PDF,
            ),
        ):
            resp = await client.post(
                "/api/incasso/batch",
                json={
                    "case_ids": [str(c.id) for c in cases],
                    "action": "generate_document",
                    "send_email": False,
                },
                headers=auth_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["processed"] == 3
        assert data["tasks_auto_completed"] == 3
        assert data["cases_auto_advanced"] == 3
        assert len(data["generated_document_ids"]) == 3

    async def test_partial_failure_one_case_fails(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """When render_docx raises for one case, others still process."""
        await self._seed_rates(db)
        steps = await create_pipeline_steps(db, test_tenant.id)
        case_ok = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
            case_number="2026-00200",
        )
        await create_pipeline_task(db, test_tenant.id, case_ok, steps[0])
        case_fail = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
            case_number="2026-00201",
        )
        await create_pipeline_task(db, test_tenant.id, case_fail, steps[0])
        await db.commit()

        call_count = 0

        async def _render_docx_maybe_fail(db, tenant_id, case, template_type, **kwargs):
            nonlocal call_count
            call_count += 1
            if case.case_number == "2026-00201":
                raise RuntimeError("Template niet gevonden")
            return _MOCK_DOCX

        with (
            # Dwing de DOCX-route af (geen e-mailsjabloon) zodat render_docx wordt
            # aangeroepen — dit test de veerkracht van de Word-brief-route.
            patch("app.incasso.service.render_incasso_email", return_value=None),
            patch("app.incasso.service.render_docx", side_effect=_render_docx_maybe_fail),
            patch(
                "app.incasso.service.docx_to_pdf",
                new_callable=AsyncMock,
                return_value=_MOCK_PDF,
            ),
        ):
            resp = await client.post(
                "/api/incasso/batch",
                json={
                    "case_ids": [str(case_ok.id), str(case_fail.id)],
                    "action": "generate_document",
                    "send_email": False,
                },
                headers=auth_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["processed"] == 1
        assert data["skipped"] == 1
        assert any("2026-00201" in e for e in data["errors"])

    async def test_email_failure_doesnt_block_document(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Email failure: document blijft bestaan (emails_failed=1), maar de zaak
        schuift NIET door en taken worden niet afgerond (Codex-review portie 1)."""
        await self._seed_rates(db)
        steps = await create_pipeline_steps(db, test_tenant.id)
        case = await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
        )
        await create_pipeline_task(db, test_tenant.id, case, steps[0])
        await db.commit()

        with (
            patch(
                "app.incasso.service.render_docx",
                new_callable=AsyncMock,
                return_value=_MOCK_DOCX,
            ),
            patch(
                "app.incasso.service.docx_to_pdf",
                new_callable=AsyncMock,
                return_value=_MOCK_PDF,
            ),
            patch(
                "app.incasso.service.send_with_attachment",
                side_effect=RuntimeError("SMTP connection failed"),
            ),
        ):
            resp = await client.post(
                "/api/incasso/batch",
                json={
                    "case_ids": [str(case.id)],
                    "action": "generate_document",
                    "send_email": True,
                },
                headers=auth_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["processed"] == 1  # Document still generated
        assert data["emails_sent"] == 0
        assert data["emails_failed"] == 1
        assert len(data["generated_document_ids"]) == 1
        # Niets verstuurd → zaak niet doorgeschoven, taken niet afgerond.
        assert data["tasks_auto_completed"] == 0
        assert data["cases_auto_advanced"] == 0

    async def test_empty_case_ids_returns_400(self, client, auth_headers):
        """Empty case_ids → 400 error."""
        resp = await client.post(
            "/api/incasso/batch",
            json={
                "case_ids": [],
                "action": "generate_document",
            },
            headers=auth_headers,
        )

        # Either 400 or 422 depending on validation
        assert resp.status_code in (400, 422)

    async def test_recalculate_interest_resyncs_financial_cache(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Batch 'recalculate_interest' must resync the cached totals, not no-op
        (AUDIT-MEDIUM).

        The old version only re-set total_principal to the value it already held
        and never touched total_paid, yet reported the case as 'processed'. Here a
        payment exists but the cached total_paid is stale at 0.00 — the action must
        bring it in line with the live payments.
        """
        case = await create_incasso_case(
            db, test_tenant.id, test_company, test_person, test_user
        )
        # A live claim (5000) and a live payment (1000)...
        db.add(
            Claim(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                case_id=case.id,
                description="Factuur 2026-001",
                principal_amount=Decimal("5000.00"),
                default_date=date(2026, 1, 1),
            )
        )
        db.add(
            Payment(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                case_id=case.id,
                amount=Decimal("1000.00"),
                payment_date=date(2026, 2, 1),
            )
        )
        # ...but the cache is stale (helper seeded total_paid=0.00).
        case.total_paid = Decimal("0.00")
        await db.commit()

        resp = await client.post(
            "/api/incasso/batch",
            json={"case_ids": [str(case.id)], "action": "recalculate_interest"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["processed"] == 1

        await db.refresh(case)
        assert case.total_paid == Decimal("1000.00")  # resynced from the payment
        assert case.total_principal == Decimal("5000.00")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: Pipeline Overview (API tests)
# ═══════════════════════════════════════════════════════════════════════════


class TestPipelineOverview:
    """Tests for GET /api/incasso/pipeline — 2 tests."""

    async def test_cases_grouped_by_step(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Cases appear in the correct pipeline columns."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
            case_number="2026-00301",
        )
        await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[1],
            case_number="2026-00302",
        )
        await db.commit()

        resp = await client.get(
            "/api/incasso/pipeline",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_cases"] == 2

        # Find columns by step name
        col_aanmaning = next(c for c in data["columns"] if c["step"]["name"] == "Aanmaning")
        col_sommatie = next(c for c in data["columns"] if c["step"]["name"] == "Sommatie")
        assert col_aanmaning["count"] == 1
        assert col_sommatie["count"] == 1

    async def test_unassigned_cases(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Cases without a pipeline step appear in unassigned."""
        await create_pipeline_steps(db, test_tenant.id)
        await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=None,
            case_number="2026-00400",
        )
        await db.commit()

        resp = await client.get(
            "/api/incasso/pipeline",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["unassigned"]) == 1

    async def test_terminal_step_cases_excluded_from_board(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """A case parked on a terminal step ('Betaald') is closed and must leave
        the active board, even though move_case_to_step never writes case.status —
        so its status is still e.g. 'sommatie' (AUDIT-H11)."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        terminal = IncassoPipelineStep(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            name="Betaald",
            sort_order=99,
            is_terminal=True,
        )
        db.add(terminal)
        await db.flush()

        # One genuinely open case + one parked on the terminal step with a stale,
        # non-closed workflow status.
        await create_incasso_case(
            db, test_tenant.id, test_company, test_person, test_user,
            step=steps[0], case_number="2026-00310",
        )
        await create_incasso_case(
            db, test_tenant.id, test_company, test_person, test_user,
            step=terminal, case_number="2026-00311", status="sommatie",
        )
        await db.commit()

        resp = await client.get("/api/incasso/pipeline", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        # The closed (terminal-step) case is excluded from the board entirely.
        assert data["total_cases"] == 1
        col_aanmaning = next(c for c in data["columns"] if c["step"]["name"] == "Aanmaning")
        col_betaald = next(c for c in data["columns"] if c["step"]["name"] == "Betaald")
        assert col_aanmaning["count"] == 1
        assert col_betaald["count"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: Queue Counts (API tests)
# ═══════════════════════════════════════════════════════════════════════════


class TestQueueCounts:
    """Tests for GET /api/incasso/queues/counts — 3 tests."""

    async def test_empty_returns_zeros(self, client, auth_headers, db, test_tenant):
        """No cases → all counts zero."""
        await create_pipeline_steps(db, test_tenant.id)
        await db.commit()

        resp = await client.get(
            "/api/incasso/queues/counts",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["ready_next_step"] == 0
        assert data["wik_expired"] == 0
        assert data["action_required"] == 0

    async def test_counts_with_data(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Case in first step for 15 days → wik_expired counted."""
        steps = await create_pipeline_steps(db, test_tenant.id)
        await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=steps[0],
            days_in_step=15,
            case_number="2026-00500",
        )
        await db.commit()

        resp = await client.get(
            "/api/incasso/queues/counts",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["wik_expired"] >= 1

    async def test_unassigned_in_action_required(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Unassigned case counted in action_required."""
        await create_pipeline_steps(db, test_tenant.id)
        await create_incasso_case(
            db,
            test_tenant.id,
            test_company,
            test_person,
            test_user,
            step=None,
            case_number="2026-00600",
        )
        await db.commit()

        resp = await client.get(
            "/api/incasso/queues/counts",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["action_required"] >= 1


# ── AUDIT-H10: verweer-switch must update the persisted step_entered_at ──────


def test_step_entered_at_is_the_real_column_not_a_phantom():
    """The verweer-switch wrote to `incasso_step_entered_at`, which is NOT a
    mapped column on Case (only a Pydantic schema field), so the write was a
    silent no-op and the "days in step" counter never reset. The real, persisted
    column is `step_entered_at`. This locks in which name actually hits the DB.
    """
    from sqlalchemy import inspect

    from app.cases.models import Case

    column_keys = {attr.key for attr in inspect(Case).column_attrs}
    assert "step_entered_at" in column_keys
    assert "incasso_step_entered_at" not in column_keys, (
        "incasso_step_entered_at is not a DB column — writing to it persists "
        "nothing (AUDIT-H10). Use step_entered_at."
    )


# ── AUDIT-#97: verweer-switch must run through move_case_to_step ─────────────


async def test_verweer_switch_routes_through_move_case_to_step(
    db, test_tenant, test_user, test_company
):
    """An inbound defense email switches the case to 'Verweer beantwoorden'. That
    switch must go through the central move_case_to_step transition so it leaves
    a CaseStepHistory row and a pipeline_change activity (audit #97) — the old
    code set incasso_step_id/step_entered_at directly, leaving no history/log.
    """
    from datetime import UTC, datetime
    from unittest.mock import AsyncMock, patch

    from app.cases.models import CaseActivity
    from app.email.oauth_models import EmailAccount
    from app.email.synced_email_models import SyncedEmail
    from app.incasso.automation_service import trigger_defense_response_for_email
    from app.incasso.models import CaseStepHistory

    # Hoofdpad step (must be in _HOOFDPAD_STEPS_FOR_DEFENSE) + the verweer step.
    eerste = IncassoPipelineStep(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Eerste sommatie",
        sort_order=1,
        min_wait_days=0,
        max_wait_days=4,
    )
    verweer = IncassoPipelineStep(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Verweer beantwoorden",
        sort_order=10,
        min_wait_days=0,
        max_wait_days=0,
        is_hold_step=True,
    )
    db.add_all([eerste, verweer])
    await db.flush()

    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user,
        step=eerste, case_number="2026-09100", days_in_step=3,
    )
    old_entered = case.step_entered_at

    account = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        provider="gmail",
        email_address="kantoor@test.nl",
        access_token_enc=b"x",
        refresh_token_enc=b"y",
    )
    db.add(account)
    await db.flush()
    email = SyncedEmail(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email_account_id=account.id,
        case_id=case.id,
        provider_message_id="defense-1",
        from_email="debiteur@example.nl",
        direction="inbound",
        body_text="Ik betwist de vordering volledig.",
        email_date=datetime.now(UTC),
    )
    db.add(email)
    await db.flush()

    # Stub the AI draft generation — the step-switch happens before it is called.
    with patch(
        "app.incasso.automation_service.generate_draft_for_step",
        new=AsyncMock(return_value=None),
    ):
        await trigger_defense_response_for_email(
            db, test_tenant.id, email.id, "juridisch_verweer"
        )

    await db.refresh(case)
    assert case.incasso_step_id == verweer.id
    assert case.step_entered_at != old_entered  # timer reset

    # #97: the switch left an audit trail via move_case_to_step.
    history = (
        await db.execute(
            select(CaseStepHistory).where(
                CaseStepHistory.case_id == case.id,
                CaseStepHistory.step_id == verweer.id,
            )
        )
    ).scalars().all()
    assert len(history) == 1
    assert history[0].exited_at is None  # currently in the verweer step

    activities = (
        await db.execute(
            select(CaseActivity).where(
                CaseActivity.case_id == case.id,
                CaseActivity.activity_type == "pipeline_change",
            )
        )
    ).scalars().all()
    assert len(activities) >= 1


# ── AUDIT-H12: only evaluable (timeout) rules are seeded ─────────────────────


async def test_seed_omits_dead_payment_and_debtor_rules(db, test_tenant):
    """The rule-evaluator only reads trigger_type='timeout'. The old seed also
    created 'payment' and 'debtor_response' rules that were never evaluated (dead
    config surfacing as loze UI-acties). The seed must now create timeout rules
    only (AUDIT-H12)."""
    from app.incasso.service import seed_default_transitions

    transitions = await seed_default_transitions(db, test_tenant.id)
    await db.commit()

    trigger_types = {t.trigger_type for t in transitions}
    assert "timeout" in trigger_types
    assert "payment" not in trigger_types
    assert "debtor_response" not in trigger_types


# ── S182: dubbele/dode timeout-regels — filter naar inactieve stap + determinisme


async def _mk_step(db, tenant_id, name, sort_order, *, is_active=True):
    step = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name=name,
        sort_order=sort_order, min_wait_days=0, max_wait_days=0,
        is_active=is_active,
    )
    db.add(step)
    await db.flush()
    return step


async def _mk_timeout_rule(db, tenant_id, from_step, to_step, *, days, created_at):
    from app.incasso.models import StepTransition

    rule = StepTransition(
        id=uuid.uuid4(), tenant_id=tenant_id,
        from_step_id=from_step.id, to_step_id=to_step.id,
        trigger_type="timeout", action="advance_to_step",
        is_default=True, is_active=True,
        condition='{"days": %d}' % days,
        created_at=created_at,
    )
    db.add(rule)
    await db.flush()
    return rule


async def test_timeout_rule_to_inactive_step_is_skipped(
    db, test_tenant, test_user, test_company, caplog
):
    """Two default timeout rules leave the same active step; the OLDER one points
    at an INACTIVE target (no template → ValueError in the draft-generator), the
    newer at an active target. The evaluator must skip the inactive-target rule
    and match the active one — regardless of created_at order — and warn about
    the duplicate config (S182)."""
    import logging
    from datetime import UTC, datetime, timedelta

    from app.incasso.automation_service import evaluate_timeout_rules

    from_step = await _mk_step(db, test_tenant.id, "Tweede sommatie", 5)
    active_target = await _mk_step(db, test_tenant.id, "Derde sommatie", 6)
    inactive_target = await _mk_step(
        db, test_tenant.id, "Ingebrekestelling (oud)", 7, is_active=False
    )
    base = datetime(2026, 1, 1, tzinfo=UTC)
    # Inactive-target rule is the OLDEST → would win without the filter.
    await _mk_timeout_rule(
        db, test_tenant.id, from_step, inactive_target, days=1, created_at=base
    )
    await _mk_timeout_rule(
        db, test_tenant.id, from_step, active_target, days=1,
        created_at=base + timedelta(hours=1),
    )
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user,
        step=from_step, case_number="2026-08200", days_in_step=5,
    )

    with caplog.at_level(logging.WARNING):
        matches = await evaluate_timeout_rules(db, test_tenant.id)

    case_matches = [m for m in matches if m.case_id == case.id]
    assert len(case_matches) == 1
    assert case_matches[0].to_step_id == active_target.id
    assert any("default timeout-regels" in r.message for r in caplog.records)


async def test_timeout_rule_deterministic_oldest_wins(
    db, test_tenant, test_user, test_company
):
    """Two default timeout rules to ACTIVE targets from the same step → the
    oldest (by created_at) is chosen deterministically (S182)."""
    from datetime import UTC, datetime, timedelta

    from app.incasso.automation_service import evaluate_timeout_rules

    from_step = await _mk_step(db, test_tenant.id, "Tweede sommatie", 5)
    older_target = await _mk_step(db, test_tenant.id, "Derde sommatie", 6)
    newer_target = await _mk_step(db, test_tenant.id, "Dagvaarding", 8)
    base = datetime(2026, 2, 1, tzinfo=UTC)
    await _mk_timeout_rule(
        db, test_tenant.id, from_step, older_target, days=1, created_at=base
    )
    await _mk_timeout_rule(
        db, test_tenant.id, from_step, newer_target, days=1,
        created_at=base + timedelta(hours=1),
    )
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user,
        step=from_step, case_number="2026-08201", days_in_step=5,
    )

    matches = await evaluate_timeout_rules(db, test_tenant.id)
    case_matches = [m for m in matches if m.case_id == case.id]
    assert len(case_matches) == 1
    assert case_matches[0].to_step_id == older_target.id


# ── S182: getrouwheids-poort — concept moet dragende dossier-elementen bevatten


def test_fidelity_amount_variants_cover_dutch_and_english():
    from app.incasso.automation_service import _amount_variants

    variants = _amount_variants(Decimal("1234.56"))
    assert "1.234,56" in variants  # NL duizendtal-punt + decimaal-komma
    assert "1234,56" in variants
    assert "1234.56" in variants
    whole = _amount_variants(Decimal("500.00"))
    assert "500,00" in whole
    assert "500,-" in whole


def test_fidelity_issues_detects_missing_elements():
    from app.incasso.automation_service import _draft_fidelity_issues

    body = "Geachte heer, gelieve € 1.234,56 te voldoen."
    issues = _draft_fidelity_issues(
        body,
        step_name="Eerste sommatie",
        template_body="Hoofdsom €\nTe voldoen €",
        case_number="2026-00042",
        amounts={
            "hoofdsom": Decimal("1000.00"),
            "rente": Decimal("0.00"),
            "te_voldoen": Decimal("1234.56"),
        },
    )
    assert any("2026-00042" in i for i in issues)  # dossiernummer mist
    assert any("hoofdsom" in i for i in issues)  # hoofdsom mist
    assert not any("te voldoen" in i for i in issues)  # te_voldoen staat erin


def test_fidelity_issues_clean_body_passes():
    from app.incasso.automation_service import _draft_fidelity_issues

    body = (
        "Betreft: sommatie / 2026-00042\n"
        "Hoofdsom € 1.000,00\nRente € 12,34\nTe voldoen € 1.234,56\n"
    )
    issues = _draft_fidelity_issues(
        body,
        step_name="Eerste sommatie",
        template_body="Hoofdsom €",
        case_number="2026-00042",
        amounts={
            "hoofdsom": Decimal("1000.00"),
            "rente": Decimal("12.34"),
            "te_voldoen": Decimal("1234.56"),
        },
    )
    assert issues == []


def test_fidelity_issues_flags_xxx_on_verweer_step():
    from app.incasso.automation_service import _draft_fidelity_issues

    issues = _draft_fidelity_issues(
        "Betreft: 2026-00042. XXX",
        step_name="Verweer beantwoorden",
        template_body="",
        case_number="2026-00042",
        amounts={},
    )
    assert any("XXX" in i for i in issues)


async def test_draft_gate_regenerates_and_marks_review_task(
    db, test_tenant, test_user, test_company
):
    """Concept zonder dossiernummer → poort regenereert (max 3 AI-calls); blijft
    het fout, dan wordt het concept tóch aangemaakt maar de reviewtaak gemarkeerd
    met een waarschuwing. Nooit stil (S182)."""
    from app.incasso.automation_service import generate_draft_for_step

    steps = await create_pipeline_steps(db, test_tenant.id)
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user,
        step=steps[0], case_number="2026-07300", days_in_step=1,
    )
    bad = {"subject": "s", "body": "Geachte heer, gelieve te betalen."}
    with patch(
        "app.ai_agent.kimi_client.call_draft_ai",
        new=AsyncMock(return_value=(bad, "test-model")),
    ) as mock_ai:
        draft = await generate_draft_for_step(
            db, test_tenant.id, case.id, steps[0].id
        )

    assert mock_ai.await_count == 3  # initieel + 2 regeneraties
    assert draft.sources.get("fidelity_issues")

    task = (await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.case_id == case.id,
            WorkflowTask.task_type == "review_ai_draft",
        )
    )).scalars().first()
    assert task is not None
    assert task.title.startswith("⚠")
    assert "wijkt af" in task.description


async def test_draft_gate_passes_clean_draft_first_try(
    db, test_tenant, test_user, test_company
):
    """Concept mét dossiernummer → geen regeneratie, gewone reviewtaak."""
    from app.incasso.automation_service import generate_draft_for_step

    steps = await create_pipeline_steps(db, test_tenant.id)
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user,
        step=steps[0], case_number="2026-07301", days_in_step=1,
    )
    good = {"subject": "s", "body": "Betreft: aanmaning / 2026-07301. Gelieve te betalen."}
    with patch(
        "app.ai_agent.kimi_client.call_draft_ai",
        new=AsyncMock(return_value=(good, "test-model")),
    ) as mock_ai:
        draft = await generate_draft_for_step(
            db, test_tenant.id, case.id, steps[0].id
        )

    assert mock_ai.await_count == 1
    assert not draft.sources.get("fidelity_issues")

    task = (await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.case_id == case.id,
            WorkflowTask.task_type == "review_ai_draft",
        )
    )).scalars().first()
    assert task is not None
    assert not task.title.startswith("⚠")


async def test_draft_gate_fixes_broken_xxx_regeneration(
    db, test_tenant, test_user, test_company
):
    """De oude XXX-check keek naar de dict-sleutels i.p.v. de tekst en heeft dus
    nooit gewerkt. Nu: verweer-concept met achtergebleven 'XXX' wordt geregenereerd
    tot de tekst schoon is (S182)."""
    from app.incasso.automation_service import generate_draft_for_step

    verweer = IncassoPipelineStep(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Verweer beantwoorden",
        sort_order=10,
        min_wait_days=0,
        max_wait_days=0,
        is_hold_step=True,
        email_subject_template="Reactie verweer {{ zaak.zaaknummer }}",
        email_body_template="Geachte, XXX. Betreft 2026-07302.",
    )
    db.add(verweer)
    await db.flush()
    case = await create_incasso_case(
        db, test_tenant.id, test_company, None, test_user,
        step=verweer, case_number="2026-07302", days_in_step=1,
    )
    with_xxx = {"subject": "s", "body": "Betreft: 2026-07302. XXX"}
    clean = {"subject": "s", "body": "Betreft: 2026-07302. Wij weerleggen uw verweer."}
    with patch(
        "app.ai_agent.kimi_client.call_draft_ai",
        new=AsyncMock(side_effect=[(with_xxx, "m"), (clean, "m")]),
    ) as mock_ai:
        draft = await generate_draft_for_step(
            db, test_tenant.id, case.id, verweer.id,
            incoming_defense="Ik betwist de vordering.",
        )

    assert mock_ai.await_count == 2
    assert "XXX" not in draft.body
    assert not draft.sources.get("fidelity_issues")
