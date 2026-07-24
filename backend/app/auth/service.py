"""Authentication service — JWT creation, verification, and password hashing."""

import hashlib
import logging
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken, User
from app.config import settings

logger = logging.getLogger(__name__)

_DUMMY_HASH = bcrypt.hashpw(b"dummy-timing-equalization", bcrypt.gensalt()).decode("utf-8")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str, tenant_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(user_id: str, tenant_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "type": "refresh",
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Verify email + password and return the user if valid.

    SEC-20: Implements account lockout after repeated failed attempts.
    - 5 failures → locked for 15 minutes
    - 10 failures → locked for 1 hour
    Successful login resets the counter.
    """
    result = await db.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        verify_password(password, _DUMMY_HASH)
        return None

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(UTC):
        return None

    # If lock has expired, reset counter
    if user.locked_until and user.locked_until <= datetime.now(UTC):
        user.failed_login_count = 0
        user.locked_until = None

    if not verify_password(password, user.hashed_password):
        user.failed_login_count += 1
        if user.failed_login_count >= 10:
            user.locked_until = datetime.now(UTC) + timedelta(hours=1)
        elif user.failed_login_count >= 5:
            user.locked_until = datetime.now(UTC) + timedelta(minutes=15)
        # COMMIT, not flush: a failed login ends with the endpoint raising
        # HTTPException(401), and get_db rolls the transaction back on any
        # exception. A flushed-only increment would be discarded every time, so
        # the lockout counter never accumulated and SEC-20 never triggered
        # (verified S161). The lockout counter is a security side-effect that
        # must persist independently of the request's failure path.
        await db.commit()
        return None

    # Successful login — reset lockout counter
    if user.failed_login_count > 0:
        user.failed_login_count = 0
        user.locked_until = None
        await db.flush()
    return user


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Fetch a user by their UUID."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email: str,
    password: str,
    full_name: str,
    role: str = "admin",
) -> User:
    """Create a new user in the given tenant. Raises ConflictError on duplicate email."""
    from app.auth.schemas import ROLES
    from app.shared.exceptions import BadRequestError, ConflictError

    if role not in ROLES:
        raise BadRequestError(f"Ongeldige rol: {role}. Kies uit: {', '.join(ROLES)}")

    # Check for duplicate email
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"E-mailadres '{email}' is al in gebruik")

    user = User(
        tenant_id=tenant_id,
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def create_password_reset_token(db: AsyncSession, email: str) -> str | None:
    """Generate a password reset token for the given email.

    Returns the token if the user exists, None otherwise.
    Caller should NOT reveal whether the email exists.
    """
    result = await db.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        return None

    token = str(uuid.uuid4())
    # Hash before storage — if DB is compromised, tokens can't be used
    user.password_reset_token = hashlib.sha256(token.encode()).hexdigest()
    user.password_reset_expires = datetime.now(UTC) + timedelta(hours=1)
    db.add(user)
    await db.flush()
    return token


async def reset_password_with_token(db: AsyncSession, token: str, new_password: str) -> bool:
    """Reset a user's password using a valid reset token.

    Returns True on success, False if token is invalid or expired.
    """
    # Hash the incoming token to compare with stored hash
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(select(User).where(User.password_reset_token == token_hash))
    user = result.scalar_one_or_none()
    if user is None:
        return False

    if user.password_reset_expires is None or user.password_reset_expires < datetime.now(UTC):
        return False

    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.add(user)
    # Resetting a password is the "I lost control of my account" path — kill all
    # existing sessions so a stolen 7-day refresh token cannot outlive the reset.
    await revoke_all_refresh_tokens(db, user.id)
    await db.flush()
    return True


# ── Refresh Token Rotation (SEC-12) ─────────────────────────────────────────


def _hash_token(token: str) -> str:
    """SHA-256 hash of a JWT for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def store_refresh_token(
    db: AsyncSession,
    token: str,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> None:
    """Store a refresh token hash in the database."""
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    rt = RefreshToken(
        user_id=user_id,
        tenant_id=tenant_id,
        token_hash=_hash_token(token),
        expires_at=expires_at,
    )
    db.add(rt)
    await db.flush()


async def rotate_refresh_token(
    db: AsyncSession,
    old_token: str,
) -> RefreshToken | None:
    """Validate and consume a refresh token for rotation.

    Returns the RefreshToken record if valid, None if not found/expired.
    Raises ValueError if token was already used (possible theft).

    SEC-26: het consumeren gebeurt ATOMAIR (``UPDATE ... WHERE is_used = false``).
    De oude opzet (SELECT → controleer is_used → UPDATE) had een TOCTOU-race: twee
    gelijktijdige requests met dezelfde token lazen allebei ``is_used = False`` en
    kregen allebei een nieuw tokenpaar — de hergebruik-detectie (SEC-12) werd zo
    omzeild en tokendiefstal bleef onzichtbaar. Nu wint alleen de eerste request de
    UPDATE; de tweede raakt 0 rijen en valt in de hergebruik-detectie hieronder.
    """
    token_hash = _hash_token(old_token)

    # Atomair claimen: alleen een nog-ongebruikte token wordt geconsumeerd.
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash, RefreshToken.is_used.is_(False))
        .values(is_used=True)
        .returning(RefreshToken.id, RefreshToken.user_id, RefreshToken.expires_at)
    )
    row = result.first()

    if row is None:
        # Niet geconsumeerd → token bestaat niet, óf was al gebruikt (hergebruik).
        existing = (
            await db.execute(
                select(RefreshToken.user_id, RefreshToken.is_used).where(
                    RefreshToken.token_hash == token_hash
                )
            )
        ).first()
        if existing is not None and existing.is_used:
            logger.warning(
                "Refresh token reuse detected for user %s — revoking all tokens",
                existing.user_id,
            )
            await revoke_all_refresh_tokens(db, existing.user_id)
            raise ValueError("Token reuse detected")
        return None

    # Verlopen? De token is nu geconsumeerd (onschadelijk — hij was toch onbruikbaar).
    if row.expires_at < datetime.now(UTC):
        return None

    await db.flush()
    # Contract: geef het geconsumeerde record terug (caller checkt alleen op None).
    return (
        await db.execute(select(RefreshToken).where(RefreshToken.id == row.id))
    ).scalar_one()


async def revoke_all_refresh_tokens(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> None:
    """Revoke all refresh tokens for a user (logout everywhere / theft detection)."""
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.is_used.is_(False))
        .values(is_used=True)
    )
    await db.flush()
