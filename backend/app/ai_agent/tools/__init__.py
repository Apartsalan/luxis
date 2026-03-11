"""AI Agent Tool Layer — tools that wrap existing Luxis services for Claude tool use."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def serialize(value: Any) -> Any:
    """Recursively serialize a value to JSON-safe types.

    - UUID -> str
    - date/datetime -> ISO string
    - Decimal -> str (preserves financial precision)
    - SQLAlchemy models -> skipped (use explicit dicts)
    - dicts/lists -> recursed
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(item) for item in value]
    # For Pydantic models
    if hasattr(value, "model_dump"):
        return serialize(value.model_dump())
    # Fallback
    return str(value)
