"""S147a (FEAT-AI-05): voeg snoozed_until kolom toe aan notifications.

Maakt het mogelijk om een CaseActionFeed-kaart tijdelijk te verbergen ("herinner
me later") zonder 'm als afgehandeld te markeren. NULL = niet gesnoozed. De feed
verbergt items waar snoozed_until > now onder het "Wachtend"-filter.

Handgeschreven (niet autogenerate) omdat autogenerate struikelt over een
pre-existing metadata-issue (invoice_lines.product_id → products). De kolom is
puur additief en nullable, dus geen backfill nodig.

Revision ID: s147a_notification_snooze
Revises: df140a_invoice_lines_btw
"""

import sqlalchemy as sa
from alembic import op

revision = "s147a_notification_snooze"
down_revision = "df140a_invoice_lines_btw"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column(
            "snoozed_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("notifications", "snoozed_until")
