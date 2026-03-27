"""add billing method fields to cases

Revision ID: 4f94bea68ff4
Revises: 2e1747ba61ca
Create Date: 2026-03-16 14:10:21.325565

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f94bea68ff4"
down_revision: Union[str, None] = "2e1747ba61ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("billing_method", sa.String(length=20), server_default="hourly", nullable=False),
    )
    op.add_column(
        "cases", sa.Column("fixed_price_amount", sa.Numeric(precision=15, scale=2), nullable=True)
    )
    op.add_column(
        "cases", sa.Column("budget_hours", sa.Numeric(precision=10, scale=2), nullable=True)
    )
    op.add_column(
        "cases", sa.Column("provisie_percentage", sa.Numeric(precision=5, scale=2), nullable=True)
    )
    op.add_column(
        "cases", sa.Column("fixed_case_costs", sa.Numeric(precision=15, scale=2), nullable=True)
    )
    op.add_column(
        "cases", sa.Column("minimum_fee", sa.Numeric(precision=15, scale=2), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("cases", "minimum_fee")
    op.drop_column("cases", "fixed_case_costs")
    op.drop_column("cases", "provisie_percentage")
    op.drop_column("cases", "budget_hours")
    op.drop_column("cases", "fixed_price_amount")
    op.drop_column("cases", "billing_method")
