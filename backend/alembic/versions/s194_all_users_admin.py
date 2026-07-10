"""S194: promoot alle bestaande gebruikers naar admin.

Kesting is een klein kantoor waar iedereen alle rechten moet hebben (wens Arsalan,
S194). Het eerst aangemaakte account stond nog op een lagere rol, waardoor Instellingen
opslaan faalde ("admin nodig"). Deze migratie tilt alle bestaande gebruikers naar admin;
nieuwe gebruikers krijgen admin als default (zie create_user / RegisterRequest / model).

Idempotent: draait alleen op rijen die nog geen admin zijn.

Revision ID: s194_all_users_admin
Revises: s184_rls_learned_answers
"""

from collections.abc import Sequence

from alembic import op

revision: str = "s194_all_users_admin"
down_revision: str | None = "s184_rls_learned_answers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE users SET role = 'admin' WHERE role <> 'admin'")


def downgrade() -> None:
    # Geen betrouwbare terugweg: de vorige rol per gebruiker is niet bewaard.
    # Bewust een no-op — terugdraaien zou willekeurige rollen moeten raden.
    pass
