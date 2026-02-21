"""EmailProvider — abstract interface for email providers (Gmail, Outlook).

All provider-specific logic (OAuth, send, fetch) is behind this interface.
The rest of Luxis only talks to EmailProvider, never to Gmail/Outlook directly.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class EmailMessage:
    """A single email message (incoming or outgoing)."""

    provider_message_id: str  # Gmail message ID or Outlook message ID
    thread_id: str | None = None
    subject: str = ""
    from_email: str = ""
    from_name: str = ""
    to_emails: list[str] = field(default_factory=list)
    cc_emails: list[str] = field(default_factory=list)
    date: str = ""  # ISO 8601
    snippet: str = ""  # Short preview text
    body_text: str = ""
    body_html: str = ""
    is_read: bool = True
    labels: list[str] = field(default_factory=list)
    has_attachments: bool = False


@dataclass
class OAuthTokens:
    """OAuth token set returned after authorization."""

    access_token: str
    refresh_token: str
    expires_in: int  # Seconds until access_token expires
    scope: str = ""
    email: str = ""  # The email address of the authenticated user


class EmailProvider(ABC):
    """Abstract email provider interface.

    Implementations: GmailProvider, OutlookProvider (future).
    """

    @abstractmethod
    def get_authorize_url(self, state: str) -> str:
        """Generate the OAuth authorization URL for the user to visit.

        Args:
            state: Opaque string for CSRF protection (encode user_id + tenant_id).

        Returns:
            Full OAuth authorization URL to redirect the user to.
        """
        ...

    @abstractmethod
    async def exchange_code(self, code: str) -> OAuthTokens:
        """Exchange an authorization code for access + refresh tokens.

        Args:
            code: The authorization code from the OAuth callback.

        Returns:
            OAuthTokens with access_token, refresh_token, expires_in.
        """
        ...

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        """Refresh an expired access token using the refresh token.

        Args:
            refresh_token: The stored refresh token.

        Returns:
            OAuthTokens with new access_token (refresh_token may be unchanged).
        """
        ...

    @abstractmethod
    async def get_user_email(self, access_token: str) -> str:
        """Get the email address of the authenticated user.

        Args:
            access_token: Valid OAuth access token.

        Returns:
            The user's email address (e.g. "user@gmail.com").
        """
        ...

    @abstractmethod
    async def list_messages(
        self,
        access_token: str,
        *,
        max_results: int = 50,
        page_token: str | None = None,
        query: str | None = None,
    ) -> tuple[list[EmailMessage], str | None]:
        """Fetch a page of messages from the inbox.

        Args:
            access_token: Valid OAuth access token.
            max_results: Maximum messages to return.
            page_token: Pagination token from previous call.
            query: Provider-specific search query (e.g. Gmail q parameter).

        Returns:
            Tuple of (messages, next_page_token). next_page_token is None when done.
        """
        ...

    @abstractmethod
    async def get_message(self, access_token: str, message_id: str) -> EmailMessage:
        """Fetch a single message by ID with full body.

        Args:
            access_token: Valid OAuth access token.
            message_id: Provider-specific message ID.

        Returns:
            EmailMessage with full body content.
        """
        ...

    @abstractmethod
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
        """Send an email through the provider.

        Args:
            access_token: Valid OAuth access token.
            to: List of recipient email addresses.
            subject: Email subject.
            body_html: HTML body content.
            cc: Optional CC recipients.
            reply_to_message_id: If replying, the original message ID.

        Returns:
            The provider message ID of the sent message.
        """
        ...

    @abstractmethod
    async def create_draft(
        self,
        access_token: str,
        *,
        to: list[str],
        subject: str,
        body_html: str,
        cc: list[str] | None = None,
    ) -> str:
        """Create a draft email in the provider.

        Args:
            access_token: Valid OAuth access token.
            to: List of recipient email addresses.
            subject: Email subject.
            body_html: HTML body content.
            cc: Optional CC recipients.

        Returns:
            The provider draft ID.
        """
        ...
