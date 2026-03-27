"""Incasso pipeline: pipeline steps table + incasso_step_id on cases.

Revision ID: 029_incasso_pipeline
Revises: 028_procesgegevens
"""

from alembic import op
import sqlalchemy as sa

revision = "029_incasso_pipeline"
down_revision = "028_procesgegevens"


def upgrade() -> None:
    # Create incasso_pipeline_steps table
    op.create_table(
        "incasso_pipeline_steps",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("min_wait_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("template_id", sa.Uuid(), nullable=True),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["document_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incasso_pipeline_steps_tenant_id", "incasso_pipeline_steps", ["tenant_id"])

    # Add incasso_step_id FK to cases table
    op.add_column("cases", sa.Column("incasso_step_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_cases_incasso_step_id",
        "cases",
        "incasso_pipeline_steps",
        ["incasso_step_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_cases_incasso_step_id", "cases", type_="foreignkey")
    op.drop_column("cases", "incasso_step_id")
    op.drop_index("ix_incasso_pipeline_steps_tenant_id", table_name="incasso_pipeline_steps")
    op.drop_table("incasso_pipeline_steps")
