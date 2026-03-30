"""Incasso pipeline tool handlers."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize
from app.incasso import service as incasso_service


async def handle_pipeline_overview(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    """Get pipeline overview — all cases grouped by pipeline step."""
    overview = await incasso_service.get_pipeline_overview(db, tenant_id)
    return serialize(overview)


async def handle_pipeline_batch(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_ids: list[str],
    action: str,
    target_step_id: str | None = None,
    send_email: bool = False,
) -> dict:
    """Execute a batch action on multiple cases."""
    result = await incasso_service.batch_execute(
        db,
        tenant_id,
        user_id,
        case_ids=[uuid.UUID(cid) for cid in case_ids],
        action=action,
        target_step_id=uuid.UUID(target_step_id) if target_step_id else None,
        send_email=send_email,
    )
    return serialize(result)


async def handle_pipeline_queue_counts(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    """Get number of cases per pipeline step."""
    counts = await incasso_service.get_queue_counts(db, tenant_id)
    return serialize(counts)
