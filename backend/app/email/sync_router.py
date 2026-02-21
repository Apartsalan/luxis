"""Email sync router — endpoints for syncing inbox and reading emails per dossier.

Endpoints:
- POST /api/email/sync              — Trigger inbox sync for current user
- GET  /api/email/cases/{id}/emails  — Get synced emails for a case
- GET  /api/email/unlinked           — Get emails not linked to any case
- POST /api/email/link               — Manually link an email to a case
- GET  /api/email/messages/{id}      — Get a single synced email with full body
"""

import json
import logging
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.email.oauth_service import get_email_account
from app.email.sync_service import (
    get_case_emails,
    get_unlinked_emails,
    link_email_to_case,
    sync_emails_for_account,
)
from app.email.synced_email_models import SyncedEmail
from app.shared.exceptions import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email-sync"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class SyncResponse(BaseModel):
    fetched: int
    new: int
    linked: int
    skipped: int


class SyncedEmailSummary(BaseModel):
    id: str
    subject: str
    from_email: str
    from_name: str
    to_emails: list[str]
    snippet: str
    direction: str
    is_read: bool
    has_attachments: bool
    email_date: str
    case_id: str | None


class SyncedEmailDetail(BaseModel):
    id: str
    subject: str
    from_email: str
    from_name: str
    to_emails: list[str]
    cc_emails: list[str]
    snippet: str
    body_html: str
    body_text: str
    direction: str
    is_read: bool
    has_attachments: bool
    email_date: str
    case_id: str | None
    provider_thread_id: str | None


class CaseEmailsResponse(BaseModel):
    emails: list[SyncedEmailSummary]
    total: int


class LinkEmailRequest(BaseModel):
    email_id: str
    case_id: str


class LinkEmailResponse(BaseModel):
    success: bool
    email_id: str
    case_id: str


# ── Helpers ──────────────────────────────────────────────────────────────────


def _email_to_summary(email: SyncedEmail) -> SyncedEmailSummary:
    """Convert a SyncedEmail to a summary response."""
    try:
        to_emails = json.loads(email.to_emails) if email.to_emails else []
    except (json.JSONDecodeError, TypeError):
        to_emails = []

    return SyncedEmailSummary(
        id=str(email.id),
        subject=email.subject,
        from_email=email.from_email,
        from_name=email.from_name,
        to_emails=to_emails,
        snippet=email.snippet,
        direction=email.direction,
        is_read=email.is_read,
        has_attachments=email.has_attachments,
        email_date=email.email_date.isoformat(),
        case_id=str(email.case_id) if email.case_id else None,
    )


def _email_to_detail(email: SyncedEmail) -> SyncedEmailDetail:
    """Convert a SyncedEmail to a detail response."""
    try:
        to_emails = json.loads(email.to_emails) if email.to_emails else []
    except (json.JSONDecodeError, TypeError):
        to_emails = []
    try:
        cc_emails = json.loads(email.cc_emails) if email.cc_emails else []
    except (json.JSONDecodeError, TypeError):
        cc_emails = []

    return SyncedEmailDetail(
        id=str(email.id),
        subject=email.subject,
        from_email=email.from_email,
        from_name=email.from_name,
        to_emails=to_emails,
        cc_emails=cc_emails,
        snippet=email.snippet,
        body_html=email.body_html,
        body_text=email.body_text,
        direction=email.direction,
        is_read=email.is_read,
        has_attachments=email.has_attachments,
        email_date=email.email_date.isoformat(),
        case_id=str(email.case_id) if email.case_id else None,
        provider_thread_id=email.provider_thread_id,
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/sync", response_model=SyncResponse)
async def trigger_sync(
    max_results: int = Query(default=100, le=500, description="Max emails op te halen"),
    query: str | None = Query(default=None, description="Gmail search query"),
    case_id: uuid.UUID | None = Query(default=None, description="Dossier ID — filtert en linkt emails automatisch"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger an inbox sync for the current user's connected email account.

    If case_id is provided, the sync will:
    1. Build a Gmail query from the case's contact email addresses
    2. Auto-link all matching emails to the case
    3. Re-link previously unlinked emails that match
    """
    account = await get_email_account(db, user.id, user.tenant_id)
    if not account:
        raise BadRequestError("Geen e-mailaccount verbonden. Ga naar Instellingen → E-mail.")

    stats = await sync_emails_for_account(
        db, account, max_results=max_results, query=query, force_case_id=case_id
    )
    return SyncResponse(**stats)


@router.get("/cases/{case_id}/emails", response_model=CaseEmailsResponse)
async def get_emails_for_case(
    case_id: uuid.UUID,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all synced emails linked to a specific case."""
    emails, total = await get_case_emails(
        db, user.tenant_id, case_id, limit=limit, offset=offset
    )
    return CaseEmailsResponse(
        emails=[_email_to_summary(e) for e in emails],
        total=total,
    )


@router.get("/unlinked", response_model=CaseEmailsResponse)
async def get_unlinked(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get emails not linked to any case (ongesorteerd queue)."""
    emails, total = await get_unlinked_emails(
        db, user.tenant_id, limit=limit, offset=offset
    )
    return CaseEmailsResponse(
        emails=[_email_to_summary(e) for e in emails],
        total=total,
    )


@router.get("/messages/{email_id}", response_model=SyncedEmailDetail)
async def get_email_detail(
    email_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single synced email with full body content."""
    result = await db.execute(
        select(SyncedEmail).where(
            SyncedEmail.id == email_id,
            SyncedEmail.tenant_id == user.tenant_id,
        )
    )
    email = result.scalar_one_or_none()
    if not email:
        raise NotFoundError("E-mail niet gevonden")

    return _email_to_detail(email)


@router.post("/link", response_model=LinkEmailResponse)
async def link_email(
    data: LinkEmailRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually link an email to a case."""
    email = await link_email_to_case(
        db,
        user.tenant_id,
        uuid.UUID(data.email_id),
        uuid.UUID(data.case_id),
    )
    if not email:
        raise NotFoundError("E-mail niet gevonden")

    return LinkEmailResponse(
        success=True,
        email_id=data.email_id,
        case_id=data.case_id,
    )
