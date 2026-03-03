"""Unified email send service — provider-first with SMTP fallback.

Centralises the send-with-attachment logic used by batch operations and
document sending. Handles logging (EmailLog, SyncedEmail, CaseActivity).
"""

import json
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import CaseActivity
from app.email.models import EmailLog
from app.email.oauth_service import get_email_account, get_provider, get_valid_access_token
from app.email.providers.base import OutgoingAttachment
from app.email.service import send_email as smtp_send_email
from app.email.synced_email_models import SyncedEmail

logger = logging.getLogger(__name__)


async def send_with_attachment(
    db: AsyncSession,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    *,
    to: str,
    subject: str,
    body_html: str,
    attachments: list[tuple[str, bytes, str]],  # (filename, data, mime_subtype)
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

            provider_message_id = await provider.send_message(
                access_token,
                to=[to],
                subject=subject,
                body_html=body_html,
                attachments=outgoing_attachments,
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
            cc_emails=json.dumps([]),
            snippet=subject[:200],
            body_text="",
            body_html=body_html,
            direction="outbound",
            is_read=True,
            has_attachments=bool(attachments),
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
