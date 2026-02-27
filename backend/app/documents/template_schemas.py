"""Pydantic schemas for managed DOCX templates."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ManagedTemplateResponse(BaseModel):
    """Full managed template response."""

    id: uuid.UUID
    name: str
    description: str | None
    template_key: str
    original_filename: str
    file_size: int
    is_builtin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ManagedTemplateUpdate(BaseModel):
    """Update metadata for a managed template."""

    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    template_key: str | None = Field(default=None, max_length=50)
