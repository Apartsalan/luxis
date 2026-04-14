"""Products module schemas — Pydantic models for product catalog."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    default_price: Decimal | None = Field(None, ge=0, decimal_places=2)
    gl_account_code: str = Field(..., min_length=1, max_length=20)
    gl_account_name: str = Field(..., min_length=1, max_length=200)
    vat_type: str = Field(default="21", description="21, 0, eu, non_eu")
    vat_percentage: Decimal = Field(default=Decimal("21.00"), ge=0)
    is_active: bool = True
    sort_order: int = 0


class ProductUpdate(BaseModel):
    code: str | None = Field(None, min_length=1, max_length=20)
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    default_price: Decimal | None = Field(None, ge=0, decimal_places=2)
    gl_account_code: str | None = Field(None, min_length=1, max_length=20)
    gl_account_name: str | None = Field(None, min_length=1, max_length=200)
    vat_type: str | None = None
    vat_percentage: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None
    sort_order: int | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None
    default_price: Decimal | None
    gl_account_code: str
    gl_account_name: str
    vat_type: str
    vat_percentage: Decimal
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductBrief(BaseModel):
    """Lightweight product for dropdowns."""

    id: uuid.UUID
    code: str
    name: str
    default_price: Decimal | None
    vat_type: str
    vat_percentage: Decimal
    gl_account_code: str

    model_config = {"from_attributes": True}
