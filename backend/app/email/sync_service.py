"""Email sync service — fetches emails from provider, matches to dossiers.

Matching logic:
  1. Extract all email addresses from the message (from, to, cc)
  2. Look up each address in the contacts table
  3. If a contact is found, find cases where that contact is client, opposing party, or case party
  4. If exactly one case matches, auto-link the email
  5. If multiple cases match, leave unlinked (user assigns via M6 "ongesorteerd" queue)
"""

import json
import logging
import uuid
from datetime import UTC, datetime

from dateutil import parser as dateparser
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseParty
from app.email.oauth_models import EmailAccount
from app.email.oauth_service import get_provider, get_valid_access_token
from app.email.providers.base import EmailMessage
from app.email.synced_email_models import SyncedEmail
from app.relations.models import Contact

logger = logging.getLogger(__name__)


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
            f"Meerdere dossiers ({len(case_ids)}) gevonden voor {email_addresses} — niet auto-gekoppeld"
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


async def sync_emails_for_account(
    db: AsyncSession,
    account: EmailAccount,
    *,
    max_results: int = 100,
    query: str | None = None,
) -> dict:
    """Sync emails from the provider into the synced_emails table.

    Returns a summary dict with counts.
    """
    provider = get_provider(account.provider)
    access_token = await get_valid_access_token(db, account)

    # Fetch messages from provider
    messages, next_page = await provider.list_messages(
        access_token,
        max_results=max_results,
        query=query,
    )

    stats = {"fetched": len(messages), "new": 0, "linked": 0, "skipped": 0}

    for msg in messages:
        # Check if already synced (dedup by provider_message_id)
        existing = await db.execute(
            select(SyncedEmail.id).where(
                SyncedEmail.email_account_id == account.id,
                SyncedEmail.provider_message_id == msg.provider_message_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
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

        # Try to match to a case
        case_id = await _find_case_for_email(db, account.tenant_id, all_addresses)

        direction = _determine_direction(msg, account.email_address)
        email_date = _parse_email_date(msg.date)

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
            email_date=email_date,
            synced_at=datetime.now(UTC),
        )
        db.add(synced)
        stats["new"] += 1
        if case_id:
            stats["linked"] += 1

    # Update last sync timestamp
    account.last_sync_at = datetime.now(UTC)
    await db.flush()

    logger.info(
        f"Sync klaar voor {account.email_address}: "
        f"{stats['fetched']} opgehaald, {stats['new']} nieuw, "
        f"{stats['linked']} gekoppeld, {stats['skipped']} overgeslagen"
    )
    return stats


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
        )
    )
    total = len(count_result.all())

    result = await db.execute(
        select(SyncedEmail)
        .where(
            SyncedEmail.tenant_id == tenant_id,
            SyncedEmail.case_id == None,  # noqa: E711
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
