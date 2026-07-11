"""S197: globale app_config-tabel met het schakelbare mailslot.

Verplaatst het bouwfase-mailslot van een env-var naar een DB-vlag die vanuit
Instellingen aan/uit kan. Fail-safe: één rij geseed op DICHT (True), zodat
productie na deploy nog steeds op slot staat. Het env-noodslot
(OUTBOUND_MAIL_LOCK) blijft als extra harde override bestaan in
check_outbound_lock — pas als dat eraf gaat, neemt de UI-knop het over.

Geen tenant_id -> geen RLS (globaal, zelfde patroon als interest_rates).

Revision ID: s197_mail_lock
Revises: s194_all_users_admin
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s197_mail_lock"
down_revision: str | None = "s194_all_users_admin"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_config",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "outbound_mail_locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    # Seed één rij, op slot: fail-safe zodat prod na deploy dicht blijft.
    op.execute("INSERT INTO app_config (outbound_mail_locked) VALUES (true)")


def downgrade() -> None:
    op.drop_table("app_config")
