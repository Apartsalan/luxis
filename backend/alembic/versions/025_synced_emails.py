"""M2: synced_emails table for inbox sync from Gmail/Outlook.

Revision ID: 025_synced_emails
Revises: 024_email_accounts
Create Date: 2026-02-21
"""

from alembic import op
import sqlalchemy as sa

revision = "025_synced_emails"
down_revision = "024_email_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "synced_emails",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column(
            "email_account_id",
            sa.Uuid(),
            sa.ForeignKey("email_accounts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("case_id", sa.Uuid(), sa.ForeignKey("cases.id"), nullable=True, index=True),
        sa.Column("provider_message_id", sa.String(255), nullable=False, index=True),
        sa.Column("provider_thread_id", sa.String(255), nullable=True),
        sa.Column("subject", sa.String(1000), nullable=False, server_default=""),
        sa.Column("from_email", sa.String(320), nullable=False),
        sa.Column("from_name", sa.String(200), nullable=False, server_default=""),
        sa.Column("to_emails", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("cc_emails", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("snippet", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_html", sa.Text(), nullable=False, server_default=""),
        sa.Column("direction", sa.String(10), nullable=False, server_default="inbound"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("has_attachments", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("email_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
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
        # Prevent duplicate syncs of same message
        sa.UniqueConstraint(
            "email_account_id", "provider_message_id", name="uq_synced_email_provider_msg"
        ),
    )
    # Index for fast lookup by case
    op.create_index("ix_synced_emails_case_date", "synced_emails", ["case_id", "email_date"])
    # Index for finding unlinked emails
    op.create_index(
        "ix_synced_emails_unlinked",
        "synced_emails",
        ["tenant_id", "case_id"],
        postgresql_where=sa.text("case_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_synced_emails_unlinked")
    op.drop_index("ix_synced_emails_case_date")
    op.drop_table("synced_emails")
