"""Calendar sync service — syncs Outlook calendar events to Luxis.

Pulls events from Microsoft Graph API calendarView endpoint,
maps them to CalendarEvent records, and handles dedup via provider_event_id.
Optionally links events to cases when the subject contains a case number.
"""

import logging
import re
import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar.models import EVENT_TYPE_COLORS, CalendarEvent
from app.email.oauth_models import EmailAccount
from app.email.oauth_service import get_valid_access_token
from app.email.providers.outlook import OutlookProvider

logger = logging.getLogger(__name__)

# Reuse case number regex from email sync
CASE_NUMBER_RE = re.compile(r"\b(20\d{2}-\d{4,6})\b")

# Simple HTML tag stripper
_HTML_TAG_RE = re.compile(r"<[^>]+>")

# Windows timezone name → IANA mapping (common European timezones)
_WINDOWS_TZ_MAP: dict[str, str] = {
    "W. Europe Standard Time": "Europe/Amsterdam",
    "Central European Standard Time": "Europe/Budapest",
    "Romance Standard Time": "Europe/Paris",
    "Central Europe Standard Time": "Europe/Prague",
    "GMT Standard Time": "Europe/London",
    "Greenwich Standard Time": "Atlantic/Reykjavik",
    "E. Europe Standard Time": "Europe/Bucharest",
    "FLE Standard Time": "Europe/Helsinki",
    "GTB Standard Time": "Europe/Athens",
    "Russian Standard Time": "Europe/Moscow",
    "UTC": "UTC",
    "Pacific Standard Time": "America/Los_Angeles",
    "Eastern Standard Time": "America/New_York",
    "tzone://Microsoft/Utc": "UTC",
}

# Default sync window: 45 days back, 45 days forward
SYNC_WINDOW_DAYS_BACK = 45
SYNC_WINDOW_DAYS_FORWARD = 45


def _strip_html(html: str) -> str:
    """Strip HTML tags to plain text."""
    if not html:
        return ""
    from html import unescape as html_unescape

    text = _HTML_TAG_RE.sub(" ", html)
    text = html_unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _windows_tz_to_iana(windows_tz: str) -> str:
    """Convert Windows timezone name to IANA timezone name."""
    return _WINDOWS_TZ_MAP.get(windows_tz, "Europe/Amsterdam")


def _parse_graph_datetime(dt_obj: dict) -> datetime:
    """Parse a Graph API dateTimeTimeZone object to a timezone-aware datetime.

    Graph returns: {"dateTime": "2026-03-28T10:00:00.0000000", "timeZone": "W. Europe Standard Time"}
    """
    dt_str = dt_obj["dateTime"]
    tz_name = _windows_tz_to_iana(dt_obj.get("timeZone", "UTC"))

    # Remove trailing zeros from fractional seconds (Python can't parse 7 digits)
    if "." in dt_str:
        dt_str = dt_str.rstrip("0").rstrip(".")

    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        tz = ZoneInfo(tz_name)
        dt = dt.replace(tzinfo=tz)

    return dt


def _build_graph_datetime(dt: datetime, all_day: bool = False) -> dict:
    """Build a Graph API dateTimeTimeZone object from a Python datetime.

    For pushing local events to Outlook.
    """
    tz_name = "Europe/Amsterdam"
    if dt.tzinfo:
        tz = ZoneInfo(tz_name)
        dt = dt.astimezone(tz)

    if all_day:
        return {
            "dateTime": dt.strftime("%Y-%m-%dT00:00:00"),
            "timeZone": tz_name,
        }

    return {
        "dateTime": dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "timeZone": tz_name,
    }


async def _find_case_id_by_subject(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    subject: str,
) -> uuid.UUID | None:
    """Try to find a case ID from a case number in the event subject."""
    from app.cases.models import Case

    if not subject:
        return None

    match = CASE_NUMBER_RE.search(subject)
    if not match:
        return None

    case_number = match.group(1)
    result = await db.execute(
        select(Case.id).where(
            Case.tenant_id == tenant_id,
            Case.case_number == case_number,
        )
    )
    case_id = result.scalar_one_or_none()
    if case_id:
        logger.debug("Calendar event matched to case %s via subject", case_number)
    return case_id


async def sync_outlook_events(
    db: AsyncSession,
    account: EmailAccount,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    """Sync Outlook calendar events to Luxis CalendarEvents.

    Returns:
        Stats dict: {"synced": N, "created": N, "updated": N, "deleted": N}
    """
    provider = OutlookProvider()
    access_token = await get_valid_access_token(db, account)

    now = datetime.now(UTC)
    start_dt = (now - timedelta(days=SYNC_WINDOW_DAYS_BACK)).isoformat()
    end_dt = (now + timedelta(days=SYNC_WINDOW_DAYS_FORWARD)).isoformat()

    # Fetch all events in the sync window
    outlook_events = await provider.list_calendar_events(access_token, start_dt, end_dt)

    stats = {"synced": 0, "created": 0, "updated": 0, "deleted": 0}

    # Track all fetched event IDs for deletion detection
    fetched_event_ids: set[str] = set()

    for event in outlook_events:
        # Skip cancelled events
        if event.get("isCancelled", False):
            continue

        event_id = event["id"]
        change_key = event.get("changeKey", "")
        fetched_event_ids.add(event_id)

        # Parse fields
        subject = event.get("subject", "(geen onderwerp)")
        location_data = event.get("location", {})
        location = location_data.get("displayName", "") if location_data else ""
        body_data = event.get("body", {})
        description = ""
        if body_data:
            content = body_data.get("content", "")
            if body_data.get("contentType", "").lower() == "html":
                description = _strip_html(content)
            else:
                description = content
        is_all_day = event.get("isAllDay", False)

        try:
            start_time = _parse_graph_datetime(event["start"])
            end_time = _parse_graph_datetime(event["end"])
        except (KeyError, ValueError) as e:
            logger.warning("Calendar sync: kan event '%s' niet parsen: %s", subject, e)
            continue

        # Look up existing event by provider_event_id
        result = await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.tenant_id == tenant_id,
                CalendarEvent.provider_event_id == event_id,
                CalendarEvent.provider == "outlook",
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Check if changed
            if existing.outlook_change_key == change_key:
                stats["synced"] += 1
                continue

            # Update existing event
            existing.title = subject
            existing.start_time = start_time
            existing.end_time = end_time
            existing.all_day = is_all_day
            existing.location = location or None
            existing.description = description or None
            existing.outlook_change_key = change_key
            existing.is_active = True  # Re-activate if was soft-deleted

            # Re-match case if subject changed
            case_id = await _find_case_id_by_subject(db, tenant_id, subject)
            if case_id:
                existing.case_id = case_id

            stats["updated"] += 1
        else:
            # Create new event
            case_id = await _find_case_id_by_subject(db, tenant_id, subject)

            new_event = CalendarEvent(
                tenant_id=tenant_id,
                title=subject,
                description=description or None,
                event_type="meeting",
                start_time=start_time,
                end_time=end_time,
                all_day=is_all_day,
                location=location or None,
                case_id=case_id,
                color=EVENT_TYPE_COLORS.get("meeting", "#8b5cf6"),
                reminder_minutes=15,
                created_by=user_id,
                provider_event_id=event_id,
                provider="outlook",
                outlook_change_key=change_key,
            )
            db.add(new_event)
            stats["created"] += 1

        stats["synced"] += 1

    # Soft-delete local Outlook events that no longer exist in Outlook
    # Only within the sync window to avoid deleting events outside the window
    if fetched_event_ids:
        result = await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.tenant_id == tenant_id,
                CalendarEvent.provider == "outlook",
                CalendarEvent.is_active.is_(True),
                CalendarEvent.provider_event_id.isnot(None),
                CalendarEvent.start_time >= now - timedelta(days=SYNC_WINDOW_DAYS_BACK),
                CalendarEvent.start_time <= now + timedelta(days=SYNC_WINDOW_DAYS_FORWARD),
                CalendarEvent.provider_event_id.notin_(fetched_event_ids),
            )
        )
        orphaned = list(result.scalars().all())
        for orphan in orphaned:
            orphan.is_active = False
            stats["deleted"] += 1

    await db.flush()

    if stats["created"] > 0 or stats["updated"] > 0 or stats["deleted"] > 0:
        logger.info(
            "Calendar sync: %d synced, %d created, %d updated, %d deleted",
            stats["synced"],
            stats["created"],
            stats["updated"],
            stats["deleted"],
        )

    return stats


async def push_event_to_outlook(
    db: AsyncSession,
    account: EmailAccount,
    event: CalendarEvent,
) -> tuple[str | None, str | None]:
    """Push a local CalendarEvent to Outlook. Returns (event_id, change_key) or (None, None)."""
    try:
        provider = OutlookProvider()
        access_token = await get_valid_access_token(db, account)

        event_data = {
            "subject": event.title,
            "start": _build_graph_datetime(event.start_time, event.all_day),
            "end": _build_graph_datetime(event.end_time, event.all_day),
            "isAllDay": event.all_day,
        }
        if event.location:
            event_data["location"] = {"displayName": event.location}
        if event.description:
            event_data["body"] = {
                "contentType": "text",
                "content": event.description,
            }

        result = await provider.create_calendar_event(access_token, event_data)
        return result.get("id"), result.get("changeKey")
    except Exception as e:
        logger.error("Push event to Outlook failed: %s", e)
        return None, None


async def update_event_in_outlook(
    db: AsyncSession,
    account: EmailAccount,
    event: CalendarEvent,
) -> str | None:
    """Update an existing event in Outlook. Returns new changeKey or None."""
    try:
        provider = OutlookProvider()
        access_token = await get_valid_access_token(db, account)

        event_data = {
            "subject": event.title,
            "start": _build_graph_datetime(event.start_time, event.all_day),
            "end": _build_graph_datetime(event.end_time, event.all_day),
            "isAllDay": event.all_day,
        }
        if event.location:
            event_data["location"] = {"displayName": event.location}
        if event.description:
            event_data["body"] = {
                "contentType": "text",
                "content": event.description,
            }

        result = await provider.update_calendar_event(
            access_token, event.provider_event_id, event_data
        )
        return result.get("changeKey")
    except Exception as e:
        logger.error("Update event in Outlook failed: %s", e)
        return None


async def delete_event_from_outlook(
    db: AsyncSession,
    account: EmailAccount,
    provider_event_id: str,
) -> bool:
    """Delete an event from Outlook. Returns True on success."""
    try:
        provider = OutlookProvider()
        access_token = await get_valid_access_token(db, account)
        await provider.delete_calendar_event(access_token, provider_event_id)
        return True
    except Exception as e:
        logger.error("Delete event from Outlook failed: %s", e)
        return False
