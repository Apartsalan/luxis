"""Tests for the incasso pipeline — P1 QA coverage.

Covers: deadline colors, batch preview, batch execute (with mocked DOCX/PDF/email),
auto-complete tasks, auto-advance pipeline, queue counts, pipeline overview,
and email template building.

Total: 36 test cases.
"""

import uuid
from unittest.mock import AsyncMock, patch

from sqlalchemy import select

from app.cases.models import CaseActivity
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
                CaseActivity.activity_type == "pipeline_advance",
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
        assert "briefsjabloon" in data["blocked"][0]["reason"]

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

    async def test_generate_document_without_email(
        self, client, auth_headers, db, test_tenant, test_user, test_company, test_person
    ):
        """Generate document only (send_email=false).

        Document created, tasks completed, case advanced.
        """
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

        async def _render_docx_maybe_fail(db, tenant_id, case, template_type):
            nonlocal call_count
            call_count += 1
            if case.case_number == "2026-00201":
                raise RuntimeError("Template niet gevonden")
            return _MOCK_DOCX

        with (
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
        """Email failure doesn't prevent document generation. emails_failed=1."""
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
