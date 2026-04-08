"""trust account fields on tenant + SEPA export tracking on trust_transactions

Sessie 119 — derdengelden afronding stap 4: SEPA-export voor goedgekeurde
uitbetalingen vanaf de Stichting Derdengelden Rabobank-rekening.

Adds:
- tenants.trust_account_iban / trust_account_holder / trust_account_bic
  (separate from tenants.iban which is the firm's operating account)
- trust_transactions.sepa_exported_at / sepa_batch_id
  (tracks which approved disbursements have been included in a SEPA batch)

Revision ID: df119
Revises: df11802a
Create Date: 2026-04-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "df119"
down_revision: Union[str, None] = "df11802a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("trust_account_iban", sa.String(34), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("trust_account_holder", sa.String(255), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("trust_account_bic", sa.String(11), nullable=True),
    )

    op.add_column(
        "trust_transactions",
        sa.Column("sepa_exported_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "trust_transactions",
        sa.Column("sepa_batch_id", sa.Uuid(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("trust_transactions", "sepa_batch_id")
    op.drop_column("trust_transactions", "sepa_exported_at")
    op.drop_column("tenants", "trust_account_bic")
    op.drop_column("tenants", "trust_account_holder")
    op.drop_column("tenants", "trust_account_iban")
