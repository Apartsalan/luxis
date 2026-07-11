"""S199: Nederlandse full-text search voor e-mails en dossierstukken.

Revision ID: s199_powersearch
Revises: s198_status_simplify
"""

from collections.abc import Sequence

from alembic import op

revision: str = "s199_powersearch"
down_revision: str | None = "s198_status_simplify"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE synced_emails ADD COLUMN search_vector tsvector
          GENERATED ALWAYS AS (
            to_tsvector('dutch',
              coalesce(subject,'') || ' ' || coalesce(left(body_text, 300000),''))
          ) STORED;
        """
    )
    op.execute(
        "CREATE INDEX ix_synced_emails_search "
        "ON synced_emails USING GIN (search_vector)"
    )
    op.execute(
        """
        ALTER TABLE case_files ADD COLUMN extracted_text text;
        """
    )
    op.execute(
        """
        ALTER TABLE case_files ADD COLUMN search_vector tsvector
          GENERATED ALWAYS AS (
            to_tsvector('dutch',
              coalesce(original_filename,'') || ' ' || coalesce(description,'') || ' ' ||
              coalesce(left(extracted_text, 300000),''))
          ) STORED;
        """
    )
    op.execute(
        "CREATE INDEX ix_case_files_search "
        "ON case_files USING GIN (search_vector)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_case_files_search")
    op.execute("ALTER TABLE case_files DROP COLUMN IF EXISTS search_vector")
    op.execute("ALTER TABLE case_files DROP COLUMN IF EXISTS extracted_text")
    op.execute("DROP INDEX IF EXISTS ix_synced_emails_search")
    op.execute("ALTER TABLE synced_emails DROP COLUMN IF EXISTS search_vector")
