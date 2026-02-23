"""Email providers — abstract interface + concrete implementations."""

from app.email.providers.base import EmailProvider
from app.email.providers.gmail import GmailProvider
from app.email.providers.outlook import OutlookProvider

__all__ = ["EmailProvider", "GmailProvider", "OutlookProvider"]
