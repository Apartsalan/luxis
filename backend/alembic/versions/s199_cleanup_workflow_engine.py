"""S199: drop the unused workflow status engine.

Revision ID: s199_cleanup_workflow_engine
Revises: s199_powersearch
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s199_cleanup_workflow_engine"
down_revision: str | None = "s199_powersearch"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    obsolete_tables = (
        "workflow_statuses",
        "workflow_transitions",
        "workflow_rules",
    )

    # Fail closed: S197 measured these tables as empty in production. Never
    # discard configured workflow data silently if an environment has drifted.
    counts = {
        table: bind.execute(sa.text(f"SELECT count(*) FROM {table}")).scalar_one()
        for table in obsolete_tables
    }
    non_empty = {table: count for table, count in counts.items() if count != 0}
    if non_empty:
        details = ", ".join(f"{table}={count}" for table, count in non_empty.items())
        raise RuntimeError(f"Refusing to drop non-empty workflow tables: {details}")

    # The live task table stays. Only its dead rule provenance column must go
    # before workflow_rules can be dropped.
    op.drop_column("workflow_tasks", "created_by_rule_id")
    op.drop_table("workflow_rules")
    op.drop_table("workflow_transitions")
    op.drop_table("workflow_statuses")


def downgrade() -> None:
    # The removed engine was unused and its guarded source tables were empty;
    # recreating a second source of truth would reintroduce the defect.
    pass
