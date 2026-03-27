"""add billable_minutes to time_entries

Revision ID: f05a42a3eeca
Revises: 4f94bea68ff4
Create Date: 2026-03-18 18:49:03.913689

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f05a42a3eeca"
down_revision: Union[str, None] = "4f94bea68ff4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "time_entries",
        sa.Column(
            "billable_minutes",
            sa.Integer(),
            nullable=True,
            comment="Te factureren minuten (null = gelijk aan duration_minutes)",
        ),
    )


def downgrade() -> None:
    op.drop_column("time_entries", "billable_minutes")
