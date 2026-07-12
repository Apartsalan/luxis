"""S205: zet het e-mailsjabloon '14_dagenbrief' op de bestaande 14-dagenbrief-stap.

Akkoord Arsalan (S205): Luxis mag de 14-dagenbrief zelf versturen ('allebei
mogelijk'). Nieuwe kantoren krijgen dit via de seed (DEFAULT_PIPELINE_STEPS);
bestaande kantoren (Kesting) hebben de stap al zonder template_type → deze
idempotente data-migratie vult 'm aan. Raakt alleen stappen die nog géén sjabloon
hebben, dus veilig voor kantoren die de brief bewust buiten Luxis houden en de stap
handmatig hebben aangepast.

Revision ID: s205_dagenbrief_template
Revises: s203b_scheduler_heartbeat
"""

from collections.abc import Sequence

from alembic import op

revision: str = "s205_dagenbrief_template"
down_revision: str | None = "s203b_scheduler_heartbeat"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE incasso_pipeline_steps
        SET template_type = '14_dagenbrief'
        WHERE name = '14-dagenbrief'
          AND (template_type IS NULL OR template_type = '')
        """
    )


def downgrade() -> None:
    # Alleen de door deze migratie gezette waarde terugdraaien.
    op.execute(
        """
        UPDATE incasso_pipeline_steps
        SET template_type = NULL
        WHERE name = '14-dagenbrief'
          AND template_type = '14_dagenbrief'
        """
    )
