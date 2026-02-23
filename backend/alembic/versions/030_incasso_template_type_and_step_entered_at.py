"""Add template_type to incasso_pipeline_steps and step_entered_at to cases.

Revision ID: 030_incasso_template_type
Revises: 029_incasso_pipeline
"""

from alembic import op
import sqlalchemy as sa

revision = "030_incasso_template_type"
down_revision = "029_incasso_pipeline"


def upgrade() -> None:
    # Add template_type string field to pipeline steps (modern docx system)
    op.add_column(
        "incasso_pipeline_steps",
        sa.Column("template_type", sa.String(50), nullable=True),
    )

    # Add step_entered_at timestamp to cases (tracks when case entered current step)
    op.add_column(
        "cases",
        sa.Column("step_entered_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "step_entered_at")
    op.drop_column("incasso_pipeline_steps", "template_type")
