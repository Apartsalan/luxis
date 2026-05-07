"""add html body fields to incasso step and ai draft

Revision ID: 1f7244b8d57e
Revises: s133c01
Create Date: 2026-05-07 09:44:37.902340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f7244b8d57e'
down_revision: Union[str, None] = 's133c01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "incasso_pipeline_steps",
        sa.Column("email_body_template_html", sa.Text(), nullable=True),
    )
    op.add_column(
        "ai_drafts",
        sa.Column("body_html", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ai_drafts", "body_html")
    op.drop_column("incasso_pipeline_steps", "email_body_template_html")
