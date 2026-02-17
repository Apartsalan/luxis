"""Interest rates: global reference table (no tenant_id)

Revision ID: 005
Revises: 004
Create Date: 2026-02-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Interest rates — global reference table, NOT tenant-scoped
    op.create_table(
        "interest_rates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rate_type", sa.String(30), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("rate", sa.Numeric(6, 2), nullable=False),
        sa.Column("source", sa.String(255), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interest_rates_type", "interest_rates", ["rate_type"])
    op.create_index(
        "ix_interest_rates_type_date",
        "interest_rates",
        ["rate_type", "effective_from"],
    )


def downgrade() -> None:
    op.drop_table("interest_rates")
