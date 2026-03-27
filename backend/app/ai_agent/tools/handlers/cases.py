"""Case (dossier) tool handlers."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.tools import serialize
from app.cases import service as cases_service
from app.cases.schemas import CaseActivityCreate, CaseCreate, CaseUpdate


async def handle_case_list(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    search: str | None = None,
    case_type: str | None = None,
    status: str | None = None,
    client_id: str | None = None,
    is_active: bool = True,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """List/search cases with optional filters."""
    cases, total = await cases_service.list_cases(
        db,
        tenant_id,
        page=page,
        per_page=per_page,
        case_type=case_type,
        status=status,
        search=search,
        client_id=uuid.UUID(client_id) if client_id else None,
        is_active=is_active,
    )
    return {
        "items": [
            {
                "id": serialize(c.id),
                "case_number": c.case_number,
                "case_type": c.case_type,
                "debtor_type": c.debtor_type,
                "status": c.status,
                "description": c.description,
                "reference": c.reference,
                "client_name": c.client.name if c.client else None,
                "opposing_party_name": c.opposing_party.name if c.opposing_party else None,
                "date_opened": serialize(c.date_opened),
                "total_principal": serialize(c.total_principal),
                "total_paid": serialize(c.total_paid),
            }
            for c in cases
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


async def handle_case_get(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
) -> dict:
    """Get full case details by ID."""
    case = await cases_service.get_case(db, tenant_id, uuid.UUID(case_id))
    if not case:
        return {"error": "Dossier niet gevonden"}
    return {
        "id": serialize(case.id),
        "case_number": case.case_number,
        "case_type": case.case_type,
        "debtor_type": case.debtor_type,
        "status": case.status,
        "description": case.description,
        "reference": case.reference,
        "court_case_number": case.court_case_number,
        "court_name": case.court_name,
        "interest_type": case.interest_type,
        "contractual_rate": serialize(case.contractual_rate),
        "contractual_compound": case.contractual_compound,
        "client_id": serialize(case.client_id) if hasattr(case, "client_id") else None,
        "client_name": case.client.name if case.client else None,
        "opposing_party_id": (
            serialize(case.opposing_party_id) if hasattr(case, "opposing_party_id") else None
        ),
        "opposing_party_name": case.opposing_party.name if case.opposing_party else None,
        "assigned_to_name": case.assigned_to.full_name if case.assigned_to else None,
        "incasso_step_id": serialize(case.incasso_step_id),
        "date_opened": serialize(case.date_opened),
        "date_closed": serialize(case.date_closed),
        "total_principal": serialize(case.total_principal),
        "total_paid": serialize(case.total_paid),
        "is_active": case.is_active,
    }


async def handle_case_create(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_type: str = "incasso",
    debtor_type: str = "b2b",
    client_id: str,
    date_opened: str,
    description: str | None = None,
    reference: str | None = None,
    opposing_party_id: str | None = None,
    interest_type: str = "statutory",
) -> dict:
    """Create a new case."""
    data = CaseCreate(
        case_type=case_type,
        debtor_type=debtor_type,
        client_id=uuid.UUID(client_id),
        opposing_party_id=uuid.UUID(opposing_party_id) if opposing_party_id else None,
        date_opened=date.fromisoformat(date_opened),
        description=description,
        reference=reference,
        interest_type=interest_type,
    )
    case = await cases_service.create_case(db, tenant_id, user_id, data)
    return {
        "id": serialize(case.id),
        "case_number": case.case_number,
        "case_type": case.case_type,
        "status": case.status,
        "date_opened": serialize(case.date_opened),
    }


async def handle_case_update(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
    description: str | None = None,
    reference: str | None = None,
    opposing_party_id: str | None = None,
    interest_type: str | None = None,
    debtor_type: str | None = None,
) -> dict:
    """Update case fields."""
    data = CaseUpdate(
        description=description,
        reference=reference,
        opposing_party_id=uuid.UUID(opposing_party_id) if opposing_party_id else None,
        interest_type=interest_type,
        debtor_type=debtor_type,
    )
    case = await cases_service.update_case(db, tenant_id, uuid.UUID(case_id), data)
    if not case:
        return {"error": "Dossier niet gevonden"}
    return {
        "id": serialize(case.id),
        "case_number": case.case_number,
        "status": case.status,
        "updated": True,
    }


async def handle_case_add_activity(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    case_id: str,
    activity_type: str,
    title: str,
    description: str | None = None,
) -> dict:
    """Add a note or activity to a case."""
    data = CaseActivityCreate(
        activity_type=activity_type,
        title=title,
        description=description,
    )
    activity = await cases_service.add_activity(db, tenant_id, uuid.UUID(case_id), user_id, data)
    return {
        "id": serialize(activity.id),
        "activity_type": activity.activity_type,
        "title": activity.title,
        "created": True,
    }
