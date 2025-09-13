"""Add notifications_enabled to events only

Revision ID: 09125aad8ac6
Revises: 80a50274ef3e
Create Date: 2025-09-12 11:12:28.765556

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09125aad8ac6'
down_revision: Union[str, None] = '604ba2287408'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add only the notifications_enabled field
    op.add_column('events', sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    # Remove the notifications_enabled field
    op.drop_column('events', 'notifications_enabled')
