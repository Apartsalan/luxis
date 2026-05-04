"""Add step_transitions table for branching workflow configuration.

Revision ID: s131a01
Revises: s129a01
Create Date: 2026-05-04

"""

import sqlalchemy as sa
from alembic import op

revision = "s131a01"
down_revision = "s129a01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "step_transitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("from_step_id", sa.Uuid(), nullable=False),
        sa.Column("to_step_id", sa.Uuid(), nullable=False),
        sa.Column("trigger_type", sa.String(30), nullable=False),
        sa.Column("condition", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["from_step_id"], ["incasso_pipeline_steps.id"]),
        sa.ForeignKeyConstraint(["to_step_id"], ["incasso_pipeline_steps.id"]),
    )
    op.create_index(
        "ix_step_transitions_tenant_id", "step_transitions", ["tenant_id"]
    )
    op.create_index(
        "ix_step_transitions_from_step",
        "step_transitions",
        ["tenant_id", "from_step_id"],
    )

    op.execute("ALTER TABLE step_transitions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE step_transitions FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_step_transitions
        ON step_transitions
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS tenant_isolation_step_transitions ON step_transitions"
    )
    op.drop_index("ix_step_transitions_from_step", table_name="step_transitions")
    op.drop_index("ix_step_transitions_tenant_id", table_name="step_transitions")
    op.drop_table("step_transitions")
