"""Add invoice_type and linked_invoice_id to invoices for credit notes.

Revision ID: 021_credit_notes
Revises: 020_calendar_events
Create Date: 2026-02-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "021_credit_notes"
down_revision: Union[str, None] = "020_calendar_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add invoice_type column with default "invoice" for existing rows
    op.add_column(
        "invoices",
        sa.Column(
            "invoice_type",
            sa.String(20),
            nullable=False,
            server_default="invoice",
        ),
    )

    # Add linked_invoice_id for credit notes
    op.add_column(
        "invoices",
        sa.Column(
            "linked_invoice_id",
            sa.Uuid(),
            sa.ForeignKey("invoices.id"),
            nullable=True,
        ),
    )

    # Index on linked_invoice_id for fast credit note lookups
    op.create_index(
        "ix_invoices_linked_invoice_id",
        "invoices",
        ["linked_invoice_id"],
    )

    # Index on invoice_type for filtering
    op.create_index(
        "ix_invoices_invoice_type",
        "invoices",
        ["invoice_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_invoices_invoice_type", table_name="invoices")
    op.drop_index("ix_invoices_linked_invoice_id", table_name="invoices")
    op.drop_column("invoices", "linked_invoice_id")
    op.drop_column("invoices", "invoice_type")
