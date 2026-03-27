"""Add intake_requests table for AI dossier intake.

Revision ID: 037_intake_requests
Revises: 036_ai_email_classification
"""

import sqlalchemy as sa

from alembic import op

revision = "037_intake_requests"
down_revision = "036_ai_email_classification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intake_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        # Source email
        sa.Column(
            "synced_email_id",
            sa.Uuid(),
            sa.ForeignKey("synced_emails.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # Extracted debtor info
        sa.Column("debtor_name", sa.String(255), nullable=True),
        sa.Column("debtor_email", sa.String(320), nullable=True),
        sa.Column("debtor_kvk", sa.String(20), nullable=True),
        sa.Column("debtor_address", sa.String(500), nullable=True),
        sa.Column("debtor_city", sa.String(255), nullable=True),
        sa.Column("debtor_postcode", sa.String(10), nullable=True),
        sa.Column(
            "debtor_type", sa.String(20), nullable=False, server_default=sa.text("'company'")
        ),
        # Extracted invoice/claim info
        sa.Column("invoice_number", sa.String(100), nullable=True),
        sa.Column("invoice_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("principal_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        # Client reference
        sa.Column("client_contact_id", sa.Uuid(), sa.ForeignKey("contacts.id"), nullable=True),
        # AI metadata
        sa.Column("ai_model", sa.String(50), nullable=False, server_default=sa.text("''")),
        sa.Column("ai_confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("ai_reasoning", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("raw_extraction", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("has_pdf_data", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        # Status
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'detected'"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Review
        sa.Column("reviewed_by_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        # Result
        sa.Column("created_case_id", sa.Uuid(), sa.ForeignKey("cases.id"), nullable=True),
        sa.Column("created_contact_id", sa.Uuid(), sa.ForeignKey("contacts.id"), nullable=True),
        # Timestamps
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
    op.create_index("ix_intake_requests_status", "intake_requests", ["status"])


def downgrade() -> None:
    op.drop_table("intake_requests")
