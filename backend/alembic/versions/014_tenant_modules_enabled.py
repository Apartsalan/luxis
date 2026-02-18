"""Add modules_enabled array column to tenants table.

Allows per-tenant feature toggling: incasso, tijdschrijven, facturatie, etc.

Revision ID: 014
Revises: 013
Create Date: 2026-02-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "modules_enabled",
            ARRAY(sa.String(50)),
            nullable=False,
            server_default="{}",
        ),
    )
    # Enable incasso for all existing tenants (backward compatible)
    op.execute("UPDATE tenants SET modules_enabled = '{incasso}'")


def downgrade() -> None:
    op.drop_column("tenants", "modules_enabled")
