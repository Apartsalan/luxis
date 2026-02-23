"""Add recurring task fields to workflow_tasks (G9: Recurring tasks).

Revision ID: 032_recurring_tasks
Revises: 031_add_budget
"""

from alembic import op
import sqlalchemy as sa

revision = "032_recurring_tasks"
down_revision = "031_add_budget"


def upgrade() -> None:
    op.add_column(
        "workflow_tasks",
        sa.Column("recurrence", sa.String(20), nullable=True),
    )
    op.add_column(
        "workflow_tasks",
        sa.Column("recurrence_end_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "workflow_tasks",
        sa.Column(
            "parent_task_id",
            sa.Uuid(),
            sa.ForeignKey("workflow_tasks.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("workflow_tasks", "parent_task_id")
    op.drop_column("workflow_tasks", "recurrence_end_date")
    op.drop_column("workflow_tasks", "recurrence")
