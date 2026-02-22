"""Email sync router — endpoints for syncing inbox and reading emails per dossier.

Endpoints:
- POST /api/email/sync                     — Trigger inbox sync for current user
- GET  /api/email/cases/{id}/emails        — Get synced emails for a case
- GET  /api/email/unlinked                 — Get emails not linked to any case
- GET  /api/email/unlinked/count           — Get count of unlinked emails (sidebar badge)
- POST /api/email/link                     — Manually link an email to a case
- POST /api/email/bulk-link                — Link multiple emails to the same case
- POST /api/email/dismiss                  — Dismiss emails from ongesorteerd queue
- GET  /api/email/suggest-cases/{id}       — Suggest cases for an unlinked email
- GET  /api/email/messages/{id}            — Get a single synced email with full body
- GET  /api/email/messages/{id}/attachments — List attachments for an email
- GET  /api/email/attachments/{id}/download — Download an attachment file
"""

import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.database import get_db
from app.dependencies import get_current_user
from app.email.attachment_models import EmailAttachment
from app.email.oauth_service import get_email_account
from app.email.sync_service import (
    EMAIL_ATTACHMENTS_BASE,
    bulk_link_emails,
    dismiss_emails,
    get_case_emails,
    get_unlinked_count,
    get_unlinked_emails,
    link_email_to_case,
    suggest_cases_for_email,
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
    attachment_count: int = 0
    email_date: str
    case_id: str | None


class AttachmentInfo(BaseModel):
    id: str
    filename: str
    content_type: str
    file_size: int


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
    attachments: list[AttachmentInfo] = []
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


class BulkLinkRequest(BaseModel):
    email_ids: list[str]
    case_id: str


class BulkLinkResponse(BaseModel):
    success: bool
    linked_count: int


class DismissEmailRequest(BaseModel):
    email_ids: list[str]


class DismissEmailResponse(BaseModel):
    success: bool
    dismissed_count: int


class UnlinkedCountResponse(BaseModel):
    count: int


class CaseSuggestion(BaseModel):
    case_id: str
    case_number: str
    description: str | None
    client_name: str
    match_reason: str
    confidence: str


class SuggestCasesResponse(BaseModel):
    suggestions: list[CaseSuggestion]


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
        attachment_count=len(email.attachments) if email.attachments else 0,
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

    attachment_list = []
    if email.attachments:
        for a in email.attachments:
            attachment_list.append(AttachmentInfo(
                id=str(a.id),
                filename=a.filename,
                content_type=a.content_type,
                file_size=a.file_size,
            ))

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
        attachments=attachment_list,
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


@router.post("/bulk-link", response_model=BulkLinkResponse)
async def bulk_link(
    data: BulkLinkRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link multiple emails to the same case in one request."""
    email_uuids = [uuid.UUID(eid) for eid in data.email_ids]
    count = await bulk_link_emails(
        db, user.tenant_id, email_uuids, uuid.UUID(data.case_id)
    )
    return BulkLinkResponse(success=True, linked_count=count)


@router.post("/dismiss", response_model=DismissEmailResponse)
async def dismiss(
    data: DismissEmailRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss emails from the ongesorteerd queue."""
    email_uuids = [uuid.UUID(eid) for eid in data.email_ids]
    count = await dismiss_emails(db, user.tenant_id, email_uuids)
    return DismissEmailResponse(success=True, dismissed_count=count)


@router.get("/unlinked/count", response_model=UnlinkedCountResponse)
async def unlinked_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get count of unlinked non-dismissed emails (for sidebar badge)."""
    count = await get_unlinked_count(db, user.tenant_id)
    return UnlinkedCountResponse(count=count)


@router.get("/suggest-cases/{email_id}", response_model=SuggestCasesResponse)
async def suggest_cases(
    email_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Suggest cases for an unlinked email based on contact + reference matching."""
    suggestions = await suggest_cases_for_email(db, user.tenant_id, email_id)
    return SuggestCasesResponse(
        suggestions=[CaseSuggestion(**s) for s in suggestions]
    )


# ── Attachment schemas ──────────────────────────────────────────────────────


class AttachmentSummary(BaseModel):
    id: str
    filename: str
    content_type: str
    file_size: int


class AttachmentListResponse(BaseModel):
    attachments: list[AttachmentSummary]


# ── Attachment endpoints ────────────────────────────────────────────────────


@router.get("/messages/{email_id}/attachments", response_model=AttachmentListResponse)
async def list_attachments(
    email_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all attachments for a synced email."""
    # Verify email belongs to tenant
    email_result = await db.execute(
        select(SyncedEmail.id).where(
            SyncedEmail.id == email_id,
            SyncedEmail.tenant_id == user.tenant_id,
        )
    )
    if not email_result.scalar_one_or_none():
        raise NotFoundError("E-mail niet gevonden")

    result = await db.execute(
        select(EmailAttachment).where(
            EmailAttachment.synced_email_id == email_id,
            EmailAttachment.tenant_id == user.tenant_id,
        )
    )
    attachments = list(result.scalars().all())

    return AttachmentListResponse(
        attachments=[
            AttachmentSummary(
                id=str(a.id),
                filename=a.filename,
                content_type=a.content_type,
                file_size=a.file_size,
            )
            for a in attachments
        ]
    )


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download an email attachment file."""
    result = await db.execute(
        select(EmailAttachment).where(
            EmailAttachment.id == attachment_id,
            EmailAttachment.tenant_id == user.tenant_id,
        )
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise NotFoundError("Bijlage niet gevonden")

    file_path = (
        EMAIL_ATTACHMENTS_BASE
        / str(attachment.tenant_id)
        / str(attachment.synced_email_id)
        / attachment.stored_filename
    )

    if not file_path.exists():
        raise NotFoundError("Bijlagebestand niet gevonden op schijf")

    return FileResponse(
        path=str(file_path),
        filename=attachment.filename,
        media_type=attachment.content_type,
    )
