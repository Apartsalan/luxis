"""CQ-3: contacts.default_hourly_rate Float → Numeric(10,2)

Revision ID: cq3_float_to_numeric
Revises: df13_settlement_type
Create Date: 2026-03-20

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cq3_float_to_numeric"
down_revision: Union[str, None] = "df13_settlement_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "contacts",
        "default_hourly_rate",
        existing_type=sa.Float(),
        type_=sa.Numeric(10, 2),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "contacts",
        "default_hourly_rate",
        existing_type=sa.Numeric(10, 2),
        type_=sa.Float(),
        existing_nullable=True,
    )
