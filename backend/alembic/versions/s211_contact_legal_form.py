"""S211: legal_form (+ herkomst) op contacts — rechtsvorm uit KvK-basisprofiel.

Bepaalt of het renteoverzicht als PDF-bijlage bij de 14-dagenbrief/eerste
sommatie meegaat: bij een privé aansprakelijke wederpartij (particulier,
eenmanszaak, VOF, maatschap, CV) wél, bij een BV/NV/stichting/coöperatie niet.
De rechtsvorm wordt uit de KvK gehaald bij het aanmaken/bijwerken van een
relatie met KvK-nummer en opgeslagen, zodat het verzendpad nooit live de KvK
hoeft te raadplegen. Puur additief (nullable); contacts heeft al RLS, dus de
nieuwe kolommen vallen automatisch onder de bestaande policy.

Revision ID: s211_contact_legal_form
Revises: s210_contact_provisie
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s211_contact_legal_form"
down_revision: str | None = "s210_contact_provisie"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("legal_form", sa.String(100), nullable=True))
    op.add_column("contacts", sa.Column("legal_form_source", sa.String(20), nullable=True))
    op.add_column(
        "contacts",
        sa.Column("legal_form_checked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("contacts", "legal_form_checked_at")
    op.drop_column("contacts", "legal_form_source")
    op.drop_column("contacts", "legal_form")
