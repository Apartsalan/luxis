"""Add ai_drafts table for persistent AI-generated email drafts

Revision ID: s129a01
Revises: s126a01
Create Date: 2026-04-28

"""

import sqlalchemy as sa
from alembic import op

revision = "s129a01"
down_revision = "s126a01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_drafts",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("case_id", sa.Uuid(), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("classification_id", sa.Uuid(), sa.ForeignKey("email_classifications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subject", sa.String(500), nullable=False, server_default=""),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("tone", sa.String(20), nullable=False, server_default="formeel"),
        sa.Column("sources", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="generated"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("model_used", sa.String(50), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("instruction", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ai_drafts_tenant_status", "ai_drafts", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_ai_drafts_tenant_status")
    op.drop_table("ai_drafts")
