"""Email attachments table — stores files downloaded from synced emails.

Revision ID: 026_email_attachments
Revises: 025_synced_emails
Create Date: 2026-02-21
"""

from alembic import op
import sqlalchemy as sa

revision = "026_email_attachments"
down_revision = "025_synced_emails"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_attachments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column(
            "synced_email_id",
            sa.Uuid(),
            sa.ForeignKey("synced_emails.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider_attachment_id", sa.String(500), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("stored_filename", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(200), nullable=False, server_default="application/octet-stream"),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=False),
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
    )


def downgrade() -> None:
    op.drop_table("email_attachments")
