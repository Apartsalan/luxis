"""Add email template fields to incasso_pipeline_steps.

Revision ID: 035_pipeline_email_templates
Revises: 034_managed_templates
"""

import sqlalchemy as sa

from alembic import op

revision = "035_pipeline_email_templates"
down_revision = "034_managed_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "incasso_pipeline_steps",
        sa.Column("email_subject_template", sa.String(500), nullable=True),
    )
    op.add_column(
        "incasso_pipeline_steps",
        sa.Column("email_body_template", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("incasso_pipeline_steps", "email_body_template")
    op.drop_column("incasso_pipeline_steps", "email_subject_template")
