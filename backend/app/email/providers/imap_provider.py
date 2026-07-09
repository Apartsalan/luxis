"""ImapProvider — fetches email via IMAP (e.g. BaseNet).

Temporary bridge until MX records point to M365.
Uses stdlib imaplib + asyncio.to_thread() for async compatibility.
"""

import asyncio
import email as email_lib
import imaplib
import logging
import re
from datetime import UTC, datetime, timedelta
from email.header import decode_header
from email.utils import formataddr, parseaddr, parsedate_to_datetime
from html import unescape as _html_unescape

from app.email.providers.base import (
    AttachmentInfo,
    EmailMessage,
    EmailProvider,
    OAuthTokens,
    OutgoingAttachment,
)

logger = logging.getLogger(__name__)

# Verzonden-map: BaseNet gebruikt "INBOX.Sent"; andere IMAP-servers variëren.
# Eén bron van waarheid zodat ophalen, opslaan en listen dezelfde volgorde
# aanhouden (voorheen stond de volgorde op 3 plekken verschillend).
SENT_FOLDER_CANDIDATES = ("INBOX.Sent", "Sent", "Sent Items", "Verzonden items")


def _imap_quote(value: str) -> str:
    """Escape een string voor een IMAP quoted-string (RFC 3501 §4.3).

    Beschermt de HEADER-zoekopdracht tegen een Message-ID met een " of \\ erin,
    én tegen regeleinde-tekens (een 'gevouwen' Message-ID-header kan CR/LF
    bevatten — rauw doorgegeven zou dat een eigen IMAP-commando injecteren).
    De waarde staat in de mail en is dus door de afzender te beïnvloeden.
    """
    value = re.sub(r"[\r\n\x00]", " ", value)
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _html_to_text(html: str) -> str:
    """Platte-tekstversie van een HTML-body voor het text/plain-alternatief.

    Zonder dit viel elke uitgaande mail terug op één placeholder-zin — dat is
    wat tekst-only clients tonen, wat in maillijst-previews verschijnt, en wat
    spamfilters negatief meewegen (geen echte tekstvariant).
    """
    if not html:
        return ""
    # Structuur-einde → nieuwe regel, vóór het strippen van de tags.
    text = re.sub(r"(?i)<\s*br\s*/?>", "\n", html)
    text = re.sub(r"(?i)</\s*(?:p|div|tr|li|h[1-6])\s*>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = _html_unescape(text)
    lines = [ln.strip() for ln in text.splitlines()]
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return out or "(deze e-mail heeft alleen opgemaakte inhoud)"


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
    is_read: bool = True,
) -> EmailMessage | None:
    """Parse raw IMAP message bytes into an EmailMessage.

    is_read weerspiegelt de IMAP \\Seen-vlag (meegelezen in dezelfde fetch);
    default True voor plekken die de vlag niet opvragen (bv. losse bijlage-fetch).
    """
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

    # Stabiele conversatie-id = de WORTEL van de keten (oudste Message-ID in
    # References), zodat elke reply — hoe diep ook — dezelfde thread_id deelt.
    # Zonder References: het directe antwoord (In-Reply-To) of, voor de eerste
    # mail zelf, de eigen Message-ID (dan matchen latere replies erop terug).
    # (Fout vóór S186: In-Reply-To kreeg voorrang → elke laag een andere id →
    # keten brak na één antwoord.)
    references = msg.get("References", "")
    in_reply_to = msg.get("In-Reply-To", "")
    ref_parts = references.split()
    if ref_parts:
        thread_id = ref_parts[0]
    elif in_reply_to.strip():
        thread_id = in_reply_to.strip()
    else:
        thread_id = message_id

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
        is_read=is_read,  # IMAP \Seen-vlag, meegelezen in dezelfde fetch
        has_attachments=len(attachments) > 0,
        attachments=attachments,
    )


def _seen_flag_present(msg_data) -> bool:
    """True als de IMAP \\Seen-vlag in de fetch-descriptor staat.

    Bij een fetch met FLAGS zit de vlaggenlijst in het beschrijvende deel
    (bv. b'1 (FLAGS (\\Seen) RFC822 {1234}'), niet in de ruwe body. We kijken
    daarom alleen naar dat descriptor-deel, nooit naar de body-inhoud.
    """
    for part in msg_data:
        descriptor = part[0] if isinstance(part, tuple) else part
        if isinstance(descriptor, bytes) and b"\\Seen" in descriptor:
            return True
    return False


def _fetch_from_imap(
    host: str,
    port: int,
    username: str,
    password: str,
    max_results: int,
    since_days: int = 90,
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
            # FLAGS meevragen zodat we de echte gelezen-status (\Seen) weten.
            # readonly select → het lezen zet zélf geen \Seen (blijft ongewijzigd).
            status, msg_data = imap.fetch(uid, "(FLAGS RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue

            raw_bytes = msg_data[0][1]
            if not isinstance(raw_bytes, bytes):
                continue

            is_read = _seen_flag_present(msg_data)
            email_msg = _imap_message_to_email(uid.decode(), raw_bytes, is_read=is_read)
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
        # Try multiple folders to find the message (INBOX first, dan de Verzonden-
        # mappen). Deduplicate while preserving order.
        folders_to_try = [folder, "INBOX", *SENT_FOLDER_CANDIDATES]
        seen = set()
        unique_folders = []
        for f in folders_to_try:
            if f not in seen:
                seen.add(f)
                unique_folders.append(f)

        safe_message_id = _imap_quote(message_id)
        raw_bytes = None
        for try_folder in unique_folders:
            try:
                status, _ = imap.select(try_folder, readonly=True)
                if status != "OK":
                    continue
                status, data = imap.search(None, f'(HEADER Message-ID "{safe_message_id}")')
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


def _append_to_sent(
    host: str,
    port: int,
    username: str,
    password: str,
    raw_message: bytes,
) -> None:
    """Zet een verzonden mail in de Verzonden-map via IMAP APPEND.

    BaseNet bewaart SMTP-verzonden mail niet zelf (gemeten S186); zonder deze
    APPEND ziet de gebruiker verzonden mail niet terug in de mailbox.
    Probeert de gangbare mapnamen; de eerste die bestaat wint.
    """
    import imaplib as _imaplib
    import time as _time

    imap = _imaplib.IMAP4_SSL(host, port)
    imap.login(username, password)
    try:
        for folder in SENT_FOLDER_CANDIDATES:
            status, _ = imap.select(folder, readonly=True)
            if status != "OK":
                continue
            imap.close()
            status, _ = imap.append(
                folder, r"(\Seen)", _imaplib.Time2Internaldate(_time.time()), raw_message
            )
            if status == "OK":
                logger.info("IMAP: kopie opgeslagen in '%s' voor %s", folder, username)
                return
        raise ValueError("Geen Verzonden-map gevonden om de kopie in op te slaan")
    finally:
        try:
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
        for sent_folder in SENT_FOLDER_CANDIDATES:
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
        access_token: str,  # For IMAP: this is the password
        *,
        to: list[str],
        subject: str,
        body_html: str,
        cc: list[str] | None = None,
        reply_to_message_id: str | None = None,
        references_root: str | None = None,
        attachments: list[OutgoingAttachment] | None = None,
        from_name: str = "",
        smtp_host: str = "",
        smtp_port: int = 587,
        username: str = "",
    ) -> str:
        """Send an email via the account's outgoing SMTP server (e.g. BaseNet).

        Spiegelbeeld van de IMAP-ontvangst: dezelfde inlog, maar dan via de
        uitgaande server. De afzender is `username` (incasso@...). Na het
        versturen wordt de mail zelf via IMAP APPEND in de Verzonden-map
        gezet — BaseNet doet dat NIET automatisch bij SMTP (gemeten S186).
        Retourneert de Message-ID die we zelf zetten, zodat de latere sync de
        Sent-kopie hierop dedupliceert.
        """
        from email.message import EmailMessage as MimeMessage
        from email.utils import formatdate, make_msgid

        import aiosmtplib

        from app.email.service import check_outbound_lock

        check_outbound_lock()
        if not smtp_host or not username:
            raise ValueError("IMAP-verzending vereist smtp_host en username")

        msg = MimeMessage()
        # Afzender met weergavenaam ("Kesting Legal <incasso@...>") als die er is,
        # anders het kale adres.
        msg["From"] = formataddr((from_name, username)) if from_name else username
        msg["To"] = ", ".join(to)
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        message_id = make_msgid(domain=username.split("@")[-1])
        msg["Message-ID"] = message_id
        # Thread-headers: laat een antwoord bij de originele mail horen.
        # In-Reply-To = de directe voorganger; References begint bij de WORTEL
        # van de keten (zodat de latere sync dit antwoord op dezelfde thread_id
        # groepeert als de rest van het gesprek — óók bij een antwoord op een
        # mail middenin een lange draad). We bewaren de volledige References van
        # het origineel niet, dus wortel + directe voorganger is het maximum;
        # dat volstaat voor de thread-groepering (die kijkt naar References[0]).
        # ponytail: root+parent, niet de hele keten — genoeg voor onze matching.
        if reply_to_message_id:
            msg["In-Reply-To"] = reply_to_message_id
            if references_root and references_root != reply_to_message_id:
                msg["References"] = f"{references_root} {reply_to_message_id}"
            else:
                msg["References"] = reply_to_message_id
        msg.set_content(_html_to_text(body_html))
        msg.add_alternative(body_html, subtype="html")

        for att in attachments or []:
            maintype, _, subtype = att.content_type.partition("/")
            if not subtype:
                maintype, subtype = "application", "octet-stream"
            msg.add_attachment(
                att.data, maintype=maintype, subtype=subtype, filename=att.filename
            )

        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            start_tls=True,
            username=username,
            password=access_token,
        )
        logger.info(
            "IMAP/SMTP: e-mail verzonden als %s naar %s via %s:%d",
            username,
            to,
            smtp_host,
            smtp_port,
        )

        # Kopie naar de Verzonden-map (IMAP APPEND). Mag nooit de verzending
        # laten falen — de mail is al onderweg; loggen en doorgaan.
        imap_host = "imap." + smtp_host[len("smtp.") :] if smtp_host.startswith("smtp.") else smtp_host
        try:
            await asyncio.to_thread(
                _append_to_sent, imap_host, 993, username, access_token, msg.as_bytes()
            )
        except Exception as e:
            logger.warning("IMAP: kopie naar Verzonden-map mislukt (mail is wel verzonden): %s", e)

        return message_id

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
