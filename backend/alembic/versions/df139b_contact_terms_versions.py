"""S140: AV-versies per cliënt + dossier-koppeling.

Voorheen: 1 AV-PDF per cliënt (`contact.terms_file_path`). Bij incasso over
oude factuur citeerde AI uit huidige AV-versie, niet uit de AV die gold bij
overeenkomst. Nu: aparte `contact_terms` tabel met versies (label,
valid_from, valid_to) en `case.contact_terms_id` FK voor expliciete koppeling.

Data-migratie: bestaande `contact.terms_file_path` wordt eerste rij in
`contact_terms` met valid_from=NULL (= "altijd geldig"). Oude kolommen
blijven staan voor backwards-compat — in volgende sessie verwijderen na
verificatie.

Revision ID: df139b_contact_terms
Revises: df139a_salutation
"""

import sqlalchemy as sa
from alembic import op

revision = "df139b_contact_terms"
down_revision = "df139a_salutation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nieuwe versie-tabel
    op.create_table(
        "contact_terms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("contact_id", sa.Uuid(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("uploaded_by_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["contact_id"], ["contacts.id"], name="fk_contact_terms_contact_id"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_contact_terms_contact_id", "contact_terms", ["contact_id"], unique=False
    )
    op.create_index(
        "ix_contact_terms_tenant_id", "contact_terms", ["tenant_id"], unique=False
    )

    # Case-koppeling
    op.add_column(
        "cases",
        sa.Column("contact_terms_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_cases_contact_terms_id",
        "cases",
        "contact_terms",
        ["contact_terms_id"],
        ["id"],
    )

    # Data-migratie: bestaande contact.terms_file_path → eerste rij in
    # contact_terms met valid_from=NULL (= geldig voor elk dossier ongeacht
    # factuur-datum tot Lisanne nieuwe versies uploadt).
    op.execute(
        """
        INSERT INTO contact_terms (
            id, tenant_id, contact_id, file_path, file_name,
            label, valid_from, valid_to, uploaded_by_id, created_at, updated_at
        )
        SELECT
            gen_random_uuid(), tenant_id, id, terms_file_path, terms_file_name,
            'Huidige versie', NULL, NULL, NULL, now(), now()
        FROM contacts
        WHERE terms_file_path IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_constraint("fk_cases_contact_terms_id", "cases", type_="foreignkey")
    op.drop_column("cases", "contact_terms_id")
    op.drop_index("ix_contact_terms_tenant_id", table_name="contact_terms")
    op.drop_index("ix_contact_terms_contact_id", table_name="contact_terms")
    op.drop_table("contact_terms")
