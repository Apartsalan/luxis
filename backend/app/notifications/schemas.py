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
    snoozed_until: datetime | None = None
    created_at: datetime
    # S241-bundeling: gezet op een bundel-rij in de bel (grouped=true) — het
    # aantal ongelezen meldingen van dit type dat deze rij vertegenwoordigt.
    # None = gewone losse melding.
    bundle_count: int | None = None

    model_config = {"from_attributes": True}


class NotificationCreate(BaseModel):
    """Internal schema for creating notifications from service/scheduler."""

    type: str
    title: str
    message: str = ""
    case_id: uuid.UUID | None = None
    case_number: str | None = None
    task_id: uuid.UUID | None = None
