"""add_promise_fields_to_email_classifications

Revision ID: a183ac898ad4
Revises: e4186602c947
Create Date: 2026-03-28 19:18:44.876394

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a183ac898ad4'
down_revision: Union[str, None] = 'e4186602c947'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('email_classifications', sa.Column('promise_date', sa.Date(), nullable=True))
    op.add_column('email_classifications', sa.Column('promise_amount', sa.Numeric(precision=15, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('email_classifications', 'promise_amount')
    op.drop_column('email_classifications', 'promise_date')
