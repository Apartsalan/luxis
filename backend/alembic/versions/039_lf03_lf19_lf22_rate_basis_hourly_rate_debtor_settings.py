"""LF-03, LF-19, LF-22: rate_basis on claims, hourly_rate + debtor settings on cases

Revision ID: 039_lf03_lf19_lf22
Revises: 42aba19cd8b0
Create Date: 2026-03-16

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "039_lf03_lf19_lf22"
down_revision: Union[str, None] = "42aba19cd8b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # LF-03: rate_basis on claims (monthly/yearly, default yearly)
    op.add_column(
        "claims",
        sa.Column("rate_basis", sa.String(10), nullable=False, server_default="yearly"),
    )

    # LF-19: hourly_rate on cases (per-case override)
    op.add_column(
        "cases",
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=True),
    )

    # LF-22: debtor settings on cases
    op.add_column(
        "cases",
        sa.Column("payment_term_days", sa.Integer(), nullable=True),
    )
    op.add_column(
        "cases",
        sa.Column("collection_strategy", sa.String(50), nullable=True),
    )
    op.add_column(
        "cases",
        sa.Column("debtor_notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "debtor_notes")
    op.drop_column("cases", "collection_strategy")
    op.drop_column("cases", "payment_term_days")
    op.drop_column("cases", "hourly_rate")
    op.drop_column("claims", "rate_basis")
