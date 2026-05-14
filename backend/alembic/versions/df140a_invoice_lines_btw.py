"""DF140a: voeg btw_percentage kolom toe aan invoice_lines.

Het InvoiceLine model declareert `btw_percentage NUMERIC(5,2) NOT NULL` als
per-line VAT (DF2-03), maar er bestond geen Alembic-migratie die deze kolom
daadwerkelijk in de DB aanmaakte. Gevolg: GET en POST /api/invoices geven 500
met UndefinedColumnError. E2E specs F2 (create invoice via form) en F7 (delete)
waren hierdoor geblokkeerd.

Deze migratie voegt de kolom toe met default 21.00 (NL standaard-BTW) voor
bestaande rijen.

Revision ID: df140a_invoice_lines_btw
Revises: df139b_contact_terms
"""

import sqlalchemy as sa
from alembic import op

revision = "df140a_invoice_lines_btw"
down_revision = "df139b_contact_terms"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "invoice_lines",
        sa.Column(
            "btw_percentage",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="21.00",
        ),
    )


def downgrade() -> None:
    op.drop_column("invoice_lines", "btw_percentage")
