"""S246b: zet de ontbrekende database-standaardwaarden op scheduled_emails.

S246 maakte created_at/updated_at not-null zonder server_default, terwijl
TimestampMixin die kolommen NIET in Python vult maar aan de database overlaat.
Gevolg: elke insert viel om met een not-null-schending. In productie live
tegengekomen bij de eerste ingeplande mail.

De tests zagen dit niet: de testdatabase wordt uit de MODELLEN gebouwd
(create_all neemt server_default mee), productie uit de MIGRATIE. Sinds S246
bewaakt tests/test_migration_timestamp_defaults.py deze soort.

Deze migratie is bewust apart: s246 is al uitgerold, dus databases die hem al
draaiden hebben deze reparatie nodig. ALTER ... SET DEFAULT is idempotent, dus
een verse installatie (die s246 al gefixt binnenkrijgt) heeft er geen last van.

Revision ID: s246b_sched_ts
Revises: s246_scheduled_emails
"""

from collections.abc import Sequence

from alembic import op

revision: str = "s246b_sched_ts"
down_revision: str | None = "s246_scheduled_emails"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE scheduled_emails ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE scheduled_emails ALTER COLUMN updated_at SET DEFAULT now()")


def downgrade() -> None:
    op.execute("ALTER TABLE scheduled_emails ALTER COLUMN created_at DROP DEFAULT")
    op.execute("ALTER TABLE scheduled_emails ALTER COLUMN updated_at DROP DEFAULT")
