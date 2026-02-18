"""Add btw_number, address, postal_code, city to tenants

Revision ID: 007
Revises: 006
Create Date: 2026-02-18
"""

from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("btw_number", sa.String(30), nullable=True))
    op.add_column("tenants", sa.Column("address", sa.String(255), nullable=True))
    op.add_column("tenants", sa.Column("postal_code", sa.String(10), nullable=True))
    op.add_column("tenants", sa.Column("city", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "city")
    op.drop_column("tenants", "postal_code")
    op.drop_column("tenants", "address")
    op.drop_column("tenants", "btw_number")
