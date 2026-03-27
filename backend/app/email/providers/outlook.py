"""OutlookProvider — Microsoft Graph API implementation of EmailProvider.

Uses Microsoft Identity Platform (OAuth 2.0) + Microsoft Graph API v1.0.
Docs: https://learn.microsoft.com/en-us/graph/api/overview

Tested with: seidony@kestinglegal.nl (M365 Business Basic)
Azure App: "Luxis Email Integration"
Permissions: Mail.Read, Mail.ReadWrite, Mail.Send, offline_access, User.Read
"""

import base64
import logging
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.email.providers.base import (
    AttachmentInfo,
    EmailMessage,
    EmailProvider,
    OAuthTokens,
    OutgoingAttachment,
)

logger = logging.getLogger(__name__)

# Microsoft Identity Platform endpoints
# Using tenant-specific endpoint (not /common) because we have a single-tenant app
MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

# Microsoft Graph API base
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

# Scopes for Outlook mail
OUTLOOK_SCOPES = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/User.Read",
    "offline_access",
]


def _parse_graph_message(data: dict) -> EmailMessage:
    """Parse a Microsoft Graph mail message resource into our EmailMessage dataclass."""
    # From
    from_data = data.get("from", {}).get("emailAddress", {})
    from_email = from_data.get("address", "")
    from_name = from_data.get("name", "")

    # To recipients
    to_emails = []
    for r in data.get("toRecipients", []):
        addr = r.get("emailAddress", {}).get("address", "")
        if addr:
            to_emails.append(addr)

    # CC recipients
    cc_emails = []
    for r in data.get("ccRecipients", []):
        addr = r.get("emailAddress", {}).get("address", "")
        if addr:
            cc_emails.append(addr)

    # Body — Graph returns body.content with body.contentType ("html" or "text")
    body_content = data.get("body", {}).get("content", "")
    body_type = data.get("body", {}).get("contentType", "text").lower()
    body_text = ""
    body_html = ""
    if body_type == "html":
        body_html = body_content
    else:
        body_text = body_content

    # Attachments — Graph includes hasAttachments flag but not full attachment data
    # in list responses. We parse inline attachment info if present.
    has_attachments = data.get("hasAttachments", False)

    # Date — Graph uses ISO 8601 datetime (receivedDateTime)
    date = data.get("receivedDateTime", data.get("sentDateTime", ""))

    # Read status
    is_read = data.get("isRead", True)

    # Conversation ID (Graph's threading equivalent)
    thread_id = data.get("conversationId")

    return EmailMessage(
        provider_message_id=data["id"],
        thread_id=thread_id,
        subject=data.get("subject", "(geen onderwerp)"),
        from_email=from_email,
        from_name=from_name,
        to_emails=to_emails,
        cc_emails=cc_emails,
        date=date,
        snippet=data.get("bodyPreview", ""),
        body_text=body_text,
        body_html=body_html,
        is_read=is_read,
        labels=[],  # Graph doesn't use labels like Gmail; categories exist but we skip them
        has_attachments=has_attachments,
        attachments=[],  # Populated separately via get_message_attachments
    )


class OutlookProvider(EmailProvider):
    """Microsoft Graph API implementation for Outlook/M365 email."""

    def __init__(self) -> None:
        self.client_id = settings.microsoft_client_id
        self.tenant_id = settings.microsoft_tenant_id
        self.client_secret = settings.microsoft_client_secret
        self.redirect_uri = settings.microsoft_redirect_uri

    def _auth_url(self) -> str:
        return MICROSOFT_AUTH_URL.format(tenant_id=self.tenant_id)

    def _token_url(self) -> str:
        return MICROSOFT_TOKEN_URL.format(tenant_id=self.tenant_id)

    def get_authorize_url(self, state: str) -> str:
        """Generate the Microsoft OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(OUTLOOK_SCOPES),
            "response_mode": "query",
            "state": state,
        }
        return f"{self._auth_url()}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthTokens:
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self._token_url(),
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                    "scope": " ".join(OUTLOOK_SCOPES),
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
                self._token_url(),
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "scope": " ".join(OUTLOOK_SCOPES),
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return OAuthTokens(
            access_token=data["access_token"],
            # Microsoft may return a new refresh token (token rotation)
            refresh_token=data.get("refresh_token", refresh_token),
            expires_in=data.get("expires_in", 3600),
            scope=data.get("scope", ""),
        )

    async def get_user_email(self, access_token: str) -> str:
        """Get the email address of the authenticated Microsoft user."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_API_BASE}/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            # mail is the primary SMTP address; userPrincipalName is the UPN fallback
            return data.get("mail") or data.get("userPrincipalName", "")

    async def list_messages(
        self,
        access_token: str,
        *,
        max_results: int = 50,
        page_token: str | None = None,
        query: str | None = None,
    ) -> tuple[list[EmailMessage], str | None]:
        """Fetch messages from Outlook inbox via Microsoft Graph.

        Args:
            access_token: Valid OAuth access token.
            max_results: Maximum messages to return.
            page_token: The @odata.nextLink URL from a previous call.
            query: OData $filter or $search string. For email-based search,
                   use $search="from:user@example.com" (KQL syntax).
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        if page_token:
            # page_token is actually the full @odata.nextLink URL
            url = page_token
            params = None
        else:
            url = f"{GRAPH_API_BASE}/me/messages"
            params = {
                "$top": str(max_results),
                "$orderby": "receivedDateTime desc",
                "$select": (
                    "id,conversationId,subject,from,toRecipients,ccRecipients,"
                    "receivedDateTime,sentDateTime,bodyPreview,body,isRead,"
                    "hasAttachments"
                ),
            }
            if query:
                # Support both $filter and $search patterns
                # The caller can pass Graph-compatible filter/search strings
                # KQL search: from:user@domain.com OR subject:keyword
                params["$search"] = f'"{query}"'

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        messages = [_parse_graph_message(msg) for msg in data.get("value", [])]

        # For each message with attachments, fetch attachment metadata
        for msg in messages:
            if msg.has_attachments:
                msg.attachments = await self._get_message_attachments(
                    access_token, msg.provider_message_id
                )

        next_link = data.get("@odata.nextLink")
        return messages, next_link

    async def get_message(self, access_token: str, message_id: str) -> EmailMessage:
        """Fetch a single message by ID with full body."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_API_BASE}/me/messages/{message_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "$select": (
                        "id,conversationId,subject,from,toRecipients,ccRecipients,"
                        "receivedDateTime,sentDateTime,bodyPreview,body,isRead,"
                        "hasAttachments"
                    ),
                },
            )
            resp.raise_for_status()
            msg = _parse_graph_message(resp.json())

        # Fetch attachments if present
        if msg.has_attachments:
            msg.attachments = await self._get_message_attachments(access_token, message_id)

        return msg

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
        """Send an email via Microsoft Graph API.

        The message appears in the user's Sent Items folder automatically.
        Supports file attachments inline via contentBytes (max ~4MB per attachment).
        """
        if reply_to_message_id:
            return await self._reply_to_message(
                access_token,
                message_id=reply_to_message_id,
                body_html=body_html,
                to=to,
                cc=cc,
            )

        # Build the sendMail request body
        message_body: dict = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body_html,
                },
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
            },
            "saveToSentItems": True,
        }

        if cc:
            message_body["message"]["ccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in cc
            ]

        if attachments:
            message_body["message"]["attachments"] = [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": att.filename,
                    "contentType": att.content_type,
                    "contentBytes": base64.b64encode(att.data).decode(),
                }
                for att in attachments
            ]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRAPH_API_BASE}/me/sendMail",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=message_body,
            )
            resp.raise_for_status()

        # sendMail returns 202 Accepted with no body — no message ID returned
        # We return a synthetic ID based on timestamp for tracking
        # The actual message will appear in Sent Items after a short delay
        logger.info(f"Email verzonden via Outlook naar {to}")
        ts = int(datetime.now(UTC).timestamp() * 1000)
        return f"outlook-sent-{ts}-{subject[:30]}"

    async def create_draft(
        self,
        access_token: str,
        *,
        to: list[str],
        subject: str,
        body_html: str,
        cc: list[str] | None = None,
        attachments: list[OutgoingAttachment] | None = None,
    ) -> tuple[str, str | None]:
        """Create a draft email in Outlook Drafts folder.

        Returns:
            Tuple of (draft_id, web_link). web_link is the Outlook Web App
            URL to open the draft directly.
        """
        draft_body: dict = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body_html,
            },
            "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
        }

        if cc:
            draft_body["ccRecipients"] = [{"emailAddress": {"address": addr}} for addr in cc]

        if attachments:
            draft_body["attachments"] = [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": att.filename,
                    "contentType": att.content_type,
                    "contentBytes": base64.b64encode(att.data).decode(),
                }
                for att in attachments
            ]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRAPH_API_BASE}/me/messages",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=draft_body,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["id"], data.get("webLink")

    async def get_attachment(
        self,
        access_token: str,
        message_id: str,
        attachment_id: str,
    ) -> bytes:
        """Download attachment bytes from Microsoft Graph API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_API_BASE}/me/messages/{message_id}/attachments/{attachment_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()

            # Graph returns contentBytes as base64-encoded string for file attachments
            content_bytes = data.get("contentBytes", "")
            if content_bytes:
                return base64.b64decode(content_bytes)

            # Fallback: if contentBytes is missing, try $value endpoint
            resp2 = await client.get(
                f"{GRAPH_API_BASE}/me/messages/{message_id}/attachments/{attachment_id}/$value",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp2.raise_for_status()
            return resp2.content

    # ── Private helpers ──────────────────────────────────────────────────────

    async def _get_message_attachments(
        self,
        access_token: str,
        message_id: str,
    ) -> list[AttachmentInfo]:
        """Fetch attachment metadata for a message."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_API_BASE}/me/messages/{message_id}/attachments",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"$select": "id,name,contentType,size,isInline"},
            )
            if resp.status_code != 200:
                logger.warning(
                    "Bijlagen ophalen mislukt voor message %s: %s",
                    message_id,
                    resp.status_code,
                )
                return []

            data = resp.json()

        attachments = []
        for att in data.get("value", []):
            # Skip inline images (embedded in HTML body)
            if att.get("isInline", False):
                continue
            # Only include file attachments (not itemAttachment or referenceAttachment)
            att_type = att.get("@odata.type", "")
            if att_type and "itemAttachment" in att_type:
                continue

            attachments.append(
                AttachmentInfo(
                    attachment_id=att["id"],
                    filename=att.get("name", "bijlage"),
                    content_type=att.get("contentType", "application/octet-stream"),
                    size=att.get("size", 0),
                )
            )

        return attachments

    async def _reply_to_message(
        self,
        access_token: str,
        *,
        message_id: str,
        body_html: str,
        to: list[str],
        cc: list[str] | None = None,
    ) -> str:
        """Reply to an existing message via Graph API reply endpoint."""
        reply_body: dict = {
            "message": {
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
            },
            "comment": body_html,
        }

        if cc:
            reply_body["message"]["ccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in cc
            ]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRAPH_API_BASE}/me/messages/{message_id}/reply",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=reply_body,
            )
            resp.raise_for_status()

        logger.info(f"Reply verzonden via Outlook op message {message_id}")
        return f"outlook-reply-{message_id[:30]}"
