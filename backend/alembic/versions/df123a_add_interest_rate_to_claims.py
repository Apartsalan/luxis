"""add interest_rate to claims

DF122-06: optional per-claim rate override.
NULL = use case-level rate (wettelijk/commercial/etc).

Revision ID: df123a
Revises: df122a
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa


revision = "df123a"
down_revision = "df122a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "claims",
        sa.Column("interest_rate", sa.Numeric(5, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("claims", "interest_rate")
