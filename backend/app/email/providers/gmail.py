"""GmailProvider — Gmail API implementation of EmailProvider.

Uses Google OAuth 2.0 + Gmail REST API v1.
Docs: https://developers.google.com/gmail/api/reference/rest
"""

import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.email.providers.base import EmailMessage, EmailProvider, OAuthTokens

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"

# Scopes: read + send + compose drafts + modify (for labels/read status)
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _parse_gmail_message(data: dict) -> EmailMessage:
    """Parse a Gmail API message resource into our EmailMessage dataclass."""
    payload = data.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}

    # Extract body
    body_text = ""
    body_html = ""

    def _extract_body(part: dict) -> None:
        nonlocal body_text, body_html
        mime = part.get("mimeType", "")
        if mime == "text/plain" and not body_text:
            raw = part.get("body", {}).get("data", "")
            if raw:
                body_text = base64.urlsafe_b64decode(raw).decode("utf-8", errors="replace")
        elif mime == "text/html" and not body_html:
            raw = part.get("body", {}).get("data", "")
            if raw:
                body_html = base64.urlsafe_b64decode(raw).decode("utf-8", errors="replace")
        for sub in part.get("parts", []):
            _extract_body(sub)

    _extract_body(payload)

    # Check for attachments
    has_attachments = False

    def _check_attachments(part: dict) -> None:
        nonlocal has_attachments
        if part.get("filename"):
            has_attachments = True
        for sub in part.get("parts", []):
            _check_attachments(sub)

    _check_attachments(payload)

    # Parse from header: "Name <email>" → name, email
    from_header = headers.get("from", "")
    from_name = ""
    from_email = from_header
    if "<" in from_header and ">" in from_header:
        from_name = from_header[: from_header.index("<")].strip().strip('"')
        from_email = from_header[from_header.index("<") + 1 : from_header.index(">")]

    # Parse to/cc (comma-separated)
    to_header = headers.get("to", "")
    to_emails = [e.strip() for e in to_header.split(",") if e.strip()] if to_header else []
    cc_header = headers.get("cc", "")
    cc_emails = [e.strip() for e in cc_header.split(",") if e.strip()] if cc_header else []

    label_ids = data.get("labelIds", [])

    return EmailMessage(
        provider_message_id=data["id"],
        thread_id=data.get("threadId"),
        subject=headers.get("subject", "(geen onderwerp)"),
        from_email=from_email,
        from_name=from_name,
        to_emails=to_emails,
        cc_emails=cc_emails,
        date=headers.get("date", ""),
        snippet=data.get("snippet", ""),
        body_text=body_text,
        body_html=body_html,
        is_read="UNREAD" not in label_ids,
        labels=label_ids,
        has_attachments=has_attachments,
    )


class GmailProvider(EmailProvider):
    """Gmail API implementation."""

    def __init__(self) -> None:
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri

    def get_authorize_url(self, state: str) -> str:
        """Generate the Google OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(GMAIL_SCOPES),
            "access_type": "offline",  # Gets us a refresh_token
            "prompt": "consent",  # Always show consent to guarantee refresh_token
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthTokens:
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        access_token = data["access_token"]
        email = await self.get_user_email(access_token)

        return OAuthTokens(
            access_token=access_token,
            refresh_token=data.get("refresh_token", ""),
            expires_in=data.get("expires_in", 3600),
            scope=data.get("scope", ""),
            email=email,
        )

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        """Refresh an expired access token."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=refresh_token,  # Google doesn't always return a new refresh token
            expires_in=data.get("expires_in", 3600),
            scope=data.get("scope", ""),
        )

    async def get_user_email(self, access_token: str) -> str:
        """Get the email address of the authenticated Gmail user."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GMAIL_API_BASE}/users/me/profile",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            return resp.json()["emailAddress"]

    async def list_messages(
        self,
        access_token: str,
        *,
        max_results: int = 50,
        page_token: str | None = None,
        query: str | None = None,
    ) -> tuple[list[EmailMessage], str | None]:
        """Fetch messages from Gmail inbox."""
        params: dict = {"maxResults": max_results}
        if page_token:
            params["pageToken"] = page_token
        if query:
            params["q"] = query

        async with httpx.AsyncClient() as client:
            # Step 1: Get message IDs
            resp = await client.get(
                f"{GMAIL_API_BASE}/users/me/messages",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

            message_ids = data.get("messages", [])
            next_page = data.get("nextPageToken")

            if not message_ids:
                return [], None

            # Step 2: Fetch each message with metadata + body
            messages = []
            for msg_ref in message_ids:
                msg_resp = await client.get(
                    f"{GMAIL_API_BASE}/users/me/messages/{msg_ref['id']}",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={"format": "full"},
                )
                if msg_resp.status_code == 200:
                    messages.append(_parse_gmail_message(msg_resp.json()))

        return messages, next_page

    async def get_message(self, access_token: str, message_id: str) -> EmailMessage:
        """Fetch a single Gmail message by ID."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GMAIL_API_BASE}/users/me/messages/{message_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"format": "full"},
            )
            resp.raise_for_status()
            return _parse_gmail_message(resp.json())

    async def send_message(
        self,
        access_token: str,
        *,
        to: list[str],
        subject: str,
        body_html: str,
        cc: list[str] | None = None,
        reply_to_message_id: str | None = None,
    ) -> str:
        """Send an email via Gmail API."""
        msg = MIMEMultipart("alternative")
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg.attach(MIMEText(body_html, "html"))

        # If replying, set threading headers
        if reply_to_message_id:
            # Fetch original to get Message-ID header
            original = await self.get_message(access_token, reply_to_message_id)
            # Gmail handles threading via threadId, but we also set headers
            msg["In-Reply-To"] = reply_to_message_id
            msg["References"] = reply_to_message_id

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        body: dict = {"raw": raw}
        if reply_to_message_id:
            body["threadId"] = (await self.get_message(access_token, reply_to_message_id)).thread_id

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GMAIL_API_BASE}/users/me/messages/send",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
            return resp.json()["id"]

    async def create_draft(
        self,
        access_token: str,
        *,
        to: list[str],
        subject: str,
        body_html: str,
        cc: list[str] | None = None,
    ) -> str:
        """Create a draft in Gmail."""
        msg = MIMEMultipart("alternative")
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg.attach(MIMEText(body_html, "html"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GMAIL_API_BASE}/users/me/drafts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={"message": {"raw": raw}},
            )
            resp.raise_for_status()
            return resp.json()["id"]
