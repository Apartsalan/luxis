"""Email OAuth service — business logic for connecting/managing email accounts.

Handles OAuth state generation, token storage, auto-refresh, and provider instantiation.
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import NamedTuple

import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.email.oauth_models import EmailAccount
from app.email.providers.base import EmailProvider
from app.email.providers.imap_provider import ImapProvider
from app.email.providers.outlook import OutlookProvider
from app.email.token_encryption import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

# Providers die via een API versturen (eigen uitgaande infrastructuur), niet via
# BaseNets SMTP-relay. S231: alleen deze kunnen de Microsoft-blokkade omzeilen.
API_SEND_PROVIDERS = frozenset({"outlook"})

# OAuth state signing — HMAC prevents forgery
_STATE_MAX_AGE_SECONDS = 600  # 10 minutes
_NONCE_PREFIX = "oauth_nonce:"


def _get_redis() -> aioredis.Redis:
    """Get async Redis client."""
    return aioredis.from_url(settings.redis_url, decode_responses=True)


def _sign_state(payload_b64: str) -> str:
    """Create HMAC signature for OAuth state."""
    return hmac.new(settings.secret_key.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()


def get_provider(provider_name: str) -> EmailProvider:
    """Get an EmailProvider instance by name."""
    if provider_name == "outlook":
        return OutlookProvider()
    if provider_name == "imap":
        return ImapProvider()
    raise ValueError(f"Onbekende email provider: {provider_name}")


def imap_smtp_kwargs(account: EmailAccount) -> dict:
    """Extra `send_message` kwargs voor een IMAP-account (SMTP-host/poort/gebruiker).

    Voor OAuth-providers (Outlook) leeg — die versturen via hun eigen API.
    De uitgaande server wordt afgeleid van de IMAP-host: `imap.basenet.nl` →
    `smtp.basenet.nl`, poort 587 (STARTTLS). Het wachtwoord (`access_token`)
    en de afzender (`username`) blijven gelijk aan de ontvangst.

    ponytail: één IMAP-provider vandaag (BaseNet). Komt er een tweede met een
    afwijkende SMTP-host bij, sla die dan expliciet op bij het account i.p.v.
    hier af te leiden.
    """
    if account.provider != "imap":
        return {}
    imap_host = (account.scopes or "imap.basenet.nl:993").split(":")[0]
    if imap_host.startswith("imap."):
        smtp_host = "smtp." + imap_host[len("imap.") :]
    else:
        smtp_host = imap_host
    return {
        "smtp_host": smtp_host,
        "smtp_port": 587,
        "username": account.email_address,
    }


async def encode_oauth_state(user_id: str, tenant_id: str, provider: str) -> str:
    """Encode and HMAC-sign user context into the OAuth state parameter.

    Stores a single-use nonce in Redis to prevent replay attacks (SEC-21).
    """
    nonce = secrets.token_urlsafe(32)
    payload = json.dumps(
        {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "provider": provider,
            "nonce": nonce,
            "ts": int(time.time()),
        }
    )
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = _sign_state(payload_b64)

    # Store nonce in Redis with TTL matching state max age
    r = _get_redis()
    try:
        await r.setex(f"{_NONCE_PREFIX}{nonce}", _STATE_MAX_AGE_SECONDS, "1")
    finally:
        await r.aclose()

    return f"{payload_b64}.{sig}"


async def decode_oauth_state(state: str) -> dict:
    """Decode and verify HMAC-signed OAuth state parameter.

    Consumes the nonce from Redis — state can only be used once (SEC-21).
    """
    if "." not in state:
        raise ValueError("Invalid OAuth state format")
    payload_b64, sig = state.rsplit(".", 1)
    expected_sig = _sign_state(payload_b64)
    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("OAuth state signature mismatch — possible CSRF attack")
    payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
    # Check expiry
    ts = payload.get("ts", 0)
    if time.time() - ts > _STATE_MAX_AGE_SECONDS:
        raise ValueError("OAuth state expired")

    # Verify and consume nonce — prevents replay (SEC-21)
    nonce = payload.get("nonce")
    if nonce:
        r = _get_redis()
        try:
            deleted = await r.delete(f"{_NONCE_PREFIX}{nonce}")
            if not deleted:
                raise ValueError("OAuth state nonce already used or expired")
        finally:
            await r.aclose()

    return payload


async def get_email_account(
    db: AsyncSession,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    provider: str | None = None,
) -> EmailAccount | None:
    """Get the email account for a user, optionally filtered by provider.

    When multiple accounts exist and no provider is specified, prefer
    'outlook' (Graph API) over other providers.
    """
    query = select(EmailAccount).where(
        EmailAccount.user_id == user_id,
        EmailAccount.tenant_id == tenant_id,
    )
    if provider:
        query = query.where(EmailAccount.provider == provider)
    result = await db.execute(query)
    rows = result.scalars().all()
    if not rows:
        return None
    if len(rows) == 1:
        return rows[0]
    # Multiple accounts — prefer outlook (Graph API) for sending/compose
    for row in rows:
        if row.provider == "outlook":
            return row
    return rows[0]


async def get_tenant_send_account(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> EmailAccount | None:
    """Return the connected account for the tenant's fixed sender channel.

    B13 — verzend-vangrail: pipeline-mail (follow-up/incasso-batch) moet altijd
    vanaf het vaste kantoorkanaal (incasso@) de deur uit, ongeacht wie klikt.
    Zoekt het verbonden account waarvan het adres overeenkomt met de ingestelde
    kantoor-e-mail (`Tenant.email`). None als geen kantoor-e-mail is ingesteld of
    er geen verbonden account met dat adres bestaat → beller valt dan terug op het
    account van de klikkende gebruiker (geen regressie).
    """
    from app.auth.models import Tenant

    tenant_email = (
        await db.execute(select(Tenant.email).where(Tenant.id == tenant_id))
    ).scalar()
    if not tenant_email:
        return None

    result = await db.execute(
        select(EmailAccount)
        .where(
            EmailAccount.tenant_id == tenant_id,
            func.lower(EmailAccount.email_address) == tenant_email.strip().lower(),
        )
        # Deterministisch: nieuwste koppeling eerst (meerdere gebruikers kunnen
        # ooit dezelfde mailbox gekoppeld hebben — Codex-review portie 1).
        .order_by(EmailAccount.connected_at.desc())
    )
    rows = result.scalars().all()
    if not rows:
        return None
    for row in rows:
        if row.provider == "outlook":
            return row
    return rows[0]


class OfficeChannel(NamedTuple):
    """Hoe kantoormail de deur uitgaat: via welk account, namens welk adres.

    S231 — BaseNets uitgaande relay (194.180.216.120) staat op Microsofts
    blokkadelijst: alles naar hotmail/outlook/M365 kaatst terug met 550 S3150.
    Daarom scheiden we vervoer van afzender: het bericht kan via het Graph-
    account van een medewerker de deur uit, terwijl er incasso@ boven staat
    (huisregel M1). Vereist "Verzenden als" op dat postvak in Microsoft 365.

    `account`     = het verbonden account dat het vervoer doet (None → SMTP).
    `from_address`= het adres dat op de mail komt; None = het accountadres zelf.
    """

    account: "EmailAccount | None"
    from_address: str | None


async def resolve_office_channel(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> OfficeChannel:
    """Bepaal het kantoorkanaal: vervoerder + afzender.

    Volgorde:
    1. Een verbonden account op het kantooradres zelf dat via een API verstuurt
       (Graph) — ideaal: vervoer én afzender kloppen zonder extra rechten.
    2. Een ander Graph-account van dezelfde tenant, mét het kantooradres als
       afzender ("Verzenden als"). Dit is de route die BaseNets blokkade omzeilt.
    3. Het account op het kantooradres via IMAP/SMTP (BaseNet) — het oude gedrag,
       nog steeds bruikbaar voor ontvangers buiten Microsoft.
    None-account laat de beller terugvallen op het gebruikersaccount of SMTP.
    """
    from app.auth.models import Tenant

    office_email = (
        await db.execute(select(Tenant.email).where(Tenant.id == tenant_id))
    ).scalar()
    if not office_email:
        return OfficeChannel(None, None)
    office_email = office_email.strip()

    accounts = (
        (
            await db.execute(
                select(EmailAccount)
                .where(EmailAccount.tenant_id == tenant_id)
                .order_by(EmailAccount.connected_at.desc())
            )
        )
        .scalars()
        .all()
    )

    on_office_address = [
        a
        for a in accounts
        if (a.email_address or "").strip().lower() == office_email.lower()
    ]

    # 1. Kantooradres zelf via een API-provider.
    for a in on_office_address:
        if a.provider in API_SEND_PROVIDERS:
            return OfficeChannel(a, None)

    # 2. Ander Graph-account, versturend namens het kantooradres.
    for a in accounts:
        if a.provider in API_SEND_PROVIDERS:
            return OfficeChannel(a, office_email)

    # 3. Kantooradres via IMAP/SMTP (BaseNet).
    if on_office_address:
        return OfficeChannel(on_office_address[0], None)

    return OfficeChannel(None, None)


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
