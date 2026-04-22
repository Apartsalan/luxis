"""add nakosten_type to cases

AUD124-03: Post-judgment costs (nakosten).
- zonder_betekening = €189
- met_betekening = €287
Default NULL (no nakosten until set).

Revision ID: aud12403
Revises: aud12401
Create Date: 2026-04-22
"""

from alembic import op
import sqlalchemy as sa


revision = "aud12403"
down_revision = "aud12401"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("nakosten_type", sa.String(30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "nakosten_type")
