"""Add AI email classification and response templates tables.

Revision ID: 036_ai_email_classification
Revises: 035_pipeline_email_templates
"""

import sqlalchemy as sa

from alembic import op

revision = "036_ai_email_classification"
down_revision = "035_pipeline_email_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Response templates — reusable email templates selected by the AI
    op.create_table(
        "response_templates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("key", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("subject_template", sa.String(500), nullable=False),
        sa.Column("body_template", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
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
        sa.UniqueConstraint("tenant_id", "key", name="uq_response_templates_tenant_key"),
    )

    # Email classifications — AI analysis of inbound debtor emails
    op.create_table(
        "email_classifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column(
            "synced_email_id",
            sa.Uuid(),
            sa.ForeignKey("synced_emails.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "case_id",
            sa.Uuid(),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Classification result
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False, server_default=sa.text("''")),
        # Suggested action
        sa.Column("suggested_action", sa.String(50), nullable=False),
        sa.Column("suggested_template_key", sa.String(50), nullable=True),
        sa.Column("suggested_reminder_days", sa.Integer(), nullable=True),
        # Human review
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("reviewed_by_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        # Execution
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_result", sa.Text(), nullable=True),
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
    op.create_index("ix_email_classifications_status", "email_classifications", ["status"])


def downgrade() -> None:
    op.drop_table("email_classifications")
    op.drop_table("response_templates")
