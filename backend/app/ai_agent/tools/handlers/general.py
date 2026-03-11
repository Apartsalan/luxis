"""General tool handlers — dashboard, search, trust funds."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize


async def handle_dashboard_summary(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    """Get dashboard KPIs and summary statistics."""
    from app.dashboard import service as dashboard_service

    summary = await dashboard_service.get_dashboard_summary(db, tenant_id)
    return serialize(summary)


async def handle_global_search(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    query: str,
    limit: int = 20,
) -> dict:
    """Search across cases, contacts, and documents."""
    from app.search import service as search_service

    results = await search_service.global_search(db, tenant_id, query, limit=limit)
    return {
        "items": [serialize(r) for r in results],
        "count": len(results),
    }


async def handle_trust_fund_balance(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
) -> dict:
    """Get trust fund (derdengelden) balance for a case."""
    from app.trust_funds import service as trust_funds_service

    balance = await trust_funds_service.get_balance(db, tenant_id, uuid.UUID(case_id))
    return serialize(balance)
