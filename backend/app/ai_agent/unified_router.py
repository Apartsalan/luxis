"""Unified AI draft endpoint — /api/ai/draft.

Routes all three AI draft intents (next_step / reply_to_email / free_compose)
through UnifiedDraftService so output always uses the branded render path.
Lives alongside the older /api/ai-agent endpoints which remain operational
until the frontend is migrated.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.router import _draft_to_response
from app.ai_agent.schemas import AIDraftResponse
from app.ai_agent.unified_draft_service import (
    DraftIntent,
    find_open_reply_draft,
    generate_unified_draft,
)
from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/ai", tags=["ai-unified"])


class UnifiedDraftRequest(BaseModel):
    case_id: uuid.UUID
    intent: DraftIntent
    tone: str | None = None
    source_email_id: uuid.UUID | None = None
    instruction: str | None = None
    # S223 — na "vervangen" laat dit het bestaande open concept vervallen en
    # genereert het opnieuw i.p.v. het bestaande terug te geven.
    force_new: bool = False


class ExistingDraftResponse(BaseModel):
    draft_id: uuid.UUID | None = None


@router.post("/draft", response_model=AIDraftResponse)
async def create_unified_draft(
    data: UnifiedDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an AI draft via the unified pipeline.

    Body fields:
    - case_id: required, dossier UUID
    - intent: required, one of next_step | reply_to_email | free_compose
    - tone: optional, mild | zakelijk | streng (gebruikt door reply_to_email)
    - source_email_id: required when intent=reply_to_email
    - instruction: optional vrije instructie voor de AI
    """
    try:
        draft = await generate_unified_draft(
            db,
            current_user.tenant_id,
            current_user.id,
            case_id=data.case_id,
            intent=data.intent,
            tone=data.tone,
            source_email_id=data.source_email_id,
            instruction=data.instruction,
            force_new=data.force_new,
        )
        await db.commit()
        await db.refresh(draft)
        return _draft_to_response(draft)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Concept genereren mislukt: {e}"
        )


@router.get("/draft/existing", response_model=ExistingDraftResponse)
async def existing_reply_draft(
    case_id: uuid.UUID,
    source_email_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Staat er al een open AI-antwoord op deze mail?

    De "AI-antwoord maken"-knop vraagt dit vóór het genereren, zodat de gebruiker
    kan kiezen: het bestaande concept openen of vervangen (S223, keuze Arsalan).
    """
    draft = await find_open_reply_draft(
        db, current_user.tenant_id, case_id, source_email_id
    )
    return ExistingDraftResponse(draft_id=draft.id if draft else None)
