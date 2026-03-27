"""ImapProvider — fetches email via IMAP (e.g. BaseNet).

Temporary bridge until MX records point to M365.
Uses stdlib imaplib + asyncio.to_thread() for async compatibility.
"""

import asyncio
import email as email_lib
import imaplib
import logging
from datetime import UTC, datetime, timedelta
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime

from app.email.providers.base import (
    AttachmentInfo,
    EmailMessage,
    EmailProvider,
    OAuthTokens,
    OutgoingAttachment,
)

logger = logging.getLogger(__name__)


def _decode_header_value(value: str | None) -> str:
    """Decode an RFC 2047 encoded header value."""
    if not value:
        return ""
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _parse_address(addr_str: str | None) -> tuple[str, str]:
    """Parse 'Name <email>' into (name, email)."""
    if not addr_str:
        return ("", "")
    decoded = _decode_header_value(addr_str)
    name, email_addr = parseaddr(decoded)
    return (name, email_addr.lower())


def _parse_address_list(addr_str: str | None) -> list[str]:
    """Parse a comma-separated address list into a list of email addresses."""
    if not addr_str:
        return []
    decoded = _decode_header_value(addr_str)
    # Split on comma, parse each
    addresses = []
    for part in decoded.split(","):
        _, email_addr = parseaddr(part.strip())
        if email_addr:
            addresses.append(email_addr.lower())
    return addresses


def _get_text_parts(msg: email_lib.message.Message) -> tuple[str, str]:
    """Extract plain text and HTML body from an email message."""
    text_body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in disposition:
                continue

            try:
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="replace")
            except Exception:
                continue

            if content_type == "text/plain" and not text_body:
                text_body = decoded
            elif content_type == "text/html" and not html_body:
                html_body = decoded
    else:
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="replace")
                if content_type == "text/plain":
                    text_body = decoded
                elif content_type == "text/html":
                    html_body = decoded
        except Exception:
            pass

    return text_body, html_body


def _get_attachments(msg: email_lib.message.Message) -> list[AttachmentInfo]:
    """Extract attachment metadata from an email message."""
    attachments = []
    if not msg.is_multipart():
        return attachments

    for i, part in enumerate(msg.walk()):
        disposition = str(part.get("Content-Disposition", ""))
        content_type = part.get_content_type()

        # Skip non-attachment parts
        if "attachment" not in disposition and "inline" not in disposition:
            continue
        # Skip inline text/html parts (not real attachments)
        if content_type in ("text/plain", "text/html") and "inline" in disposition:
            continue

        filename = part.get_filename()
        if filename:
            filename = _decode_header_value(filename)
        else:
            filename = f"attachment_{i}"

        size = len(part.get_payload(decode=True) or b"")

        attachments.append(
            AttachmentInfo(
                attachment_id=str(i),  # Part index as ID
                filename=filename,
                content_type=content_type,
                size=size,
                part_id=str(i),
            )
        )

    return attachments


def _imap_message_to_email(
    uid: str,
    raw_bytes: bytes,
) -> EmailMessage | None:
    """Parse raw IMAP message bytes into an EmailMessage."""
    try:
        msg = email_lib.message_from_bytes(raw_bytes)
    except Exception as e:
        logger.error(f"Failed to parse IMAP message UID {uid}: {e}")
        return None

    # Message-ID as provider_message_id
    message_id = msg.get("Message-ID", "").strip()
    if not message_id:
        message_id = f"imap-uid-{uid}"

    # Parse headers
    from_name, from_email = _parse_address(msg.get("From"))
    to_emails = _parse_address_list(msg.get("To"))
    cc_emails = _parse_address_list(msg.get("Cc"))
    subject = _decode_header_value(msg.get("Subject"))

    # Parse date
    date_str = msg.get("Date", "")
    try:
        dt = parsedate_to_datetime(date_str)
        date_iso = dt.isoformat()
    except Exception:
        date_iso = datetime.now(UTC).isoformat()

    # Thread ID from References/In-Reply-To
    references = msg.get("References", "")
    in_reply_to = msg.get("In-Reply-To", "")
    thread_id = in_reply_to.strip() or (references.split()[0] if references else None)

    # Body
    text_body, html_body = _get_text_parts(msg)
    snippet = (text_body or "")[:200]

    # Attachments
    attachments = _get_attachments(msg)

    return EmailMessage(
        provider_message_id=message_id,
        thread_id=thread_id,
        subject=subject,
        from_email=from_email,
        from_name=from_name,
        to_emails=to_emails,
        cc_emails=cc_emails,
        date=date_iso,
        snippet=snippet,
        body_text=text_body,
        body_html=html_body,
        is_read=True,  # IMAP doesn't easily expose this in bulk fetch
        has_attachments=len(attachments) > 0,
        attachments=attachments,
    )


def _fetch_from_imap(
    host: str,
    port: int,
    username: str,
    password: str,
    max_results: int,
    since_days: int = 14,
    folder: str = "INBOX",
) -> list[EmailMessage]:
    """Synchronous IMAP fetch — runs in asyncio.to_thread()."""
    messages = []

    try:
        imap = imaplib.IMAP4_SSL(host, port)
        imap.login(username, password)
    except Exception as e:
        logger.error(f"IMAP login failed for {username}@{host}:{port}: {e}")
        raise

    try:
        status, _ = imap.select(folder, readonly=True)
        if status != "OK":
            logger.warning(f"IMAP SELECT {folder} failed: {status}")
            return messages

        # Search for recent messages
        since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
        status, data = imap.search(None, f"(SINCE {since_date})")
        if status != "OK" or not data[0]:
            return messages

        uids = data[0].split()
        # Take newest N messages
        uids = uids[-max_results:]

        for uid in uids:
            status, msg_data = imap.fetch(uid, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue

            raw_bytes = msg_data[0][1]
            if not isinstance(raw_bytes, bytes):
                continue

            email_msg = _imap_message_to_email(uid.decode(), raw_bytes)
            if email_msg:
                messages.append(email_msg)

    finally:
        try:
            imap.close()
            imap.logout()
        except Exception:
            pass

    return messages


def _fetch_attachment_from_imap(
    host: str,
    port: int,
    username: str,
    password: str,
    message_id: str,
    attachment_idx: int,
    folder: str = "INBOX",
) -> bytes:
    """Fetch a specific attachment from IMAP by searching for Message-ID.

    Tries multiple folders (INBOX, Sent) to find the message.
    """
    try:
        imap = imaplib.IMAP4_SSL(host, port)
        imap.login(username, password)
    except Exception as e:
        logger.error(f"IMAP login failed: {e}")
        raise

    try:
        # Try multiple folders to find the message
        folders_to_try = [folder, "INBOX.Sent", "INBOX"]
        # Deduplicate while preserving order
        seen = set()
        unique_folders = []
        for f in folders_to_try:
            if f not in seen:
                seen.add(f)
                unique_folders.append(f)

        raw_bytes = None
        for try_folder in unique_folders:
            try:
                status, _ = imap.select(try_folder, readonly=True)
                if status != "OK":
                    continue
                status, data = imap.search(None, f'(HEADER Message-ID "{message_id}")')
                if status != "OK" or not data[0]:
                    continue
                uid = data[0].split()[0]
                status, msg_data = imap.fetch(uid, "(RFC822)")
                if status == "OK" and msg_data and msg_data[0]:
                    raw_bytes = msg_data[0][1]
                    break
            except Exception:
                continue

        if not raw_bytes:
            raise ValueError(f"Message not found: {message_id}")

        msg = email_lib.message_from_bytes(raw_bytes)

        # Walk to find the right part by walk-index (matches _get_attachments)
        for i, part in enumerate(msg.walk()):
            if i == attachment_idx:
                return part.get_payload(decode=True) or b""

        raise ValueError(f"Attachment walk-index {attachment_idx} not found")

    finally:
        try:
            imap.close()
            imap.logout()
        except Exception:
            pass


class ImapProvider(EmailProvider):
    """IMAP email provider for BaseNet and similar IMAP servers.

    Credentials are stored in the EmailAccount model:
    - access_token_enc: encrypted IMAP password
    - scopes: "host:port" (e.g. "imap.basenet.nl:993")
    - email_address: IMAP username (usually the email address)
    """

    def _parse_host_port(self, host_port: str) -> tuple[str, int]:
        """Parse 'host:port' string."""
        parts = host_port.split(":")
        return parts[0], int(parts[1]) if len(parts) > 1 else 993

    # --- OAuth methods: not applicable for IMAP ---

    def get_authorize_url(self, state: str) -> str:
        raise NotImplementedError("IMAP does not use OAuth")

    async def exchange_code(self, code: str) -> OAuthTokens:
        raise NotImplementedError("IMAP does not use OAuth")

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        raise NotImplementedError("IMAP does not use OAuth")

    async def get_user_email(self, access_token: str) -> str:
        raise NotImplementedError("IMAP does not use OAuth")

    # --- Email operations ---

    async def list_messages(
        self,
        access_token: str,  # For IMAP: this is the password
        *,
        max_results: int = 50,
        page_token: str | None = None,
        query: str | None = None,
        host: str = "",
        port: int = 993,
        username: str = "",
    ) -> tuple[list[EmailMessage], str | None]:
        """Fetch messages from IMAP server.

        For IMAP, access_token contains the password.
        Host/port/username must be passed as kwargs.
        """
        all_messages = []

        # Fetch from INBOX
        inbox_msgs = await asyncio.to_thread(
            _fetch_from_imap,
            host,
            port,
            username,
            access_token,
            max_results,
        )
        all_messages.extend(inbox_msgs)

        # Also fetch from Sent Items (try common folder names)
        for sent_folder in ("Sent", "Sent Items", "Verzonden items", "INBOX.Sent"):
            try:
                sent_msgs = await asyncio.to_thread(
                    _fetch_from_imap,
                    host,
                    port,
                    username,
                    access_token,
                    max_results,
                    folder=sent_folder,
                )
                all_messages.extend(sent_msgs)
                if sent_msgs:
                    logger.info(f"IMAP: {len(sent_msgs)} berichten uit '{sent_folder}'")
                    break  # Found the right sent folder
            except Exception:
                continue  # Folder doesn't exist, try next

        # Deduplicate by Message-ID (in case same message appears in multiple folders)
        seen = set()
        unique = []
        for m in all_messages:
            if m.provider_message_id not in seen:
                seen.add(m.provider_message_id)
                unique.append(m)

        # Sort by date descending
        unique.sort(key=lambda m: m.date, reverse=True)

        return unique[:max_results], None

    async def get_message(self, access_token: str, message_id: str) -> EmailMessage:
        raise NotImplementedError("IMAP get_message not implemented")

    async def send_message(
        self,
        access_token: str,
        *,
        to: list[str],
        subject: str,
        body_html: str,
        cc: list[str] | None = None,
        reply_to_message_id: str | None = None,
        attachments: list[OutgoingAttachment] | None = None,
    ) -> str:
        raise NotImplementedError("Use OutlookProvider for sending via Graph API")

    async def create_draft(
        self,
        access_token: str,
        *,
        to: list[str],
        subject: str,
        body_html: str,
        cc: list[str] | None = None,
    ) -> str:
        raise NotImplementedError("Use OutlookProvider for drafts via Graph API")

    async def get_attachment(
        self,
        access_token: str,  # IMAP password
        message_id: str,
        attachment_id: str,
        *,
        host: str = "",
        port: int = 993,
        username: str = "",
    ) -> bytes:
        """Download an attachment from IMAP."""
        return await asyncio.to_thread(
            _fetch_attachment_from_imap,
            host,
            port,
            username,
            access_token,
            message_id,
            int(attachment_id),
        )
