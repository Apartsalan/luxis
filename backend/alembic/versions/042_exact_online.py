"""Exact Online integration tables.

Revision ID: 042_exact_online
Revises: 041_df12_expense_tax_type_file_id
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "042_exact_online"
down_revision = "041_df12_expense_tax_type_file_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exact_online_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("division_id", sa.Integer(), nullable=False),
        sa.Column("division_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("access_token_enc", sa.LargeBinary(), nullable=False),
        sa.Column("refresh_token_enc", sa.LargeBinary(), nullable=False),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("connected_email", sa.String(320), nullable=False, server_default=""),
        sa.Column("connected_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sales_journal_code", sa.String(10), nullable=True),
        sa.Column("bank_journal_code", sa.String(10), nullable=True),
        sa.Column("default_revenue_gl", sa.String(50), nullable=True),
        sa.Column("default_expense_gl", sa.String(50), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exact_online_connections_tenant_id", "exact_online_connections", ["tenant_id"])

    op.create_table(
        "exact_sync_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("exact_id", sa.String(50), nullable=False),
        sa.Column("exact_number", sa.String(50), nullable=True),
        sa.Column("sync_status", sa.String(20), nullable=False, server_default="synced"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exact_sync_log_tenant_id", "exact_sync_log", ["tenant_id"])
    op.create_index("ix_exact_sync_log_entity", "exact_sync_log", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_table("exact_sync_log")
    op.drop_table("exact_online_connections")
