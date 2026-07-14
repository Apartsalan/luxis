"""S214: invoice_payments.payment_date nullable — historische BaseNet-import.

Van 305 historische kantoorbetalingen is alleen het bedrag bewezen (via de
memoriaal-afletering), niet de werkelijke ontvangstdatum. Die betalingen krijgen
`payment_date = NULL` → de UI toont "Datum onbekend" in plaats van een verzonnen
datum. Handmatige invoer blijft via `InvoicePaymentCreate` een datum vereisen.

Puur een nullability-verruiming; invoice_payments heeft al RLS.

Revision ID: s214_payment_date_null
Revises: s211_contact_legal_form
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s214_payment_date_null"
down_revision: str | None = "s211_contact_legal_form"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "invoice_payments", "payment_date", existing_type=sa.Date(), nullable=True
    )


def downgrade() -> None:
    # Alleen terugdraaibaar als er geen NULL-datums staan (historische import).
    op.alter_column(
        "invoice_payments", "payment_date", existing_type=sa.Date(), nullable=False
    )
