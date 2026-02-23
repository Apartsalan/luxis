"""Email OAuth service — business logic for connecting/managing email accounts.

Handles OAuth state generation, token storage, auto-refresh, and provider instantiation.
"""

import base64
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.email.oauth_models import EmailAccount
from app.email.providers.base import EmailProvider
from app.email.providers.gmail import GmailProvider
from app.email.providers.outlook import OutlookProvider
from app.email.token_encryption import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)


def get_provider(provider_name: str) -> EmailProvider:
    """Get an EmailProvider instance by name."""
    if provider_name == "gmail":
        return GmailProvider()
    if provider_name == "outlook":
        return OutlookProvider()
    raise ValueError(f"Onbekende email provider: {provider_name}")


def encode_oauth_state(user_id: str, tenant_id: str, provider: str) -> str:
    """Encode user context into the OAuth state parameter for CSRF protection."""
    payload = json.dumps({"user_id": user_id, "tenant_id": tenant_id, "provider": provider})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_oauth_state(state: str) -> dict:
    """Decode the OAuth state parameter back to user context."""
    payload = base64.urlsafe_b64decode(state.encode()).decode()
    return json.loads(payload)


async def get_email_account(
    db: AsyncSession,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    provider: str | None = None,
) -> EmailAccount | None:
    """Get the email account for a user, optionally filtered by provider."""
    query = select(EmailAccount).where(
        EmailAccount.user_id == user_id,
        EmailAccount.tenant_id == tenant_id,
    )
    if provider:
        query = query.where(EmailAccount.provider == provider)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def store_email_account(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    provider: str,
    email_address: str,
    access_token: str,
    refresh_token: str,
    expires_in: int,
    scopes: str = "",
) -> EmailAccount:
    """Store or update an email account with encrypted tokens.

    If an account already exists for this user+provider, update it.
    Otherwise, create a new one.
    """
    existing = await get_email_account(db, user_id, tenant_id, provider)

    token_expiry = datetime.now(UTC) + timedelta(seconds=expires_in)
    access_enc = encrypt_token(access_token)
    refresh_enc = encrypt_token(refresh_token)

    if existing:
        existing.email_address = email_address
        existing.access_token_enc = access_enc
        existing.refresh_token_enc = refresh_enc
        existing.token_expiry = token_expiry
        existing.scopes = scopes
        existing.connected_at = datetime.now(UTC)
        await db.flush()
        await db.refresh(existing)
        logger.info(f"Email account bijgewerkt: {email_address} ({provider})")
        return existing

    account = EmailAccount(
        tenant_id=tenant_id,
        user_id=user_id,
        provider=provider,
        email_address=email_address,
        access_token_enc=access_enc,
        refresh_token_enc=refresh_enc,
        token_expiry=token_expiry,
        scopes=scopes,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)
    logger.info(f"Email account verbonden: {email_address} ({provider})")
    return account


async def get_valid_access_token(
    db: AsyncSession,
    account: EmailAccount,
) -> str:
    """Get a valid access token, auto-refreshing if expired.

    This is the main entry point for getting a usable token.
    It checks expiry, refreshes if needed, and updates the stored tokens.
    """
    # Check if token is still valid (with 5-minute buffer)
    if account.token_expiry and account.token_expiry > datetime.now(UTC) + timedelta(minutes=5):
        return decrypt_token(account.access_token_enc)

    # Token expired or about to expire — refresh it
    logger.info(f"Token verlopen voor {account.email_address}, verversing gestart...")
    provider = get_provider(account.provider)
    refresh_token = decrypt_token(account.refresh_token_enc)

    try:
        new_tokens = await provider.refresh_access_token(refresh_token)

        # Update stored tokens
        account.access_token_enc = encrypt_token(new_tokens.access_token)
        account.token_expiry = datetime.now(UTC) + timedelta(seconds=new_tokens.expires_in)
        # Google sometimes returns a new refresh token
        if new_tokens.refresh_token and new_tokens.refresh_token != refresh_token:
            account.refresh_token_enc = encrypt_token(new_tokens.refresh_token)

        await db.flush()
        logger.info(f"Token ververst voor {account.email_address}")
        return new_tokens.access_token

    except Exception as e:
        logger.error(f"Token refresh mislukt voor {account.email_address}: {e}")
        raise


async def disconnect_email_account(
    db: AsyncSession,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    provider: str | None = None,
) -> bool:
    """Remove an email account connection."""
    account = await get_email_account(db, user_id, tenant_id, provider)
    if not account:
        return False

    await db.delete(account)
    await db.flush()
    logger.info(f"Email account ontkoppeld: {account.email_address}")
    return True
