"""add_recurring_event_master_exception_pattern

Revision ID: 0552a18454b2
Revises: ac8299650abe
Create Date: 2025-09-12 20:32:38.272952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0552a18454b2'
down_revision: Union[str, None] = 'ac8299650abe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new recurring event fields (SQLite compatible)
    op.add_column('events', sa.Column('recurrence_master_id', sa.String(36), nullable=True))
    op.add_column('events', sa.Column('is_recurrence_master', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('events', sa.Column('is_recurrence_exception', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('events', sa.Column('recurrence_instance_date', sa.DateTime(), nullable=True))
    
    # Note: SQLite doesn't support adding foreign key constraints via ALTER TABLE
    # The relationship will be enforced at the application level


def downgrade() -> None:
    # Remove added columns
    op.drop_column('events', 'recurrence_instance_date')
    op.drop_column('events', 'is_recurrence_exception')
    op.drop_column('events', 'is_recurrence_master')
    op.drop_column('events', 'recurrence_master_id')
