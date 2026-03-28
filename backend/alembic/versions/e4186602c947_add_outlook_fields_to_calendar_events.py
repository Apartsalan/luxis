"""add_outlook_fields_to_calendar_events

Revision ID: e4186602c947
Revises: 955340ca35b1
Create Date: 2026-03-28 14:15:02.347831

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e4186602c947'
down_revision: Union[str, None] = '955340ca35b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('calendar_events', sa.Column('provider_event_id', sa.String(500), nullable=True))
    op.add_column('calendar_events', sa.Column('provider', sa.String(20), nullable=True))
    op.add_column('calendar_events', sa.Column('outlook_change_key', sa.String(500), nullable=True))
    op.create_index(op.f('ix_calendar_events_provider_event_id'), 'calendar_events', ['provider_event_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_calendar_events_provider_event_id'), table_name='calendar_events')
    op.drop_column('calendar_events', 'outlook_change_key')
    op.drop_column('calendar_events', 'provider')
    op.drop_column('calendar_events', 'provider_event_id')
