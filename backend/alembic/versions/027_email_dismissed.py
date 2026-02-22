"""Add is_dismissed to synced_emails for M6 ongesorteerd queue.

Revision ID: 027_email_dismissed
Revises: 026_email_attachments
Create Date: 2026-02-22
"""

from alembic import op
import sqlalchemy as sa

revision = "027_email_dismissed"
down_revision = "026_email_attachments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "synced_emails",
        sa.Column("is_dismissed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    # Partial index for efficient unlinked-and-not-dismissed queries
    op.create_index(
        "ix_synced_emails_unlinked_active",
        "synced_emails",
        ["tenant_id"],
        postgresql_where=sa.text("case_id IS NULL AND is_dismissed = false"),
    )


def downgrade() -> None:
    op.drop_index("ix_synced_emails_unlinked_active", table_name="synced_emails")
    op.drop_column("synced_emails", "is_dismissed")
