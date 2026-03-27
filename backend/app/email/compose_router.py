"""Email compose router — compose emails via connected provider (Outlook/Gmail).

Generates .eml files that open directly in Outlook desktop as new compose windows
with all content pre-filled (recipients, subject, body, attachments).

Endpoints:
- POST /api/email/compose/send          — Send email via provider (direct)
- POST /api/email/compose/draft         — Create draft in provider
- POST /api/email/compose/cases/{id}    — Generate .eml file for Outlook desktop
- POST /api/email/compose/cases/{id}/render-template — Preview template as HTML
"""

import base64
import logging
import uuid
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.cases.models import Case, CaseActivity, CaseFile
from app.database import get_db
from app.dependencies import get_current_user
from app.documents.docx_service import build_base_context
from app.email.incasso_templates import render_incasso_email
from app.email.oauth_service import get_email_account, get_provider, get_valid_access_token
from app.email.providers.base import OutgoingAttachment
from app.shared.exceptions import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email/compose", tags=["email-compose"])

# Upload storage base path (must match cases/files_service.py)
UPLOADS_BASE = Path("/app/uploads")

# Attachment limits
MAX_ATTACHMENT_SIZE = 3 * 1024 * 1024  # 3 MB (Graph API base64 limit ~4MB)
MAX_ATTACHMENTS = 10


# ── Schemas ──────────────────────────────────────────────────────────────────


class ComposeRequest(BaseModel):
    to: list[str] = Field(..., description="Ontvangers e-mailadressen")
    cc: list[str] | None = Field(default=None, description="CC e-mailadressen")
    subject: str = Field(..., max_length=500, description="Onderwerp")
    body_html: str = Field(..., max_length=100000, description="HTML body")
    reply_to_message_id: str | None = Field(
        default=None, description="Provider message ID om op te antwoorden"
    )


class InlineAttachment(BaseModel):
    filename: str = Field(..., max_length=255)
    data_base64: str
    content_type: str = Field(..., max_length=100)


class CaseComposeRequest(BaseModel):
    recipient_email: str = Field(..., max_length=320)
    recipient_name: str | None = Field(default=None, max_length=200)
    cc: list[str] | None = None
    subject: str = Field(..., max_length=500)
    body: str = Field(default="", max_length=50000, description="Platte tekst body")
    body_html: str | None = Field(
        default=None, max_length=200000, description="HTML body (van template)"
    )
    case_file_ids: list[uuid.UUID] | None = None
    inline_attachments: list[InlineAttachment] | None = None


class ComposeResponse(BaseModel):
    success: bool
    provider_message_id: str | None = None
    draft_id: str | None = None
    web_link: str | None = None
    message: str


class RenderTemplateRequest(BaseModel):
    template_type: str = Field(..., max_length=50)


class RenderTemplateResponse(BaseModel):
    supported: bool
    subject: str | None = None
    body_html: str | None = None


# ── Attachment resolver ──────────────────────────────────────────────────────


async def _resolve_attachments(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    case_file_ids: list[uuid.UUID] | None,
    inline_attachments: list[InlineAttachment] | None,
) -> list[OutgoingAttachment]:
    """Load CaseFiles from disk + decode inline uploads into OutgoingAttachment list."""
    attachments: list[OutgoingAttachment] = []

    # CaseFiles from disk
    if case_file_ids:
        result = await db.execute(
            select(CaseFile).where(
                CaseFile.tenant_id == tenant_id,
                CaseFile.case_id == case_id,
                CaseFile.id.in_(case_file_ids),
                CaseFile.is_active.is_(True),
            )
        )
        case_files = result.scalars().all()

        for cf in case_files:
            file_path = UPLOADS_BASE / str(tenant_id) / str(case_id) / cf.stored_filename
            if not file_path.exists():
                logger.warning("CaseFile %s not found on disk: %s", cf.id, file_path)
                continue
            data = file_path.read_bytes()
            if len(data) > MAX_ATTACHMENT_SIZE:
                raise BadRequestError(
                    f"Bijlage '{cf.original_filename}' is te groot "
                    f"({len(data) // (1024 * 1024)} MB, max 3 MB)"
                )
            attachments.append(
                OutgoingAttachment(
                    filename=cf.original_filename,
                    data=data,
                    content_type=cf.content_type or "application/octet-stream",
                )
            )

    # Inline uploads (base64-encoded)
    if inline_attachments:
        for att in inline_attachments:
            try:
                data = base64.b64decode(att.data_base64)
            except Exception:
                raise BadRequestError(f"Ongeldige bijlage: '{att.filename}'")
            if len(data) > MAX_ATTACHMENT_SIZE:
                raise BadRequestError(
                    f"Bijlage '{att.filename}' is te groot "
                    f"({len(data) // (1024 * 1024)} MB, max 3 MB)"
                )
            attachments.append(
                OutgoingAttachment(
                    filename=att.filename,
                    data=data,
                    content_type=att.content_type or "application/octet-stream",
                )
            )

    if len(attachments) > MAX_ATTACHMENTS:
        raise BadRequestError(f"Maximaal {MAX_ATTACHMENTS} bijlagen toegestaan")

    return attachments


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
        draft_id, web_link = await provider.create_draft(
            access_token,
            to=data.to,
            subject=data.subject,
            body_html=data.body_html,
            cc=data.cc,
        )
        return ComposeResponse(
            success=True,
            draft_id=draft_id,
            web_link=web_link,
            message="Concept aangemaakt in " + account.provider,
        )
    except Exception as e:
        logger.error(f"Draft aanmaken mislukt via {account.provider}: {e}")
        raise BadRequestError(f"Concept aanmaken mislukt: {e}")


@router.post("/cases/{case_id}")
async def compose_eml_from_case(
    case_id: uuid.UUID,
    data: CaseComposeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a .eml file that opens in Outlook desktop as a new email.

    The .eml contains recipients, subject, HTML body, and attachments.
    When opened on Windows, Outlook desktop shows it as a ready-to-send email.
    """
    # Verify case exists
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == user.tenant_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError("Dossier niet gevonden")

    # Resolve body HTML
    if data.body_html:
        body_html = data.body_html
    elif data.body:
        body_html = data.body.replace("\n", "<br>")
    else:
        body_html = ""

    # Resolve attachments
    attachments = await _resolve_attachments(
        db,
        user.tenant_id,
        case_id,
        data.case_file_ids,
        data.inline_attachments,
    )

    # Get sender email from connected account (for From header)
    account = await get_email_account(db, user.id, user.tenant_id)
    sender_email = account.email_address if account else (user.email or "")
    sender_name = user.full_name or ""

    # Build .eml (RFC 2822 MIME message)
    msg = EmailMessage()
    msg["Subject"] = data.subject
    msg["To"] = data.recipient_email
    if data.cc:
        msg["Cc"] = ", ".join(data.cc)
    if sender_email:
        msg["From"] = formataddr((sender_name, sender_email))
    # No Date header → Outlook treats it as unsent/draft
    msg["X-Unsent"] = "1"  # Outlook-specific: opens in compose mode

    # Set HTML body
    msg.set_content(body_html, subtype="html")

    # Add attachments
    for att in attachments:
        maintype, _, subtype = att.content_type.partition("/")
        if not subtype:
            maintype, subtype = "application", "octet-stream"
        msg.add_attachment(
            att.data,
            maintype=maintype,
            subtype=subtype,
            filename=att.filename,
        )

    # Log activity on the case
    recipient_label = data.recipient_name or data.recipient_email
    att_count = len(attachments)
    att_text = f", {att_count} bijlage(n)" if att_count else ""
    activity = CaseActivity(
        tenant_id=user.tenant_id,
        case_id=case.id,
        user_id=user.id,
        activity_type="email",
        title=f"E-mail opgesteld voor {recipient_label}",
        description=f"Onderwerp: {data.subject}{att_text}",
    )
    db.add(activity)
    await db.flush()

    # Return .eml file
    eml_bytes = msg.as_bytes()
    filename = f"email-{case.case_number}.eml"

    return Response(
        content=eml_bytes,
        media_type="message/rfc822",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post(
    "/cases/{case_id}/render-template",
    response_model=RenderTemplateResponse,
)
async def render_template_preview(
    case_id: uuid.UUID,
    data: RenderTemplateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Render an incasso template as HTML for email body preview."""
    # Verify case exists
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.tenant_id == user.tenant_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundError("Dossier niet gevonden")

    # Build context and render
    context = await build_base_context(db, user.tenant_id, case)
    html = render_incasso_email(data.template_type, context)

    if html is None:
        return RenderTemplateResponse(supported=False)

    return RenderTemplateResponse(
        supported=True,
        subject=f"{data.template_type.replace('_', ' ').title()} inzake dossier {case.case_number}",
        body_html=html,
    )
