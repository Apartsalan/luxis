import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """A tenant represents a law firm in the system."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    kvk_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    btw_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    modules_enabled: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)),
        nullable=False,
        server_default="{}",
        default=list,
    )

    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")


class User(Base, TimestampMixin):
    """A user of the system, always belonging to a tenant."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Roles: admin, advocaat, medewerker
    role: Mapped[str] = mapped_column(String(50), default="medewerker")
    is_active: Mapped[bool] = mapped_column(default=True)
    default_hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    password_reset_token: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, default=None
    )
    password_reset_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    # SEC-20: Account lockout
    failed_login_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")


class RefreshToken(Base, TimestampMixin):
    """Stored refresh token hash for token rotation and theft detection.

    Flow:
    1. Login → create refresh token JWT + store SHA-256 hash here
    2. Refresh → find by hash, check is_used == False, mark as used, issue new pair
    3. Reuse detection → if is_used == True, reject + revoke all user tokens
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tenants.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )  # SHA-256 hex digest of the JWT
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
