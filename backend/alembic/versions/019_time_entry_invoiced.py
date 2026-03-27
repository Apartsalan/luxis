"""add invoiced field to time_entries

Revision ID: 019_time_entry_invoiced
Revises: 018_case_files
Create Date: 2026-02-20 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "019_time_entry_invoiced"
down_revision: Union[str, None] = "018_case_files"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add invoiced column with default false
    op.add_column(
        "time_entries",
        sa.Column("invoiced", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_time_entries_invoiced", "time_entries", ["invoiced"])

    # Data migration: mark time entries that are already on invoice lines
    op.execute("""
        UPDATE time_entries
        SET invoiced = true
        WHERE id IN (
            SELECT DISTINCT time_entry_id
            FROM invoice_lines
            WHERE time_entry_id IS NOT NULL
        )
    """)


def downgrade() -> None:
    op.drop_index("ix_time_entries_invoiced", table_name="time_entries")
    op.drop_column("time_entries", "invoiced")
