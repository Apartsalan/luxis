"""Notifications table for in-app deadline/task/verjaring alerts.

Revision ID: 043_notifications
Revises: 042_exact_online
Create Date: 2026-03-30
"""

import sqlalchemy as sa
from alembic import op

revision = "043_notifications"
down_revision = "042_exact_online"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("case_id", sa.Uuid(), sa.ForeignKey("cases.id"), nullable=True),
        sa.Column("case_number", sa.String(50), nullable=True),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_notifications_user_unread",
        "notifications",
        ["tenant_id", "user_id", "is_read", "created_at"],
    )
    op.create_index(
        "ix_notifications_tenant_id",
        "notifications",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_tenant_id", table_name="notifications")
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_table("notifications")
