"""Add budget column to cases (G13: Budget tracking).

Revision ID: 031_add_budget
Revises: 030_incasso_template_type
"""

from alembic import op
import sqlalchemy as sa

revision = "031_add_budget"
down_revision = "030_incasso_template_type"


def upgrade() -> None:
    op.add_column("cases", sa.Column("budget", sa.Numeric(15, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("cases", "budget")
