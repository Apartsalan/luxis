import re
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

ROLES = ("admin", "advocaat", "medewerker")


class LoginRequest(BaseModel):
    email: str
    password: str


def _validate_password_complexity(password: str) -> str:
    """Enforce password complexity: min 12 chars, 1 uppercase, 1 digit."""
    if len(password) < 12:
        raise ValueError("Wachtwoord moet minimaal 12 tekens bevatten")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Wachtwoord moet minimaal 1 hoofdletter bevatten")
    if not re.search(r"[0-9]", password):
        raise ValueError("Wachtwoord moet minimaal 1 cijfer bevatten")
    return password


class RegisterRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=12)
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="medewerker", description="admin, advocaat, or medewerker")

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _validate_password_complexity(v)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    tenant_id: uuid.UUID
    is_active: bool
    default_hourly_rate: Decimal | None = None

    model_config = {"from_attributes": True}


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    kvk_number: str | None

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    default_hourly_rate: Decimal | None = Field(None, ge=0, decimal_places=2)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _validate_password_complexity(v)


class TenantUpdateRequest(BaseModel):
    name: str | None = None
    kvk_number: str | None = None
    btw_number: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    iban: str | None = None
    phone: str | None = None
    email: str | None = None
    modules_enabled: list[str] | None = None


class ForgotPasswordRequest(BaseModel):
    email: str = Field(max_length=320)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=12)

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _validate_password_complexity(v)


class TenantDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    kvk_number: str | None
    btw_number: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    iban: str | None = None
    phone: str | None = None
    email: str | None = None
    modules_enabled: list[str] = []

    model_config = {"from_attributes": True}
