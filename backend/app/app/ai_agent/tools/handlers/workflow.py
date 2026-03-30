"""Workflow tool handlers — tasks, verjaring check."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize
from app.workflow import service as workflow_service
from app.workflow.schemas import WorkflowTaskCreate


async def handle_task_create(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
    task_type: str,
    title: str,
    due_date: str,
    description: str | None = None,
    assigned_to_id: str | None = None,
) -> dict:
    """Create a workflow task."""
    data = WorkflowTaskCreate(
        case_id=uuid.UUID(case_id),
        assigned_to_id=uuid.UUID(assigned_to_id) if assigned_to_id else None,
        task_type=task_type,
        title=title,
        description=description,
        due_date=date.fromisoformat(due_date),
    )
    task = await workflow_service.create_task(db, tenant_id, data)
    return {
        "id": serialize(task.id),
        "title": task.title,
        "task_type": task.task_type,
        "due_date": serialize(task.due_date),
        "status": task.status,
        "created": True,
    }


async def handle_task_list(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str | None = None,
    status: str | None = None,
    assigned_to_id: str | None = None,
) -> dict:
    """List workflow tasks with optional filters."""
    tasks = await workflow_service.list_tasks(
        db,
        tenant_id,
        case_id=uuid.UUID(case_id) if case_id else None,
        status=status,
        assigned_to_id=uuid.UUID(assigned_to_id) if assigned_to_id else None,
    )
    return {
        "items": [
            {
                "id": serialize(t.id),
                "case_id": serialize(t.case_id),
                "title": t.title,
                "task_type": t.task_type,
                "due_date": serialize(t.due_date),
                "status": t.status,
                "assigned_to_id": serialize(t.assigned_to_id),
            }
            for t in tasks
        ],
        "count": len(tasks),
    }


async def handle_verjaring_check(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    """Check all active cases for approaching statute of limitations (verjaring)."""
    results = await workflow_service.check_verjaring(db, tenant_id)
    return {
        "items": [serialize(r) for r in results],
        "count": len(results),
    }
