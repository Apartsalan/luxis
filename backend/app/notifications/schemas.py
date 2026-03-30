import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Matches the frontend Notification interface exactly."""

    id: uuid.UUID
    type: str
    title: str
    message: str
    case_id: uuid.UUID | None = None
    case_number: str | None = None
    task_id: uuid.UUID | None = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationCreate(BaseModel):
    """Internal schema for creating notifications from service/scheduler."""

    type: str
    title: str
    message: str = ""
    case_id: uuid.UUID | None = None
    case_number: str | None = None
    task_id: uuid.UUID | None = None
