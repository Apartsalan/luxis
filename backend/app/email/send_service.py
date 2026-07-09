"""Unified email send service — provider-first with SMTP fallback.

Centralises the send-with-attachment logic used by batch operations and
document sending. Handles logging (EmailLog, SyncedEmail, CaseActivity).
"""

import json
import logging
import uuid
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseActivity
from app.email.incasso_templates import is_branded, render_plain_branded
from app.email.models import EmailLog
from app.email.oauth_service import (
    get_email_account,
    get_provider,
    get_valid_access_token,
    imap_smtp_kwargs,
)
from app.email.providers.base import OutgoingAttachment
from app.email.service import send_email as smtp_send_email
from app.email.synced_email_models import SyncedEmail

logger = logging.getLogger(__name__)


async def build_branding_context(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case: Case | None = None,
) -> dict:
    """Context voor de huisstijl-aankleding (handtekening, disclaimer, Betreft).

    Mét dossier: de volledige briefcontext (zelfde als de sjablonen).
    Zonder dossier: een minimale context — de handtekening en het
    schuldhulpblok hebben alleen kantoorgegevens nodig.
    """
    from app.documents.docx_service import _tenant_ctx, build_base_context, load_tenant

    if case is not None:
        return await build_base_context(db, tenant_id, case)

    tenant = await load_tenant(db, tenant_id)
    return {
        "kantoor": _tenant_ctx(tenant),
        "wederpartij": {"naam": ""},
        "zaak": {"referentie_regel": "", "type": "incasso"},
        "vandaag": date.today().strftime("%d-%m-%Y"),
    }


async def ensure_branded_body(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    subject: str,
    body_html: str,
    case_id: uuid.UUID | None = None,
    quoted_html: str = "",
    force: bool = False,
) -> str:
    """Geef body_html terug in de huisstijl; al-aangeklede HTML blijft onaangeraakt.

    Afspraak S186: alles wat Luxis verstuurt draagt de sjabloon-opmaak
    (handtekening + logo + schuldhulpblok); alleen de tekst verschilt.

    `force=True` slaat de is_branded-detectie over — gebruikt op het compose-pad,
    waar een geciteerd antwoord zelf "Betreft:" kan bevatten en de detectie dus
    onbetrouwbaar is; de aanroeper weet daar zeker dat de tekst kaal is.
    """
    if not force and is_branded(body_html):
        return body_html

    case = None
    if case_id is not None:
        result = await db.execute(
            select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id)
        )
        case = result.scalar_one_or_none()

    ctx = await build_branding_context(db, tenant_id, case)
    return render_plain_branded(ctx, subject, body_html, quoted_html)


async def send_with_attachment(
    db: AsyncSession,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    *,
    to: str,
    subject: str,
    body_html: str,
    attachments: list[tuple[str, bytes, str]],  # (filename, data, mime_subtype)
    cc: list[str] | None = None,
    case_id: uuid.UUID | None = None,
    document_id: uuid.UUID | None = None,
    recipient_name: str = "",
    sender_name: str = "",
) -> EmailLog:
    """Send an email with attachments via provider (preferred) or SMTP fallback.

    Tries the connected email provider first (Gmail/Outlook). If no provider
    is connected, falls back to SMTP. Logs everything to EmailLog and
    optionally SyncedEmail (for provider sends).

    Args:
        db: Database session.
        user_id: The user sending the email.
        tenant_id: Tenant scope.
        to: Recipient email address.
        subject: Email subject.
        body_html: HTML body content.
        attachments: List of (filename, bytes, mime_subtype) tuples.
        case_id: Optional case reference for logging.
        document_id: Optional document reference for logging.
        recipient_name: Display name of recipient (for activity log).
        sender_name: Display name of sender (for SyncedEmail).

    Returns:
        The EmailLog record (check .status for "sent" or "failed").
    """
    # Huisstijl: kale tekst (facturen, opvolging, AI-agent) krijgt de sjabloon-
    # opmaak (handtekening + logo + schuldhulpblok). Al-opgemaakte HTML (incasso-
    # stappen, documentmails) wordt herkend door is_branded en niet aangeraakt.
    body_html = await ensure_branded_body(
        db, tenant_id, subject=subject, body_html=body_html, case_id=case_id
    )

    account = await get_email_account(db, user_id, tenant_id)

    email_log = EmailLog(
        tenant_id=tenant_id,
        case_id=case_id,
        document_id=document_id,
        template="batch_document_send",
        recipient=to,
        subject=subject,
        status="sent",
    )

    provider_message_id: str | None = None
    used_provider = False

    if account:
        # Provider path — email appears in Sent folder
        try:
            provider = get_provider(account.provider)
            access_token = await get_valid_access_token(db, account)

            outgoing_attachments = [
                OutgoingAttachment(
                    filename=fname,
                    data=data,
                    content_type=f"application/{mime_sub}",
                )
                for fname, data, mime_sub in attachments
            ]

            from app.auth.models import Tenant

            from_name = (
                await db.execute(select(Tenant.name).where(Tenant.id == tenant_id))
            ).scalar() or ""

            provider_message_id = await provider.send_message(
                access_token,
                to=[to],
                subject=subject,
                body_html=body_html,
                cc=cc,
                attachments=outgoing_attachments,
                from_name=from_name,
                **imap_smtp_kwargs(account),
            )
            used_provider = True
            logger.info(
                "Email met bijlage verzonden via %s naar %s",
                account.provider,
                to,
            )
        except Exception as e:
            email_log.status = "failed"
            email_log.error_message = f"Provider ({account.provider}): {e}"
            logger.error("Email via provider mislukt naar %s: %s", to, e)
    else:
        # SMTP fallback — email does NOT appear in email client's Sent folder
        try:
            await smtp_send_email(
                to=to,
                subject=subject,
                html_body=body_html,
                cc=cc,
                attachments=attachments,
            )
            logger.info("Email met bijlage verzonden via SMTP naar %s", to)
        except Exception as e:
            email_log.status = "failed"
            email_log.error_message = f"SMTP: {e}"
            logger.error("Email via SMTP mislukt naar %s: %s", to, e)

    db.add(email_log)
    await db.flush()
    await db.refresh(email_log)

    # Create SyncedEmail record for provider sends (shows in correspondentie tab)
    if used_provider and provider_message_id and email_log.status == "sent":
        synced = SyncedEmail(
            tenant_id=tenant_id,
            email_account_id=account.id,
            case_id=case_id,
            provider_message_id=provider_message_id,
            subject=subject,
            from_email=account.email_address,
            from_name=sender_name,
            to_emails=json.dumps([to]),
            cc_emails=json.dumps(cc or []),
            snippet=subject[:200],
            body_text="",
            body_html=body_html,
            direction="outbound",
            is_read=True,
            has_attachments=bool(attachments),
            matched_by="outbound_send",
            email_date=datetime.now(UTC),
            synced_at=datetime.now(UTC),
        )
        db.add(synced)

    # Log case activity
    if case_id and email_log.status == "sent":
        label = recipient_name or to
        method = account.provider if used_provider else "SMTP"
        activity = CaseActivity(
            tenant_id=tenant_id,
            case_id=case_id,
            user_id=user_id,
            activity_type="email",
            title=f"E-mail verzonden naar {label}",
            description=f"Onderwerp: {subject} (via {method})",
        )
        db.add(activity)

    await db.flush()
    return email_log
