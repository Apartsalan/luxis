"""SEC-20: Add account lockout fields to users table

Adds failed_login_count and locked_until columns for brute-force protection.

Revision ID: sec20_account_lockout
Revises: sec13_rls_email_logs
Create Date: 2026-03-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "sec20_account_lockout"
down_revision: Union[str, None] = "sec13_rls_email_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_count")
