"""Pipeline overhaul: step categories, verweer, case_step_history table

Adds step_category/debtor_type/is_terminal/is_hold_step to incasso_pipeline_steps.
Adds has_verweer/verweer_note/verweer_date to cases.
Creates case_step_history table for step audit trail.

Revision ID: s126a01
Revises: aud12408
Create Date: 2026-04-23

"""

import sqlalchemy as sa
from alembic import op

revision = "s126a01"
down_revision = "aud12408"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── IncassoPipelineStep: new columns ─────────────────────────────────
    op.add_column(
        "incasso_pipeline_steps",
        sa.Column(
            "step_category",
            sa.String(30),
            nullable=False,
            server_default="minnelijk",
        ),
    )
    op.add_column(
        "incasso_pipeline_steps",
        sa.Column(
            "debtor_type",
            sa.String(10),
            nullable=False,
            server_default="both",
        ),
    )
    op.add_column(
        "incasso_pipeline_steps",
        sa.Column(
            "is_terminal",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "incasso_pipeline_steps",
        sa.Column(
            "is_hold_step",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # ── Case: verweer columns ────────────────────────────────────────────
    op.add_column(
        "cases",
        sa.Column(
            "has_verweer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "cases",
        sa.Column("verweer_note", sa.Text(), nullable=True),
    )
    op.add_column(
        "cases",
        sa.Column("verweer_date", sa.Date(), nullable=True),
    )

    # ── CaseStepHistory table ────────────────────────────────────────────
    op.create_table(
        "case_step_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("step_id", sa.Uuid(), nullable=False),
        sa.Column(
            "entered_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "exited_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("triggered_by", sa.Uuid(), nullable=True),
        sa.Column(
            "trigger_type",
            sa.String(30),
            nullable=False,
            server_default="manual",
        ),
        sa.Column(
            "template_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "email_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["step_id"], ["incasso_pipeline_steps.id"]),
        sa.ForeignKeyConstraint(["triggered_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["generated_documents.id"]),
    )
    op.create_index(
        "ix_case_step_history_case_id",
        "case_step_history",
        ["case_id"],
    )
    op.create_index(
        "ix_case_step_history_tenant_case",
        "case_step_history",
        ["tenant_id", "case_id", "entered_at"],
    )

    # RLS policy for case_step_history
    op.execute(
        "ALTER TABLE case_step_history ENABLE ROW LEVEL SECURITY"
    )
    op.execute(
        "ALTER TABLE case_step_history FORCE ROW LEVEL SECURITY"
    )
    op.execute("""
        CREATE POLICY tenant_isolation_case_step_history
        ON case_step_history
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_case_step_history ON case_step_history")
    op.drop_index("ix_case_step_history_tenant_case", table_name="case_step_history")
    op.drop_index("ix_case_step_history_case_id", table_name="case_step_history")
    op.drop_table("case_step_history")

    op.drop_column("cases", "verweer_date")
    op.drop_column("cases", "verweer_note")
    op.drop_column("cases", "has_verweer")

    op.drop_column("incasso_pipeline_steps", "is_hold_step")
    op.drop_column("incasso_pipeline_steps", "is_terminal")
    op.drop_column("incasso_pipeline_steps", "debtor_type")
    op.drop_column("incasso_pipeline_steps", "step_category")
