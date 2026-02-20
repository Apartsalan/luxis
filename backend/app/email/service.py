"""Email service — async SMTP email sending with aiosmtplib.

Sends emails with optional file attachments (PDF/DOCX).
Configuration via SMTP_* environment variables in config.py.
"""

import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    """Check if SMTP is configured (host and from address set)."""
    return bool(settings.smtp_host) and bool(settings.smtp_from)


async def send_email(
    *,
    to: str,
    subject: str,
    html_body: str,
    cc: list[str] | None = None,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> None:
    """Send an email via SMTP.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        html_body: HTML content of the email body.
        cc: Optional list of CC email addresses.
        attachments: List of (filename, data, mime_subtype) tuples.
            Example: [("document.pdf", pdf_bytes, "pdf")]

    Raises:
        RuntimeError: If SMTP is not configured.
        aiosmtplib.SMTPException: On SMTP delivery failure.
    """
    if not is_configured():
        raise RuntimeError(
            "SMTP niet geconfigureerd. Stel SMTP_HOST en SMTP_FROM in."
        )

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    msg.set_content("Uw e-mailclient ondersteunt geen HTML.", subtype="plain")
    msg.add_alternative(html_body, subtype="html")

    if attachments:
        for filename, data, mime_subtype in attachments:
            msg.add_attachment(
                data,
                maintype="application",
                subtype=mime_subtype,
                filename=filename,
            )

    smtp_kwargs: dict = {
        "hostname": settings.smtp_host,
        "port": settings.smtp_port,
    }
    if settings.smtp_use_tls:
        smtp_kwargs["start_tls"] = True
    if settings.smtp_user:
        smtp_kwargs["username"] = settings.smtp_user
        smtp_kwargs["password"] = settings.smtp_pass

    await aiosmtplib.send(msg, **smtp_kwargs)

    logger.info(f"Email verzonden naar {to}: {subject}")
