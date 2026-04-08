"""trust_funds offset/consent fields + transaction_date

Sessie 118 — DF117-21 stap 2: extend TrustTransaction for verrekening (offset
to invoice) + per-transaction client consent (Voda art. 6.19 lid 5).

Adds:
- transaction_date (date the funds moved — distinct from created_at)
- target_invoice_id (FK to invoices, only set when type=offset_to_invoice)
- consent_received_at, consent_method, consent_document_url, consent_note
- reversed_by_id (self-FK for reversal/correction entries)

Also widens transaction_type from String(20) to String(30) so 'offset_to_invoice'
fits.

Revision ID: df11802a
Revises: df11801a
Create Date: 2026-04-08 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "df11802a"
down_revision: Union[str, None] = "df11801a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Widen transaction_type column for the new 'offset_to_invoice' value
    op.alter_column(
        "trust_transactions",
        "transaction_type",
        existing_type=sa.String(length=20),
        type_=sa.String(length=30),
        existing_nullable=False,
    )

    # Backfill-friendly add: transaction_date defaults to created_at::date for
    # existing rows, then we'll keep nullable=False going forward.
    op.add_column(
        "trust_transactions",
        sa.Column("transaction_date", sa.Date(), nullable=True),
    )
    op.execute(
        "UPDATE trust_transactions SET transaction_date = created_at::date "
        "WHERE transaction_date IS NULL"
    )
    op.alter_column(
        "trust_transactions",
        "transaction_date",
        existing_type=sa.Date(),
        nullable=False,
    )

    # Offset / consent columns
    op.add_column(
        "trust_transactions",
        sa.Column("target_invoice_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_trust_transactions_target_invoice_id",
        "trust_transactions",
        "invoices",
        ["target_invoice_id"],
        ["id"],
    )
    op.add_column(
        "trust_transactions",
        sa.Column("consent_received_at", sa.Date(), nullable=True),
    )
    op.add_column(
        "trust_transactions",
        sa.Column("consent_method", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "trust_transactions",
        sa.Column("consent_document_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "trust_transactions",
        sa.Column("consent_note", sa.Text(), nullable=True),
    )

    # Reversal self-FK
    op.add_column(
        "trust_transactions",
        sa.Column("reversed_by_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_trust_transactions_reversed_by_id",
        "trust_transactions",
        "trust_transactions",
        ["reversed_by_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_trust_transactions_reversed_by_id", "trust_transactions", type_="foreignkey"
    )
    op.drop_column("trust_transactions", "reversed_by_id")
    op.drop_column("trust_transactions", "consent_note")
    op.drop_column("trust_transactions", "consent_document_url")
    op.drop_column("trust_transactions", "consent_method")
    op.drop_column("trust_transactions", "consent_received_at")
    op.drop_constraint(
        "fk_trust_transactions_target_invoice_id", "trust_transactions", type_="foreignkey"
    )
    op.drop_column("trust_transactions", "target_invoice_id")
    op.drop_column("trust_transactions", "transaction_date")
    op.alter_column(
        "trust_transactions",
        "transaction_type",
        existing_type=sa.String(length=30),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
