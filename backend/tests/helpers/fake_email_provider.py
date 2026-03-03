"""Fake email provider for testing — records all sent messages in-memory."""

from dataclasses import dataclass, field

from app.email.providers.base import (
    AttachmentInfo,
    EmailMessage,
    EmailProvider,
    OAuthTokens,
    OutgoingAttachment,
)


@dataclass
class SentMessage:
    """A message captured by FakeEmailProvider."""

    to: list[str]
    subject: str
    body_html: str
    cc: list[str] | None = None
    reply_to_message_id: str | None = None
    attachments: list[OutgoingAttachment] = field(default_factory=list)


class FakeEmailProvider(EmailProvider):
    """In-memory email provider that captures all sent messages for assertion."""

    def __init__(self):
        self.sent_messages: list[SentMessage] = []
        self._message_counter = 0

    def get_authorize_url(self, state: str) -> str:
        return f"https://fake-provider.test/auth?state={state}"

    async def exchange_code(self, code: str) -> OAuthTokens:
        return OAuthTokens(
            access_token="fake-access-token",
            refresh_token="fake-refresh-token",
            expires_in=3600,
            email="test@fake.test",
        )

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        return OAuthTokens(
            access_token="fake-refreshed-token",
            refresh_token=refresh_token,
            expires_in=3600,
        )

    async def get_user_email(self, access_token: str) -> str:
        return "test@fake.test"

    async def list_messages(
        self,
        access_token: str,
        *,
        max_results: int = 50,
        page_token: str | None = None,
        query: str | None = None,
    ) -> tuple[list[EmailMessage], str | None]:
        return [], None

    async def get_message(
        self, access_token: str, message_id: str
    ) -> EmailMessage:
        return EmailMessage(provider_message_id=message_id)

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
        self._message_counter += 1
        msg = SentMessage(
            to=to,
            subject=subject,
            body_html=body_html,
            cc=cc,
            reply_to_message_id=reply_to_message_id,
            attachments=attachments or [],
        )
        self.sent_messages.append(msg)
        return f"fake-msg-{self._message_counter}"

    async def create_draft(
        self,
        access_token: str,
        *,
        to: list[str],
        subject: str,
        body_html: str,
        cc: list[str] | None = None,
    ) -> str:
        return "fake-draft-1"

    async def get_attachment(
        self,
        access_token: str,
        message_id: str,
        attachment_id: str,
    ) -> bytes:
        return b"fake-attachment-data"
