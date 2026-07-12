"""S203 #2: scheduler_heartbeat — laatste-run-registratie per achtergrondtaak.

Dead-man-switch: stopt een job (m.n. de dagelijkse verjaringscheck) stil, dan
loopt zijn last_run_at achter en kan de UI dat signaleren. Globale tabel (geen
tenant_id → geen RLS, zelfde patroon als app_config/interest_rates).

Revision ID: s203b_scheduler_heartbeat
Revises: s203_email_sync_error
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s203b_scheduler_heartbeat"
down_revision: str | None = "s203_email_sync_error"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scheduler_heartbeat",
        sa.Column("job_id", sa.String(length=100), primary_key=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("scheduler_heartbeat")
