"""contact default_rate_basis + default_minimum_fee

Sessie 120 — DF120: Lisanne demo 2026-04-08 feedback extensions for the
DF117-02 (interest inheritance) and DF117-22 (collection fee inheritance)
patterns. Adds two new defaultable fields on Contact that cascade to
new cases/claims created for that client.

- default_rate_basis ("yearly" | "monthly") — inherited at claim creation
- default_minimum_fee (NUMERIC 15,2) — inherited at case creation

Revision ID: df120a
Revises: df119
Create Date: 2026-04-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "df120a"
down_revision: Union[str, None] = "df119"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "contacts",
        sa.Column("default_rate_basis", sa.String(10), nullable=True),
    )
    op.add_column(
        "contacts",
        sa.Column("default_minimum_fee", sa.Numeric(15, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("contacts", "default_minimum_fee")
    op.drop_column("contacts", "default_rate_basis")
