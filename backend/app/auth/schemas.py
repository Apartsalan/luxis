import uuid

from pydantic import BaseModel, Field

ROLES = ("admin", "advocaat", "medewerker")


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="medewerker", description="admin, advocaat, or medewerker")


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

    model_config = {"from_attributes": True}


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    kvk_number: str | None

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


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
