"""Email providers — abstract interface + concrete implementations."""

from app.email.providers.base import EmailProvider
from app.email.providers.gmail import GmailProvider

__all__ = ["EmailProvider", "GmailProvider"]
