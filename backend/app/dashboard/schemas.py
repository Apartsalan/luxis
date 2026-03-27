"""Dashboard module schemas — response models for KPIs and activity."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CaseStatusCount(BaseModel):
    """Count of cases per status."""

    status: str
    count: int


class CaseTypeCount(BaseModel):
    """Count of cases per type."""

    case_type: str
    count: int


class DashboardSummary(BaseModel):
    """Main dashboard KPI summary."""

    total_active_cases: int
    total_contacts: int
    total_outstanding: Decimal  # Sum of all open cases' outstanding amounts
    total_principal: Decimal
    total_paid: Decimal
    cases_by_status: list[CaseStatusCount]
    cases_by_type: list[CaseTypeCount]
    cases_this_month: int
    cases_closed_this_month: int
    contacts_this_month: int


class RecentActivityItem(BaseModel):
    """A single recent activity for the dashboard feed."""

    id: uuid.UUID
    case_id: uuid.UUID
    case_number: str
    activity_type: str
    title: str
    description: str | None
    user_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecentActivityResponse(BaseModel):
    """Response for the recent activity feed."""

    items: list[RecentActivityItem]
    total: int
