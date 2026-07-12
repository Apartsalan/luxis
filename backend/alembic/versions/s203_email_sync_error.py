"""S203 #1: last_sync_error op email_accounts.

Maakt een stil doodgegane e-mailsync zichtbaar. NULL = laatste sync geslaagd;
een tekst = de laatste sync-fout (bv. verlopen OAuth-token). email_accounts is
al een tenant-tabel met RLS; deze migratie voegt alleen een nullable kolom toe.

Revision ID: s203_email_sync_error
Revises: s199_cleanup_workflow_engine
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s203_email_sync_error"
down_revision: str | None = "s199_cleanup_workflow_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "email_accounts",
        sa.Column("last_sync_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("email_accounts", "last_sync_error")
