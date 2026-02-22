"""G3: Add procesgegevens fields to cases table.

Fields: court_name, judge_name, chamber, procedure_type, procedure_phase.
Kleos-style court proceeding details for Dutch legal practice.

Revision ID: 028_procesgegevens
Revises: 027_email_dismissed
"""

from alembic import op
import sqlalchemy as sa

revision = "028_procesgegevens"
down_revision = "027_email_dismissed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("court_name", sa.String(100), nullable=True))
    op.add_column("cases", sa.Column("judge_name", sa.String(100), nullable=True))
    op.add_column("cases", sa.Column("chamber", sa.String(50), nullable=True))
    op.add_column("cases", sa.Column("procedure_type", sa.String(50), nullable=True))
    op.add_column("cases", sa.Column("procedure_phase", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("cases", "procedure_phase")
    op.drop_column("cases", "procedure_type")
    op.drop_column("cases", "chamber")
    op.drop_column("cases", "judge_name")
    op.drop_column("cases", "court_name")
