"""Email compose router — send/draft via connected email provider (Gmail/Outlook).

When a user has a connected email account, this sends via Gmail API instead of SMTP.
This means the email appears in the user's Gmail Sent folder.

Endpoints:
- POST /api/email/compose/send          — Send email via provider
- POST /api/email/compose/draft         — Create draft in provider
- POST /api/email/compose/cases/{id}    — Send from case context (logs activity)
"""

import json
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.cases.models import Case, CaseActivity
from app.database import get_db
from app.dependencies import get_current_user
from app.email.models import EmailLog
from app.email.oauth_service import get_email_account, get_provider, get_valid_access_token
from app.email.synced_email_models import SyncedEmail
from app.shared.exceptions import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email/compose", tags=["email-compose"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class ComposeRequest(BaseModel):
    to: list[str] = Field(..., description="Ontvangers e-mailadressen")
    cc: list[str] | None = Field(default=None, description="CC e-mailadressen")
    subject: str = Field(..., max_length=500, description="Onderwerp")
    body_html: str = Field(..., max_length=100000, description="HTML body")
    reply_to_message_id: str | None = Field(
        default=None, description="Provider message ID om op te antwoorden"
    )


class CaseComposeRequest(BaseModel):
    recipient_email: str = Field(..., max_length=320)
    recipient_name: str | None = Field(default=None, max_length=200)
    cc: list[str] | None = None
    subject: str = Field(..., max_length=500)
    body: str = Field(..., max_length=50000, description="Platte tekst body")


class ComposeResponse(BaseModel):
    success: bool
    provider_message_id: str | None = None
    draft_id: str | None = None
    message: str


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/send", response_model=ComposeResponse)
async def send_via_provider(
    data: ComposeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send an email via the connected email provider (Gmail/Outlook)."""
    account = await get_email_account(db, user.id, user.tenant_id)
    if not account:
        raise BadRequestError("Geen e-mailaccount verbonden. Ga naar Instellingen → E-mail.")

    provider = get_provider(account.provider)
    access_token = await get_valid_access_token(db, account)

    try:
        message_id = await provider.send_message(
            access_token,
            to=data.to,
            subject=data.subject,
            body_html=data.body_html,
            cc=data.cc,
            reply_to_message_id=data.reply_to_message_id,
        )
        return ComposeResponse(
            success=True,
            provider_message_id=message_id,
            message="E-mail verzonden via " + account.provider,
        )
    except Exception as e:
        logger.error(f"Email verzenden mislukt via {account.provider}: {e}")
        raise BadRequestError(f"Verzenden mislukt: {e}")


@router.post("/draft", response_model=ComposeResponse)
async def create_draft_via_provider(
    data: ComposeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a draft in the connected email provider."""
    account = await get_email_account(db, user.id, user.tenant_id)
    if not account:
        raise BadRequestError("Geen e-mailaccount verbonden. Ga naar Instellingen → E-mail.")

    provider = get_provider(account.provider)
    access_token = await get_valid_access_token(db, account)

    try:
        draft_id = await provider.create_draft(
            access_token,
            to=data.to,
            subject=data.subject,
            body_html=data.body_html,
            cc=data.cc,
        )
        return ComposeResponse(
            success=True,
            draft_id=draft_id,
            message="Concept aangemaakt in " + account.provider,
        )
    except Exception as e:
        logger.error(f"Draft aanmaken mislukt via {account.provider}: {e}")
        raise BadRequestError(f"Concept aanmaken mislukt: {e}")


@router.post("/cases/{case_id}", response_model=ComposeResponse)
async def send_from_case(
    case_id: uuid.UUID,
    data: CaseComposeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send email from case context via provider.

    Falls back to SMTP if no provider connected.
    Logs EmailLog + CaseActivity for audit trail.
    """
    # Verify case exists
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == user.tenant_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError("Dossier niet gevonden")

    account = await get_email_account(db, user.id, user.tenant_id)

    if not account:
        # No provider connected — fall back to SMTP
        raise BadRequestError(
            "Geen e-mailaccount verbonden. Verbind Gmail of Outlook via Instellingen → E-mail, "
            "of gebruik de bestaande SMTP e-mail functie."
        )

    provider = get_provider(account.provider)
    access_token = await get_valid_access_token(db, account)

    body_html = data.body.replace("\n", "<br>")
    provider_message_id = None

    # Create email log
    email_log = EmailLog(
        tenant_id=user.tenant_id,
        case_id=case.id,
        document_id=None,
        template="provider_compose",
        recipient=data.recipient_email,
        subject=data.subject,
        status="sent",
    )

    try:
        provider_message_id = await provider.send_message(
            access_token,
            to=[data.recipient_email],
            subject=data.subject,
            body_html=body_html,
            cc=data.cc,
        )
    except Exception as e:
        email_log.status = "failed"
        email_log.error_message = str(e)
        logger.error(f"E-mail verzenden mislukt via {account.provider} voor zaak {case_id}: {e}")

    db.add(email_log)
    await db.flush()
    await db.refresh(email_log)

    # Also store as synced email (so it shows in correspondentie tab immediately)
    if provider_message_id and email_log.status == "sent":
        synced = SyncedEmail(
            tenant_id=user.tenant_id,
            email_account_id=account.id,
            case_id=case.id,
            provider_message_id=provider_message_id,
            subject=data.subject,
            from_email=account.email_address,
            from_name=user.full_name or "",
            to_emails=json.dumps([data.recipient_email]),
            cc_emails=json.dumps(data.cc or []),
            snippet=data.body[:200] if data.body else "",
            body_text=data.body,
            body_html=body_html,
            direction="outbound",
            is_read=True,
            has_attachments=False,
            email_date=datetime.now(UTC),
            synced_at=datetime.now(UTC),
        )
        db.add(synced)

    # Log activity on the case
    recipient_label = data.recipient_name or data.recipient_email
    activity = CaseActivity(
        tenant_id=user.tenant_id,
        case_id=case.id,
        user_id=user.id,
        activity_type="email",
        title=f"E-mail verzonden naar {recipient_label}",
        description=f"Onderwerp: {data.subject} (via {account.provider})",
    )
    db.add(activity)
    await db.flush()

    if email_log.status == "failed":
        raise BadRequestError(f"E-mail verzenden mislukt: {email_log.error_message}")

    return ComposeResponse(
        success=True,
        provider_message_id=provider_message_id,
        message=f"E-mail verzonden via {account.provider}",
    )
