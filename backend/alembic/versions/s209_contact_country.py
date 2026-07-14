"""S209: visit_country + postal_country op contacts — land bij adressen.

BaseNet vulde het land bij ~49 niet-Nederlandse relaties; Luxis-adressen kenden
alleen straat/postcode/plaats. Deze migratie voegt een land-veld toe bij het
bezoek- en postadres. Puur additief (nullable); contacts heeft al RLS, dus de
nieuwe kolommen vallen automatisch onder de bestaande policy — geen apply_rls
nodig. Backfill van de landen gebeurt ná deze migratie uit de export.

Revision ID: s209_contact_country
Revises: s207d_basenet_origin_phase
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s209_contact_country"
down_revision: str | None = "s207d_basenet_origin_phase"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "contacts",
        sa.Column("visit_country", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "contacts",
        sa.Column("postal_country", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("contacts", "postal_country")
    op.drop_column("contacts", "visit_country")
