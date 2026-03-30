"""Email sync service — fetches emails from provider, matches to dossiers.

Matching logic (in priority order):
  1. Thread match: same provider_thread_id as an already-linked email
  2. System/bounce email: auto-dismiss, link only via thread or case number
  3. Case number match: scan SUBJECT for patterns like "2026-00012"
     If a case number is found but the dossier doesn't exist → STOP (don't fallthrough)
  4. Contact email match: look up email addresses → Contact → Case
  5. If exactly one case matches, auto-link
  6. If multiple cases match, leave unlinked (user assigns via "ongesorteerd" queue)
"""

import json
import logging
import re
import uuid
from datetime import UTC, datetime
from html import unescape as html_unescape
from pathlib import Path

from dateutil import parser as dateparser
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseParty
from app.email.attachment_models import EmailAttachment
from app.email.oauth_models import EmailAccount
from app.email.oauth_service import get_provider, get_valid_access_token
from app.email.providers.base import EmailMessage
from app.email.synced_email_models import SyncedEmail
from app.email.token_encryption import decrypt_token
from app.relations.models import Contact

# Base directory for email attachment storage
EMAIL_ATTACHMENTS_BASE = Path("/app/uploads/email_attachments")

logger = logging.getLogger(__name__)

# Regex: matches case numbers like "2024-00001", "2026-12345"
CASE_NUMBER_RE = re.compile(r"\b(20\d{2}-\d{4,6})\b")

# Simple HTML tag stripper — faster than BeautifulSoup for our needs
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(html: str) -> str:
    """Strip HTML tags and decode entities to plain text."""
    if not html:
        return ""
    text = _HTML_TAG_RE.sub(" ", html)
    text = html_unescape(text)
    # Collapse whitespace
    return re.sub(r"\s+", " ", text).strip()


def _build_searchable_text(
    subject: str | None,
    body_text: str | None,
    body_html: str | None,
    snippet: str | None,
) -> str:
    """Build full searchable text from email fields.

    Many emails only have HTML body (no text/plain part), so we strip
    HTML tags to get searchable plain text from body_html as well.
    """
    parts = [subject or ""]
    if body_text:
        parts.append(body_text)
    if body_html:
        parts.append(_strip_html(body_html))
    if snippet:
        parts.append(snippet)
    return " ".join(parts)


async def _find_case_by_case_number(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    subject: str,
) -> tuple[uuid.UUID | None, str | None, bool]:
    """Scan subject for case numbers like "2026-00012".

    Returns (case_id, matched_by, has_case_number):
      - (uuid, "case_number", True) — matched to an active case
      - (None, None, True)          — case number found but dossier doesn't exist
      - (None, None, False)         — no case number found in text
    """
    if not subject:
        return None, None, False

    matches = CASE_NUMBER_RE.findall(subject)
    if not matches:
        return None, None, False

    # Case number found in subject — look up in DB
    result = await db.execute(
        select(Case.id).where(
            Case.tenant_id == tenant_id,
            Case.is_active == True,  # noqa: E712
            Case.case_number.in_(matches),
        )
    )
    case_ids = {row[0] for row in result.all()}

    if len(case_ids) == 1:
        return case_ids.pop(), "case_number", True

    if len(case_ids) > 1:
        logger.info(
            "Meerdere dossiers (%d) gematcht op dossiernummer %s — niet auto-gekoppeld",
            len(case_ids),
            matches,
        )
        return None, None, True

    # Case number found in text but no active dossier exists
    logger.info(
        "Dossiernummer %s gevonden in email maar dossier bestaat niet"
        " — niet doorvallen naar contact-matching",
        matches,
    )
    return None, None, True


async def _find_case_by_thread(
    db: AsyncSession,
    account_id: uuid.UUID,
    thread_id: str | None,
) -> uuid.UUID | None:
    """Find a case via an already-linked email in the same thread."""
    if not thread_id:
        return None
    result = await db.execute(
        select(SyncedEmail.case_id)
        .where(
            SyncedEmail.email_account_id == account_id,
            SyncedEmail.provider_thread_id == thread_id,
            SyncedEmail.case_id.isnot(None),
        )
        .order_by(SyncedEmail.email_date.desc())
        .limit(1)
    )
    row = result.first()
    return row[0] if row else None


# ── Bounce / system email detection ──────────────────────────────────────────

_BOUNCE_FROM_LOCALS = {
    "mailer-daemon",
    "postmaster",
    "mail-daemon",
    "noreply",
    "no-reply",
    "auto-reply",
    "autoreply",
}

_BOUNCE_SUBJECT_RE = re.compile(
    r"(undeliverable|delivery.{0,10}fail|returned.{0,5}mail|"
    r"niet.{0,5}bezorg|onbestelbaar|failure.{0,5}notice|"
    r"delivery.{0,5}status|auto.{0,3}reply|automatisch.{0,5}antwoord|"
    r"out.{0,3}of.{0,3}office|afwezig)",
    re.IGNORECASE,
)


def _is_system_email(msg: EmailMessage) -> bool:
    """Detect bounce/NDR/auto-reply/system emails."""
    from_email = (msg.from_email or "").lower()
    from_local = from_email.split("@")[0] if from_email else ""
    from_name = (msg.from_name or "").lower()
    subject = msg.subject or ""

    # Known bounce senders
    if from_local in _BOUNCE_FROM_LOCALS:
        return True

    # Microsoft Exchange bounce format
    if "microsoftexchange" in from_email.replace("-", "").replace("_", ""):
        return True

    # Microsoft system notifications
    if from_name in ("microsoft", "microsoft outlook", "microsoft 365"):
        return True

    # Bounce/auto-reply subject patterns
    if _BOUNCE_SUBJECT_RE.search(subject):
        return True

    return False


async def _find_case_for_email(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email_addresses: list[str],
) -> uuid.UUID | None:
    """Try to find a single case that matches the email addresses.

    Returns case_id if exactly one active case is found, otherwise None.
    """
    if not email_addresses:
        return None

    # Step 1: Find contacts matching any of the email addresses
    result = await db.execute(
        select(Contact.id).where(
            Contact.tenant_id == tenant_id,
            Contact.email.in_(email_addresses),
            Contact.is_active == True,  # noqa: E712
        )
    )
    contact_ids = [row[0] for row in result.all()]
    if not contact_ids:
        return None

    # Step 2: Find cases where any contact is client, opposing party, or case party
    case_ids = set()

    # Direct case links (client, opposing_party)
    result = await db.execute(
        select(Case.id).where(
            Case.tenant_id == tenant_id,
            Case.is_active == True,  # noqa: E712
            or_(
                Case.client_id.in_(contact_ids),
                Case.opposing_party_id.in_(contact_ids),
            ),
        )
    )
    for row in result.all():
        case_ids.add(row[0])

    # Case party links
    result = await db.execute(
        select(CaseParty.case_id).where(
            CaseParty.tenant_id == tenant_id,
            CaseParty.contact_id.in_(contact_ids),
        )
    )
    for row in result.all():
        case_ids.add(row[0])

    # Only auto-link if exactly one case matches
    if len(case_ids) == 1:
        return case_ids.pop()

    if len(case_ids) > 1:
        logger.info(
            "Meerdere dossiers (%d) gevonden voor %s — niet auto-gekoppeld",
            len(case_ids),
            email_addresses,
        )

    return None


def _parse_email_date(date_str: str) -> datetime:
    """Parse an email date string into a timezone-aware datetime."""
    try:
        dt = dateparser.parse(date_str)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt or datetime.now(UTC)
    except Exception:
        return datetime.now(UTC)


def _determine_direction(email_msg: EmailMessage, account_email: str) -> str:
    """Determine if an email is inbound or outbound based on the account email."""
    if email_msg.from_email.lower() == account_email.lower():
        return "outbound"
    return "inbound"


async def _get_case_contact_emails(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
) -> list[str]:
    """Get all email addresses of contacts linked to a case.

    Collects emails from: client, opposing_party, billing_contact, and case parties.
    """
    emails = []

    # Get the case with its relationships
    result = await db.execute(select(Case).where(Case.id == case_id, Case.tenant_id == tenant_id))
    case = result.scalar_one_or_none()
    if not case:
        return emails

    # Collect contact IDs from the case
    contact_ids = set()
    if case.client_id:
        contact_ids.add(case.client_id)
    if case.opposing_party_id:
        contact_ids.add(case.opposing_party_id)
    if hasattr(case, "billing_contact_id") and case.billing_contact_id:
        contact_ids.add(case.billing_contact_id)

    # Add case party contacts
    party_result = await db.execute(
        select(CaseParty.contact_id).where(
            CaseParty.case_id == case_id,
            CaseParty.tenant_id == tenant_id,
        )
    )
    for row in party_result.all():
        if row[0]:
            contact_ids.add(row[0])

    if not contact_ids:
        return emails

    # Get email addresses for all contacts
    contact_result = await db.execute(
        select(Contact.email).where(
            Contact.id.in_(contact_ids),
            Contact.email.isnot(None),
            Contact.email != "",
        )
    )
    for row in contact_result.all():
        if row[0]:
            emails.append(row[0].lower().strip())

    return emails


async def _download_attachments(
    db: AsyncSession,
    provider,
    access_token: str,
    tenant_id: uuid.UUID,
    synced_email_id: uuid.UUID,
    msg: EmailMessage,
    *,
    imap_host: str = "",
    imap_port: int = 993,
    imap_username: str = "",
) -> int:
    """Download all attachments for an email and store them on disk + DB.

    Returns the number of attachments successfully downloaded.
    """
    if not msg.attachments:
        return 0

    # Create storage directory
    storage_dir = EMAIL_ATTACHMENTS_BASE / str(tenant_id) / str(synced_email_id)
    storage_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    for att in msg.attachments:
        try:
            # Download from provider
            if imap_host:
                file_bytes = await provider.get_attachment(
                    access_token,
                    msg.provider_message_id,
                    att.attachment_id,
                    host=imap_host,
                    port=imap_port,
                    username=imap_username,
                )
            else:
                file_bytes = await provider.get_attachment(
                    access_token, msg.provider_message_id, att.attachment_id
                )

            # Generate stored filename
            import os

            ext = os.path.splitext(att.filename)[1] if att.filename else ""
            stored_filename = f"{uuid.uuid4()}{ext}"
            file_path = storage_dir / stored_filename

            # Write to disk
            file_path.write_bytes(file_bytes)

            # Create DB record
            attachment = EmailAttachment(
                tenant_id=tenant_id,
                synced_email_id=synced_email_id,
                provider_attachment_id=att.attachment_id,
                filename=att.filename,
                stored_filename=stored_filename,
                content_type=att.content_type,
                file_size=len(file_bytes),
                downloaded_at=datetime.now(UTC),
            )
            db.add(attachment)
            downloaded += 1

        except Exception as e:
            logger.error(f"Bijlage '{att.filename}' downloaden mislukt: {e}")

    return downloaded


async def sync_emails_for_account(
    db: AsyncSession,
    account: EmailAccount,
    *,
    max_results: int = 100,
    query: str | None = None,
    force_case_id: uuid.UUID | None = None,
) -> dict:
    """Sync emails from the provider into the synced_emails table.

    Args:
        db: Database session
        account: The email account to sync
        max_results: Maximum emails to fetch
        query: Gmail search query filter
        force_case_id: If provided, builds a Gmail query from the case's
            contact emails and auto-links all results to this case.

    Returns a summary dict with counts.
    """
    provider = get_provider(account.provider)

    # IMAP accounts use password directly instead of OAuth tokens
    if account.provider == "imap":
        access_token = decrypt_token(account.access_token_enc)
    else:
        access_token = await get_valid_access_token(db, account)

    # If syncing from a dossier context, build a Gmail query from the case contacts
    if force_case_id and not query:
        contact_emails = await _get_case_contact_emails(db, account.tenant_id, force_case_id)
        if contact_emails:
            # Build Gmail query: emails from OR to any contact
            email_parts = []
            for email in contact_emails:
                email_parts.append(f"from:{email}")
                email_parts.append(f"to:{email}")
            query = " OR ".join(email_parts)
            logger.info(f"Dossier-sync query voor case {force_case_id}: {query}")
        else:
            logger.warning(f"Geen contact-emailadressen gevonden voor case {force_case_id}")

    # Fetch messages from provider
    if account.provider == "imap":
        # IMAP: parse host:port from scopes field, pass username
        host_port = (account.scopes or "imap.basenet.nl:993").split(":")
        imap_host = host_port[0]
        imap_port = int(host_port[1]) if len(host_port) > 1 else 993
        messages, next_page = await provider.list_messages(
            access_token,
            max_results=max_results,
            host=imap_host,
            port=imap_port,
            username=account.email_address,
        )
    else:
        messages, next_page = await provider.list_messages(
            access_token,
            max_results=max_results,
            query=query,
        )

    stats = {"fetched": len(messages), "new": 0, "linked": 0, "skipped": 0}
    new_emails_with_attachments: list[tuple[EmailMessage, uuid.UUID]] = []

    for msg in messages:
        # Check if already synced (dedup by provider_message_id)
        existing = await db.execute(
            select(SyncedEmail.id, SyncedEmail.case_id).where(
                SyncedEmail.email_account_id == account.id,
                SyncedEmail.provider_message_id == msg.provider_message_id,
            )
        )
        existing_row = existing.first()
        if existing_row is not None:
            # If already synced but unlinked → try to link it
            if existing_row[1] is None:
                link_to = force_case_id
                matched_by_val = "force_case_id" if force_case_id else None
                if not link_to:
                    link_to, matched_by_val, _ = await _find_case_by_case_number(
                        db, account.tenant_id, msg.subject or ""
                    )
                if link_to:
                    synced_email = (
                        await db.execute(
                            select(SyncedEmail).where(SyncedEmail.id == existing_row[0])
                        )
                    ).scalar_one()
                    synced_email.case_id = link_to
                    synced_email.matched_by = matched_by_val
                    stats["linked"] += 1
            stats["skipped"] += 1
            continue

        # Secondary dedup: outbound emails sent via provider get a synthetic
        # message ID ("outlook-sent-..."). When the sync later picks up the
        # same email from Sent Items with a real Graph ID, merge instead of
        # creating a duplicate.
        if msg.from_email and msg.from_email.lower() == account.email_address.lower():
            from sqlalchemy import func as sa_func

            dedup_result = await db.execute(
                select(SyncedEmail).where(
                    SyncedEmail.email_account_id == account.id,
                    SyncedEmail.provider_message_id.like("outlook-sent-%"),
                    SyncedEmail.direction == "outbound",
                    sa_func.left(SyncedEmail.subject, 30) == (msg.subject or "")[:30],
                )
            )
            dedup_match = dedup_result.scalar()
            if dedup_match:
                # Update existing record with real IDs from Graph
                dedup_match.provider_message_id = msg.provider_message_id
                dedup_match.provider_thread_id = msg.thread_id
                logger.info(f"Dedup merge: updated synthetic ID for '{msg.subject[:50]}'")
                stats["skipped"] += 1
                continue

        # Collect all email addresses from the message for matching
        all_addresses = []
        if msg.from_email:
            all_addresses.append(msg.from_email.lower())
        for addr in msg.to_emails:
            # Extract email from "Name <email>" format
            email = addr.strip()
            if "<" in email:
                email = email[email.index("<") + 1 : email.index(">")]
            all_addresses.append(email.lower())
        for addr in msg.cc_emails:
            email = addr.strip()
            if "<" in email:
                email = email[email.index("<") + 1 : email.index(">")]
            all_addresses.append(email.lower())

        # Remove the account's own email from matching
        all_addresses = [a for a in all_addresses if a != account.email_address.lower()]

        # ── Matching pipeline ──────────────────────────────────────────────
        direction = _determine_direction(msg, account.email_address)
        email_date = _parse_email_date(msg.date)
        case_id = None
        matched_by = None
        is_bounce = False

        if force_case_id:
            # Priority 1: explicit case context
            case_id = force_case_id
            matched_by = "force_case_id"
        else:
            # Priority 2: thread matching — most reliable
            case_id = await _find_case_by_thread(db, account.id, msg.thread_id)
            if case_id:
                matched_by = "thread"

            # Priority 3: bounce/system email detection
            if not case_id and _is_system_email(msg):
                is_bounce = True
                # For bounces: only try case number in subject, never contact-match
                cn_case_id, cn_matched_by, _ = await _find_case_by_case_number(
                    db, account.tenant_id, msg.subject or ""
                )
                if cn_case_id:
                    case_id = cn_case_id
                    matched_by = cn_matched_by
                # Bounce without a link → leave unlinked, auto-dismiss
            elif not case_id:
                # Priority 4: case number in subject
                cn_case_id, cn_matched_by, has_case_number = await _find_case_by_case_number(
                    db, account.tenant_id, msg.subject or ""
                )
                if cn_case_id:
                    case_id = cn_case_id
                    matched_by = cn_matched_by
                elif not has_case_number:
                    # Priority 5: contact email match
                    # ONLY if no case number was found in the subject
                    # (if a case number was found but dossier doesn't exist,
                    #  we intentionally stop here — don't guess)
                    case_id = await _find_case_for_email(db, account.tenant_id, all_addresses)
                    if case_id:
                        matched_by = "contact_email"

        synced = SyncedEmail(
            tenant_id=account.tenant_id,
            email_account_id=account.id,
            case_id=case_id,
            provider_message_id=msg.provider_message_id,
            provider_thread_id=msg.thread_id,
            subject=msg.subject[:1000],
            from_email=msg.from_email,
            from_name=msg.from_name,
            to_emails=json.dumps(msg.to_emails),
            cc_emails=json.dumps(msg.cc_emails),
            snippet=msg.snippet,
            body_text=msg.body_text,
            body_html=msg.body_html,
            direction=direction,
            is_read=msg.is_read,
            has_attachments=msg.has_attachments,
            is_bounce=is_bounce,
            is_dismissed=is_bounce,  # auto-dismiss bounces
            matched_by=matched_by,
            email_date=email_date,
            synced_at=datetime.now(UTC),
        )
        db.add(synced)
        await db.flush()  # Flush to get synced.id for attachments
        stats["new"] += 1
        if case_id:
            stats["linked"] += 1
        if msg.has_attachments and msg.attachments:
            new_emails_with_attachments.append((msg, synced.id))

    # Update last sync timestamp
    account.last_sync_at = datetime.now(UTC)
    await db.flush()

    # Download attachments for new emails
    attachments_downloaded = 0
    # Prepare IMAP kwargs for attachment downloads
    att_kwargs = {}
    if account.provider == "imap":
        host_port = (account.scopes or "imap.basenet.nl:993").split(":")
        att_kwargs = {
            "imap_host": host_port[0],
            "imap_port": int(host_port[1]) if len(host_port) > 1 else 993,
            "imap_username": account.email_address,
        }
    for msg, synced_id in new_emails_with_attachments:
        try:
            downloaded = await _download_attachments(
                db,
                provider,
                access_token,
                account.tenant_id,
                synced_id,
                msg,
                **att_kwargs,
            )
            attachments_downloaded += downloaded
        except Exception as e:
            logger.error(f"Bijlagen downloaden mislukt voor {msg.provider_message_id}: {e}")

    if attachments_downloaded:
        await db.flush()

    # Re-match unlinked emails on case number / reference
    # This catches emails that were synced before the matching was implemented,
    # or where a case/reference was added after the email was synced.
    # Always run — also when syncing from a dossier context (force_case_id).
    re_linked = await _rematch_unlinked_emails(db, account.tenant_id)
    stats["linked"] += re_linked

    logger.info(
        f"Sync klaar voor {account.email_address}: "
        f"{stats['fetched']} opgehaald, {stats['new']} nieuw, "
        f"{stats['linked']} gekoppeld, {stats['skipped']} overgeslagen, "
        f"{attachments_downloaded} bijlagen"
    )
    return stats


async def _rematch_unlinked_emails(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> int:
    """Re-scan all unlinked synced emails and try to match them to a case.

    Uses thread matching, then case number in subject, then contact email.
    Skips bounce/system emails. Same restrictive pipeline as initial sync.

    Returns the number of emails that were newly linked.
    """
    result = await db.execute(
        select(SyncedEmail).where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.case_id == None,  # noqa: E711
            SyncedEmail.is_bounce == False,  # noqa: E712 — skip bounces
        )
    )
    unlinked = list(result.scalars().all())
    if not unlinked:
        return 0

    linked_count = 0
    for email in unlinked:
        case_id = None
        matched_by = None

        # Priority 1: thread matching
        case_id = await _find_case_by_thread(db, email.email_account_id, email.provider_thread_id)
        if case_id:
            matched_by = "thread"

        # Priority 2: case number in subject
        if not case_id:
            cn_case_id, cn_matched_by, has_case_number = await _find_case_by_case_number(
                db, tenant_id, email.subject or ""
            )
            if cn_case_id:
                case_id = cn_case_id
                matched_by = cn_matched_by
            elif has_case_number:
                # Case number found but dossier doesn't exist → don't fallthrough
                continue

        # Priority 3: contact email match (only if no case number found)
        if not case_id:
            all_addresses = []
            if email.from_email:
                all_addresses.append(email.from_email.lower())
            try:
                to_emails = json.loads(email.to_emails) if email.to_emails else []
            except (json.JSONDecodeError, TypeError):
                to_emails = []
            for addr in to_emails:
                a = addr.strip()
                if "<" in a:
                    a = a[a.index("<") + 1 : a.index(">")]
                all_addresses.append(a.lower())

            if email.email_account:
                all_addresses = [
                    a for a in all_addresses if a != email.email_account.email_address.lower()
                ]

            case_id = await _find_case_for_email(db, tenant_id, all_addresses)
            if case_id:
                matched_by = "contact_email"

        if case_id:
            email.case_id = case_id
            email.matched_by = matched_by
            linked_count += 1
            logger.info(
                f"Re-match: email '{email.subject}' gekoppeld aan case {case_id} via {matched_by}"
            )

    if linked_count:
        await db.flush()
        logger.info(f"Re-match: {linked_count} ongelinkte emails alsnog gekoppeld")

    return linked_count


async def get_case_emails(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[SyncedEmail], int]:
    """Get all synced emails for a specific case, ordered by date desc."""
    # Count
    count_result = await db.execute(
        select(SyncedEmail.id).where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.case_id == case_id,
        )
    )
    total = len(count_result.all())

    # Fetch
    result = await db.execute(
        select(SyncedEmail)
        .where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.case_id == case_id,
        )
        .order_by(SyncedEmail.email_date.desc())
        .limit(limit)
        .offset(offset)
    )
    emails = list(result.scalars().all())

    return emails, total


async def get_all_emails(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    filter_linked: str = "all",  # "all", "linked", "unlinked"
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[SyncedEmail], int]:
    """Get all synced emails with optional filters.

    filter_linked: 'all' = everything, 'linked' = has case_id, 'unlinked' = no case_id
    """
    from sqlalchemy import func, or_

    base_where = [SyncedEmail.tenant_id == tenant_id, SyncedEmail.is_dismissed == False]  # noqa: E712

    if filter_linked == "linked":
        base_where.append(SyncedEmail.case_id != None)  # noqa: E711
    elif filter_linked == "unlinked":
        base_where.append(SyncedEmail.case_id == None)  # noqa: E711

    if search:
        search_term = f"%{search}%"
        base_where.append(
            or_(
                SyncedEmail.subject.ilike(search_term),
                SyncedEmail.from_email.ilike(search_term),
                SyncedEmail.snippet.ilike(search_term),
            )
        )

    count_result = await db.execute(select(func.count(SyncedEmail.id)).where(*base_where))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(SyncedEmail)
        .where(*base_where)
        .order_by(SyncedEmail.email_date.desc())
        .limit(limit)
        .offset(offset)
    )
    emails = list(result.scalars().all())

    return emails, total


async def get_unlinked_emails(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[SyncedEmail], int]:
    """Get emails not linked to any case (for M6 'ongesorteerd' queue)."""
    count_result = await db.execute(
        select(SyncedEmail.id).where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.case_id == None,  # noqa: E711
            SyncedEmail.is_dismissed == False,  # noqa: E712
        )
    )
    total = len(count_result.all())

    result = await db.execute(
        select(SyncedEmail)
        .where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.case_id == None,  # noqa: E711
            SyncedEmail.is_dismissed == False,  # noqa: E712
        )
        .order_by(SyncedEmail.email_date.desc())
        .limit(limit)
        .offset(offset)
    )
    emails = list(result.scalars().all())

    return emails, total


async def link_email_to_case(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email_id: uuid.UUID,
    case_id: uuid.UUID,
) -> SyncedEmail | None:
    """Manually link an email to a case."""
    result = await db.execute(
        select(SyncedEmail).where(
            SyncedEmail.id == email_id,
            SyncedEmail.tenant_id == tenant_id,
        )
    )
    email = result.scalar_one_or_none()
    if not email:
        return None

    email.case_id = case_id
    await db.flush()
    await db.refresh(email)
    return email


async def get_unlinked_count(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> int:
    """Get count of unlinked non-dismissed emails (for sidebar badge)."""
    result = await db.execute(
        select(SyncedEmail.id).where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.case_id == None,  # noqa: E711
            SyncedEmail.is_dismissed == False,  # noqa: E712
        )
    )
    return len(result.all())


async def dismiss_emails(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email_ids: list[uuid.UUID],
) -> int:
    """Dismiss emails from the ongesorteerd queue (bulk)."""
    result = await db.execute(
        select(SyncedEmail).where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.id.in_(email_ids),
        )
    )
    emails = list(result.scalars().all())
    count = 0
    for email in emails:
        email.is_dismissed = True
        count += 1
    await db.flush()
    return count


async def bulk_link_emails(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email_ids: list[uuid.UUID],
    case_id: uuid.UUID,
) -> int:
    """Link multiple emails to the same case (bulk)."""
    result = await db.execute(
        select(SyncedEmail).where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.id.in_(email_ids),
        )
    )
    emails = list(result.scalars().all())
    count = 0
    for email in emails:
        email.case_id = case_id
        email.is_dismissed = False  # Un-dismiss if previously dismissed
        count += 1
    await db.flush()
    return count


async def suggest_cases_for_email(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email_id: uuid.UUID,
) -> list[dict]:
    """Suggest cases for an unlinked email based on contact + case number matching.

    Returns list of dicts with case_id, case_number, description, client_name, match_reason.
    """
    result = await db.execute(
        select(SyncedEmail).where(
            SyncedEmail.id == email_id,
            SyncedEmail.tenant_id == tenant_id,
        )
    )
    email = result.scalar_one_or_none()
    if not email:
        return []

    suggestions: dict[uuid.UUID, dict] = {}  # case_id -> suggestion dict

    # --- Method 1: Case number / reference / court number matching ---
    searchable = _build_searchable_text(
        email.subject, email.body_text, email.body_html, email.snippet
    )
    if searchable:
        text_lower = searchable.lower()

        # Case number regex
        matches = CASE_NUMBER_RE.findall(searchable)
        if matches:
            cn_result = await db.execute(
                select(Case.id, Case.case_number, Case.description).where(
                    Case.tenant_id == tenant_id,
                    Case.is_active == True,  # noqa: E712
                    Case.case_number.in_(matches),
                )
            )
            for row in cn_result.all():
                suggestions[row[0]] = {
                    "case_id": str(row[0]),
                    "case_number": row[1],
                    "description": row[2],
                    "match_reason": "dossiernummer",
                    "confidence": "high",
                }

        # Client reference
        ref_result = await db.execute(
            select(Case.id, Case.case_number, Case.description, Case.reference).where(
                Case.tenant_id == tenant_id,
                Case.is_active == True,  # noqa: E712
                Case.reference.isnot(None),
                Case.reference != "",
            )
        )
        for row in ref_result.all():
            ref = row[3].strip()
            if len(ref) >= 3 and ref.lower() in text_lower and row[0] not in suggestions:
                suggestions[row[0]] = {
                    "case_id": str(row[0]),
                    "case_number": row[1],
                    "description": row[2],
                    "match_reason": "klantreferentie",
                    "confidence": "high",
                }

        # Court case number
        court_result = await db.execute(
            select(Case.id, Case.case_number, Case.description, Case.court_case_number).where(
                Case.tenant_id == tenant_id,
                Case.is_active == True,  # noqa: E712
                Case.court_case_number.isnot(None),
                Case.court_case_number != "",
            )
        )
        for row in court_result.all():
            court_num = row[3].strip()
            is_match = (
                len(court_num) >= 3
                and court_num.lower() in text_lower
                and row[0] not in suggestions
            )
            if is_match:
                suggestions[row[0]] = {
                    "case_id": str(row[0]),
                    "case_number": row[1],
                    "description": row[2],
                    "match_reason": "zaaknummer rechtbank",
                    "confidence": "high",
                }

    # --- Method 2: Contact email matching ---
    all_addresses = []
    if email.from_email:
        all_addresses.append(email.from_email.lower())
    try:
        to_list = json.loads(email.to_emails) if email.to_emails else []
        for addr in to_list:
            addr = addr.strip()
            if "<" in addr:
                addr = addr[addr.index("<") + 1 : addr.index(">")]
            all_addresses.append(addr.lower())
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        cc_list = json.loads(email.cc_emails) if email.cc_emails else []
        for addr in cc_list:
            addr = addr.strip()
            if "<" in addr:
                addr = addr[addr.index("<") + 1 : addr.index(">")]
            all_addresses.append(addr.lower())
    except (json.JSONDecodeError, TypeError):
        pass

    if all_addresses:
        contact_result = await db.execute(
            select(Contact.id, Contact.email).where(
                Contact.tenant_id == tenant_id,
                Contact.email.in_(all_addresses),
                Contact.is_active == True,  # noqa: E712
            )
        )
        contact_rows = contact_result.all()
        contact_ids = [row[0] for row in contact_rows]
        contact_email_map = {row[0]: row[1] for row in contact_rows}

        if contact_ids:
            # Cases where contact is client or opposing party
            case_result = await db.execute(
                select(
                    Case.id,
                    Case.case_number,
                    Case.description,
                    Case.client_id,
                    Case.opposing_party_id,
                ).where(
                    Case.tenant_id == tenant_id,
                    Case.is_active == True,  # noqa: E712
                    or_(
                        Case.client_id.in_(contact_ids),
                        Case.opposing_party_id.in_(contact_ids),
                    ),
                )
            )
            for row in case_result.all():
                if row[0] not in suggestions:
                    matched_contact_id = None
                    role = "contact"
                    if row[3] in contact_ids:
                        matched_contact_id = row[3]
                        role = "cliënt"
                    elif row[4] in contact_ids:
                        matched_contact_id = row[4]
                        role = "wederpartij"
                    matched_email = contact_email_map.get(matched_contact_id, "")
                    suggestions[row[0]] = {
                        "case_id": str(row[0]),
                        "case_number": row[1],
                        "description": row[2],
                        "match_reason": f"{role} ({matched_email})",
                        "confidence": "high" if role == "cliënt" else "medium",
                    }

            # Cases via case parties
            party_result = await db.execute(
                select(CaseParty.case_id, CaseParty.contact_id).where(
                    CaseParty.tenant_id == tenant_id,
                    CaseParty.contact_id.in_(contact_ids),
                )
            )
            party_case_ids = []
            party_contact_map = {}
            for row in party_result.all():
                party_case_ids.append(row[0])
                party_contact_map[row[0]] = row[1]

            if party_case_ids:
                pcase_result = await db.execute(
                    select(Case.id, Case.case_number, Case.description).where(
                        Case.tenant_id == tenant_id,
                        Case.is_active == True,  # noqa: E712
                        Case.id.in_(party_case_ids),
                    )
                )
                for row in pcase_result.all():
                    if row[0] not in suggestions:
                        matched_contact_id = party_contact_map.get(row[0])
                        matched_email = contact_email_map.get(matched_contact_id, "")
                        suggestions[row[0]] = {
                            "case_id": str(row[0]),
                            "case_number": row[1],
                            "description": row[2],
                            "match_reason": f"partij ({matched_email})",
                            "confidence": "medium",
                        }

    # Fetch client names for all suggestions
    suggestion_list = list(suggestions.values())
    case_ids_to_fetch = [uuid.UUID(s["case_id"]) for s in suggestion_list]
    client_names: dict[str, str] = {}
    if case_ids_to_fetch:
        cn_result = await db.execute(
            select(Case.id, Contact.display_name)
            .join(Contact, Case.client_id == Contact.id, isouter=True)
            .where(Case.id.in_(case_ids_to_fetch))
        )
        for row in cn_result.all():
            client_names[str(row[0])] = row[1] or ""

    for s in suggestion_list:
        s["client_name"] = client_names.get(s["case_id"], "")

    # Sort: high confidence first, then by case_number
    suggestion_list.sort(key=lambda s: (0 if s["confidence"] == "high" else 1, s["case_number"]))

    return suggestion_list[:5]
