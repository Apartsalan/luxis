"""Update user roles: user → medewerker, add advocaat role

Role values: admin, advocaat, medewerker
- admin: full access, can manage users and tenant settings
- advocaat: can manage cases and generate documents
- medewerker: basic access to assigned cases

Revision ID: 011
Revises: 010
Create Date: 2026-02-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename existing 'user' roles to 'medewerker'
    op.execute("UPDATE users SET role = 'medewerker' WHERE role = 'user'")

    # Change the server default
    op.alter_column(
        "users",
        "role",
        server_default="medewerker",
    )


def downgrade() -> None:
    op.execute("UPDATE users SET role = 'user' WHERE role = 'medewerker'")
    op.alter_column(
        "users",
        "role",
        server_default="user",
    )
