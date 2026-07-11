"""S198 (B3): zaak-status versimpelen naar 4 vaste waarden.

De status kende een 8-staps-keten (nieuw/14_dagenbrief/sommatie/dagvaarding/
vonnis/executie/betaald/afgesloten), maar de workflow_statuses/transitions-tabellen
stonden leeg → elke statuswijziging faalde. De incasso-pijplijn is de echte motor.
Deze migratie brengt de bestaande data naar het nieuwe 4-status-model:

  nieuw / in_behandeling / betaald / afgesloten

Regels (idempotent + guarded):
  1. Elke niet-terminale legacy-status (14_dagenbrief/sommatie/dagvaarding/vonnis/
     executie en alles wat niet in de 4 valt, behalve 'nieuw') → 'in_behandeling'.
  2. Zaken die nog 'nieuw' zijn maar op een niet-terminale pijplijn-stap staan →
     'in_behandeling' (een zaak op een werk-stap is in behandeling).
  3. 'nieuw' zonder stap blijft 'nieuw'; 'betaald' en 'afgesloten' blijven ongemoeid.

Geen nieuwe tabel → geen RLS-wijziging. Draait als DB-owner (bypass RLS), raakt
dus alle tenants.

Revision ID: s198_status_simplify
Revises: s197_mail_lock
"""

from collections.abc import Sequence

from alembic import op

revision: str = "s198_status_simplify"
down_revision: str | None = "s197_mail_lock"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Legacy niet-terminale statussen → in_behandeling.
    op.execute(
        """
        UPDATE cases
        SET status = 'in_behandeling'
        WHERE status NOT IN ('nieuw', 'in_behandeling', 'betaald', 'afgesloten')
        """
    )
    # 2. 'nieuw' + op een niet-terminale pijplijn-stap → in_behandeling.
    op.execute(
        """
        UPDATE cases c
        SET status = 'in_behandeling'
        FROM incasso_pipeline_steps s
        WHERE c.incasso_step_id = s.id
          AND c.status = 'nieuw'
          AND s.is_terminal = false
        """
    )


def downgrade() -> None:
    # Onomkeerbaar: de oude fijnmazige statussen zijn niet te reconstrueren uit
    # 'in_behandeling'. No-op (bewust) — de 4-status-set blijft geldig.
    pass
