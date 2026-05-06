"""Voeg pipeline_auto_drafts_enabled feature flag toe aan tenants.

Revision ID: s133c01
Revises: s133b01
Create Date: 2026-05-06

Per-tenant flag: bij true draait de daily scheduler de rule-evaluator over
alle dossiers en genereert AI-drafts. Default false — manual trigger werkt
altijd, ongeacht deze flag.
"""

import sqlalchemy as sa
from alembic import op

revision = "s133c01"
down_revision = "s133b01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "pipeline_auto_drafts_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "pipeline_auto_drafts_enabled")
