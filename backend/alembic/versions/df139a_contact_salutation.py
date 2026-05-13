"""DF138-04: Aanhef-veld op contactpersoon (mr|mrs|unknown).

Lisanne demo: bij bekende aanhef (heer/mevrouw) → gebruik in mail-aanhef
met achternaam. Bij onbekend → generieke "Geachte heer/mevrouw,". Lost
gokwerk uit de AI-prompt op en voorkomt verkeerde aanhef.

Revision ID: df139a_salutation
Revises: df138a_bik_min
"""

import sqlalchemy as sa
from alembic import op

revision = "df139a_salutation"
down_revision = "df138a_bik_min"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "contacts",
        sa.Column(
            "salutation",
            sa.String(length=10),
            nullable=False,
            server_default="unknown",
        ),
    )


def downgrade() -> None:
    op.drop_column("contacts", "salutation")
