"""Endpoints voor geplande mails (S246, 'Verstuur later').

Inplannen gebeurt op de bestaande verzendknop (`POST /api/email/compose/send` met
een gepland moment). Hier alleen: bekijken en annuleren.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.email.scheduled_service import cancel_scheduled_email, list_scheduled_emails

router = APIRouter(prefix="/api/email/scheduled", tags=["email-scheduled"])


class ScheduledEmailResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID | None = None
    scheduled_at: datetime
    status: str
    subject: str
    recipients: str
    attempts: int
    last_error: str | None = None
    sent_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ScheduledEmailResponse])
async def get_scheduled_emails(
    case_id: uuid.UUID | None = None,
    include_done: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Geplande mails — standaard alleen wat nog komt of aandacht vraagt."""
    return await list_scheduled_emails(
        db, user.tenant_id, case_id=case_id, include_done=include_done
    )


@router.delete("/{scheduled_id}", response_model=ScheduledEmailResponse)
async def delete_scheduled_email(
    scheduled_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Annuleer een geplande mail (kan zolang hij nog wacht)."""
    row = await cancel_scheduled_email(db, user.tenant_id, scheduled_id)
    await db.commit()
    return row
