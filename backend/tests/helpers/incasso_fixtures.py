"""Shared helpers for incasso pipeline tests — creates test data in the DB."""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.cases.models import Case
from app.incasso.models import IncassoPipelineStep
from app.relations.models import Contact
from app.workflow.models import WorkflowTask


async def create_pipeline_steps(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[IncassoPipelineStep]:
    """Create a 3-step pipeline: Aanmaning -> Sommatie -> Dagvaarding.

    Aanmaning: immediate (min=0, max=7), with email templates
    Sommatie: 14-day wait (min=14, max=28), with email templates
    Dagvaarding: 14-day wait (min=14, max=28), no email templates
    """
    steps_data = [
        {
            "name": "Aanmaning",
            "sort_order": 1,
            "min_wait_days": 0,
            "max_wait_days": 7,
            "template_type": "aanmaning",
            "email_subject_template": "Aanmaning inzake {{ zaak.zaaknummer }}",
            "email_body_template": (
                "Geachte {{ wederpartij.naam }},\n\n"
                "Bijgaand treft u een aanmaning aan.\n\n"
                "Met vriendelijke groet,\n{{ kantoor.naam }}"
            ),
        },
        {
            "name": "Sommatie",
            "sort_order": 2,
            "min_wait_days": 14,
            "max_wait_days": 28,
            "template_type": "sommatie",
            "email_subject_template": "Sommatie inzake {{ zaak.zaaknummer }}",
            "email_body_template": (
                "Geachte {{ wederpartij.naam }},\n\n"
                "Bijgaand treft u een sommatie aan.\n\n"
                "Met vriendelijke groet,\n{{ kantoor.naam }}"
            ),
        },
        {
            "name": "Dagvaarding",
            "sort_order": 3,
            "min_wait_days": 14,
            "max_wait_days": 28,
            "template_type": "dagvaarding",
            # No email templates — tests fallback path
        },
    ]
    steps = []
    for d in steps_data:
        step = IncassoPipelineStep(id=uuid.uuid4(), tenant_id=tenant_id, **d)
        db.add(step)
        steps.append(step)
    await db.flush()
    for s in steps:
        await db.refresh(s)
    return steps


async def create_incasso_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    client_contact: Contact,
    opposing_party: Contact | None,
    user: User,
    *,
    step: IncassoPipelineStep | None = None,
    case_number: str = "2026-00001",
    days_in_step: int = 0,
    status: str = "nieuw",
) -> Case:
    """Create an incasso case, optionally assigned to a pipeline step."""
    step_entered = datetime.now(UTC) - timedelta(days=days_in_step) if step else None
    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_number=case_number,
        case_type="incasso",
        status=status,
        description="Test incassozaak",
        client_id=client_contact.id,
        opposing_party_id=opposing_party.id if opposing_party else None,
        assigned_to_id=user.id,
        incasso_step_id=step.id if step else None,
        step_entered_at=step_entered,
        date_opened=date.today() - timedelta(days=days_in_step + 10),
        total_principal=Decimal("5000.00"),
        total_paid=Decimal("0.00"),
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


async def create_pipeline_task(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    step: IncassoPipelineStep,
    *,
    task_type: str = "generate_document",
    status: str = "pending",
) -> WorkflowTask:
    """Create a pipeline-sourced workflow task for a case."""
    task = WorkflowTask(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_id=case.id,
        assigned_to_id=case.assigned_to_id,
        task_type=task_type,
        title=f"{step.name} genereren voor zaak {case.case_number}",
        due_date=date.today(),
        status=status,
        auto_execute=False,
        action_config={"source": "pipeline", "step_id": str(step.id)},
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def create_manual_task(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case,
    *,
    title: str = "Bel debiteur",
    status: str = "pending",
) -> WorkflowTask:
    """Create a manual (non-pipeline) workflow task."""
    task = WorkflowTask(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_id=case.id,
        assigned_to_id=case.assigned_to_id,
        task_type="manual_review",
        title=title,
        due_date=date.today(),
        status=status,
        auto_execute=False,
        action_config={"source": "manual"},
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task
