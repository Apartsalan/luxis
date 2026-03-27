"""add matched_by and is_bounce to synced_emails

Revision ID: 7e3f01a2b9c4
Revises: 466aa6937a91
Create Date: 2026-03-23

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "7e3f01a2b9c4"
down_revision: Union[str, None] = "466aa6937a91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "synced_emails",
        sa.Column("is_bounce", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "synced_emails",
        sa.Column("matched_by", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("synced_emails", "matched_by")
    op.drop_column("synced_emails", "is_bounce")
