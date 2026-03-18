"""DF-12: Add tax_type and file_id to expenses

Revision ID: 041_df12_expense
Revises: f05a42a3eeca
Create Date: 2026-03-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "041_df12_expense"
down_revision: Union[str, None] = "f05a42a3eeca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # DF-12: Tax type for Exact Online export
    op.add_column(
        "expenses",
        sa.Column("tax_type", sa.String(20), nullable=False, server_default="belast"),
    )
    # DF-12: Optional file attachment (bon/factuur)
    op.add_column(
        "expenses",
        sa.Column("file_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_expenses_file_id",
        "expenses",
        "case_files",
        ["file_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_expenses_file_id", "expenses", type_="foreignkey")
    op.drop_column("expenses", "file_id")
    op.drop_column("expenses", "tax_type")
