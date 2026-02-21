"""M1: email_accounts table for OAuth-connected email providers.

Revision ID: 024_email_accounts
Revises: 023_billing_and_billing_cntct
Create Date: 2026-02-21
"""

from alembic import op
import sqlalchemy as sa

revision = "024_email_accounts"
down_revision = "023_billing_and_billing_cntct"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("email_address", sa.String(320), nullable=False),
        sa.Column("access_token_enc", sa.LargeBinary(), nullable=False),
        sa.Column("refresh_token_enc", sa.LargeBinary(), nullable=False),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_cursor", sa.Text(), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # One account per user per provider
        sa.UniqueConstraint("tenant_id", "user_id", "provider", name="uq_email_account_user_provider"),
    )


def downgrade() -> None:
    op.drop_table("email_accounts")
