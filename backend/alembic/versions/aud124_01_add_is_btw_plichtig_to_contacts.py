"""add is_btw_plichtig to contacts

AUD124-01: BTW-on-BIK for non-VAT-exempt clients.
Default True (most clients are BV's that can deduct BTW).

Revision ID: aud12401
Revises: df123a
Create Date: 2026-04-22
"""

from alembic import op
import sqlalchemy as sa


revision = "aud12401"
down_revision = "df123a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "contacts",
        sa.Column(
            "is_btw_plichtig",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("contacts", "is_btw_plichtig")
