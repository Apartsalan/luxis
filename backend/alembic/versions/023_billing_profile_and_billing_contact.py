"""F6: billing profile on contacts, F7: billing_contact_id on cases.

Revision ID: 023_billing_profile_and_billing_contact
Revises: 022_practical_test_findings
Create Date: 2026-02-20
"""

from alembic import op
import sqlalchemy as sa

revision = "023_billing_profile_and_billing_contact"
down_revision = "022_practical_test_findings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # F6: Billing profile fields on contacts
    op.add_column("contacts", sa.Column("default_hourly_rate", sa.Float(), nullable=True))
    op.add_column("contacts", sa.Column("payment_term_days", sa.Integer(), nullable=True))
    op.add_column("contacts", sa.Column("billing_email", sa.String(320), nullable=True))
    op.add_column("contacts", sa.Column("iban", sa.String(34), nullable=True))

    # F7: Alternate billing contact on cases
    op.add_column(
        "cases",
        sa.Column("billing_contact_id", sa.Uuid(), sa.ForeignKey("contacts.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "billing_contact_id")
    op.drop_column("contacts", "iban")
    op.drop_column("contacts", "billing_email")
    op.drop_column("contacts", "payment_term_days")
    op.drop_column("contacts", "default_hourly_rate")
