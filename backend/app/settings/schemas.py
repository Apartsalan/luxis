"""Settings schemas — tenant profile and module configuration."""

import uuid

from pydantic import BaseModel, Field

VALID_MODULES = ("incasso", "tijdschrijven", "facturatie", "wwft", "budget")


class TenantSettingsResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    kvk_number: str | None = None
    btw_number: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    iban: str | None = None
    phone: str | None = None
    email: str | None = None
    modules_enabled: list[str] = []

    model_config = {"from_attributes": True}


class TenantSettingsUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    kvk_number: str | None = None
    btw_number: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    iban: str | None = None
    phone: str | None = None
    email: str | None = None
    modules_enabled: list[str] | None = None
