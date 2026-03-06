"""Authentication service — JWT creation, verification, and password hashing."""

import logging
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.config import settings

logger = logging.getLogger(__name__)


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
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: str, tenant_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Verify email + password and return the user if valid."""
    result = await db.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        return None
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
    role: str = "medewerker",
) -> User:
    """Create a new user in the given tenant. Raises ConflictError on duplicate email."""
    from app.auth.schemas import ROLES
    from app.shared.exceptions import BadRequestError, ConflictError

    if role not in ROLES:
        raise BadRequestError(
            f"Ongeldige rol: {role}. Kies uit: {', '.join(ROLES)}"
        )

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
    result = await db.execute(
        select(User).where(User.email == email, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    token = str(uuid.uuid4())
    user.password_reset_token = token
    user.password_reset_expires = datetime.now(UTC) + timedelta(hours=1)
    db.add(user)
    await db.flush()
    return token


async def reset_password_with_token(
    db: AsyncSession, token: str, new_password: str
) -> bool:
    """Reset a user's password using a valid reset token.

    Returns True on success, False if token is invalid or expired.
    """
    result = await db.execute(
        select(User).where(User.password_reset_token == token)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return False

    if user.password_reset_expires is None or user.password_reset_expires < datetime.now(UTC):
        return False

    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.add(user)
    await db.flush()
    return True
