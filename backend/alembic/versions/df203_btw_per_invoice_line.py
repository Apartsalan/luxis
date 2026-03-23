"""DF2-03: Add btw_percentage to invoice_lines for per-line VAT.

Backfills existing lines with their parent invoice's btw_percentage.
"""

from alembic import op
import sqlalchemy as sa

revision = "df203_btw_per_line"
down_revision = None  # Non-linear; run after latest
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add btw_percentage column with default 21.00
    op.add_column(
        "invoice_lines",
        sa.Column(
            "btw_percentage",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="21.00",
        ),
    )

    # Backfill from parent invoice's btw_percentage
    op.execute(
        """
        UPDATE invoice_lines
        SET btw_percentage = invoices.btw_percentage
        FROM invoices
        WHERE invoice_lines.invoice_id = invoices.id
        """
    )


def downgrade() -> None:
    op.drop_column("invoice_lines", "btw_percentage")
