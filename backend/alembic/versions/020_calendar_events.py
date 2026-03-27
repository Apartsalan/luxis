"""add calendar_events table

Revision ID: 020_calendar_events
Revises: 019_time_entry_invoiced, b7e38c3f07cc
Create Date: 2026-02-20 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "020_calendar_events"
down_revision: Union[str, Sequence[str]] = (
    "019_time_entry_invoiced",
    "b7e38c3f07cc",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(30), nullable=False, server_default="appointment"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("all_day", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("case_id", sa.Uuid(), sa.ForeignKey("cases.id"), nullable=True),
        sa.Column("contact_id", sa.Uuid(), sa.ForeignKey("contacts.id"), nullable=True),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("reminder_minutes", sa.Integer(), nullable=True, server_default="30"),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("ix_calendar_events_start_time", "calendar_events", ["start_time"])
    op.create_index("ix_calendar_events_case_id", "calendar_events", ["case_id"])
    op.create_index("ix_calendar_events_created_by", "calendar_events", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_calendar_events_created_by", table_name="calendar_events")
    op.drop_index("ix_calendar_events_case_id", table_name="calendar_events")
    op.drop_index("ix_calendar_events_start_time", table_name="calendar_events")
    op.drop_table("calendar_events")
