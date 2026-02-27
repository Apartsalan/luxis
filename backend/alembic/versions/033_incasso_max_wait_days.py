"""Add max_wait_days to incasso_pipeline_steps for deadline color coding.

Revision ID: 033_incasso_max_wait_days
Revises: 032_recurring_tasks
"""

from alembic import op
import sqlalchemy as sa

revision = "033_incasso_max_wait_days"
down_revision = "032_recurring_tasks"


def upgrade() -> None:
    op.add_column(
        "incasso_pipeline_steps",
        sa.Column(
            "max_wait_days",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("incasso_pipeline_steps", "max_wait_days")
