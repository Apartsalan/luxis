"""Email service — async SMTP email sending with aiosmtplib.

Sends emails with optional file attachments (PDF/DOCX).
Configuration via SMTP_* environment variables in config.py.
"""

import logging
from email.message import EmailMessage

import aiosmtplib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory stand van het schakelbare DB-mailslot. Wordt bij het opstarten uit de
# DB geladen (app.main.lifespan) vóór er ook maar één request wordt bediend, en
# bijgewerkt bij elke toggle. De backend draait één proces, dus deze
# module-waarde is consistent voor de web-handlers én de scheduler die 'm lezen.
# Default False alleen relevant in tests (die draaien lifespan niet); in productie
# zet load_mail_lock 'm altijd vóór het bedienen van requests, en fail-safe DICHT
# bij twijfel (zie load_mail_lock).
_db_mail_locked: bool = False


def is_configured() -> bool:
    """Check if SMTP is configured (host and from address set)."""
    return bool(settings.smtp_host) and bool(settings.smtp_from)


def db_mail_locked() -> bool:
    """De UI-schakelbare mailslot-stand (los van het env-noodslot)."""
    return _db_mail_locked


def is_mail_locked() -> bool:
    """Effectief slot: env-noodslot (harde override) OF de UI-schakelbare DB-vlag."""
    return bool(settings.outbound_mail_lock) or _db_mail_locked


def check_outbound_lock() -> None:
    """Bouwfase-mailslot: blokkeer álle uitgaande mail zolang het slot aan staat.

    Aangevraagd 9 juli 2026 (Arsalan). Sinds S197 zit het slot in de DB en is het
    vanuit Instellingen te schakelen; het env-noodslot (OUTBOUND_MAIL_LOCK) blijft
    als harde override erboven — staat dat aan, dan kan de knop niet openen.
    """
    if is_mail_locked():
        raise RuntimeError(
            "Mailverzending staat op slot (bouwfase). Zet het mailslot open in "
            "Instellingen om weer te kunnen versturen."
        )


async def load_mail_lock(db: AsyncSession) -> bool:
    """Laad de persistente mailslot-stand in het geheugen. Fail-safe: als de rij
    ontbreekt of de DB onleesbaar is -> op slot (True), zodat er nooit per ongeluk
    mail uit gaat wanneer het env-noodslot eraf is."""
    global _db_mail_locked
    from app.settings.models import AppConfig

    try:
        row = (await db.execute(select(AppConfig).limit(1))).scalar_one_or_none()
        _db_mail_locked = bool(row.outbound_mail_locked) if row is not None else True
    except Exception:
        _db_mail_locked = True
        raise
    return _db_mail_locked


async def set_mail_lock(db: AsyncSession, locked: bool) -> bool:
    """Zet de mailslot-stand: persisteer in de DB én werk het geheugen bij.

    S202 L5: commit hier zelf i.p.v. te vertrouwen op de latere request-commit
    (`get_db`). Het geheugen wordt pas bijgewerkt NA een geslaagde commit — zo
    kan een mislukte commit het geheugen niet open laten terwijl de DB nog dicht
    staat (de oude volgorde deed `flush()` + geheugen-update vóór de commit).
    """
    global _db_mail_locked
    from app.settings.models import AppConfig

    row = (await db.execute(select(AppConfig).limit(1))).scalar_one_or_none()
    if row is None:
        row = AppConfig(outbound_mail_locked=locked)
        db.add(row)
    else:
        row.outbound_mail_locked = locked
    await db.commit()
    _db_mail_locked = bool(locked)
    return _db_mail_locked


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
    check_outbound_lock()
    if not is_configured():
        raise RuntimeError("SMTP niet geconfigureerd. Stel SMTP_HOST en SMTP_FROM in.")

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
