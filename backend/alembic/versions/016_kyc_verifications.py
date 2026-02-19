"""Add kyc_verifications table for WWFT/KYC compliance.

WWFT (Wet ter voorkoming van witwassen en financieren van terrorisme) requires
Dutch law firms to verify client identity, check PEP/sanctions lists, and
classify risk levels. This table stores all verification data per contact.

Revision ID: 016
Revises: 015
Create Date: 2026-02-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kyc_verifications",
        # PK + tenant
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Uuid(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        # Link to contact
        sa.Column(
            "contact_id",
            sa.Uuid(),
            sa.ForeignKey("contacts.id"),
            nullable=False,
            index=True,
        ),
        # Status
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="niet_gestart",
        ),
        # Risk classification
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("risk_notes", sa.Text(), nullable=True),
        # Identity document
        sa.Column("id_type", sa.String(30), nullable=True),
        sa.Column("id_number", sa.String(50), nullable=True),
        sa.Column("id_expiry_date", sa.Date(), nullable=True),
        sa.Column("id_verified_at", sa.Date(), nullable=True),
        # UBO (for companies)
        sa.Column("ubo_name", sa.String(255), nullable=True),
        sa.Column("ubo_dob", sa.Date(), nullable=True),
        sa.Column("ubo_nationality", sa.String(100), nullable=True),
        sa.Column("ubo_percentage", sa.String(20), nullable=True),
        sa.Column("ubo_verified_at", sa.Date(), nullable=True),
        # PEP check
        sa.Column(
            "pep_checked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "pep_is_pep",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("pep_notes", sa.Text(), nullable=True),
        # Sanctions check
        sa.Column(
            "sanctions_checked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "sanctions_hit",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("sanctions_notes", sa.Text(), nullable=True),
        # Source of funds
        sa.Column("source_of_funds", sa.Text(), nullable=True),
        sa.Column(
            "source_of_funds_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        # Verification metadata
        sa.Column(
            "verified_by_id",
            sa.Uuid(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("verification_date", sa.Date(), nullable=True),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        # Notes
        sa.Column("notes", sa.Text(), nullable=True),
        # Timestamps
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

    # Unique constraint: one KYC record per contact per tenant
    op.create_unique_constraint(
        "uq_kyc_contact_tenant",
        "kyc_verifications",
        ["tenant_id", "contact_id"],
    )


def downgrade() -> None:
    op.drop_table("kyc_verifications")
