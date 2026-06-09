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
    trust_account_iban: str | None = None
    trust_account_holder: str | None = None
    trust_account_bic: str | None = None
    trust_allow_self_approval: bool = True
    phone: str | None = None
    email: str | None = None
    modules_enabled: list[str] = []
    pipeline_auto_drafts_enabled: bool = False

    model_config = {"from_attributes": True}


class TenantSettingsUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    kvk_number: str | None = None
    btw_number: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    iban: str | None = None
    trust_account_iban: str | None = None
    trust_account_holder: str | None = None
    trust_account_bic: str | None = None
    trust_allow_self_approval: bool | None = None
    phone: str | None = None
    email: str | None = None
    modules_enabled: list[str] | None = None
    pipeline_auto_drafts_enabled: bool | None = None
