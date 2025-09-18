"""Fix initiative model to be a container not a scheduled item

Revision ID: fix_initiative_as_container
Revises: ac8299650abe
Create Date: 2025-09-13 01:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_initiative_as_container'
down_revision = 'ac8299650abe'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the scheduling-related columns from initiatives table
    with op.batch_alter_table('initiatives', schema=None) as batch_op:
        batch_op.drop_column('frequency')
        batch_op.drop_column('interval')
        batch_op.drop_column('preferred_start_time')
        batch_op.drop_column('estimated_duration_minutes')


def downgrade():
    # Add back the columns if we need to rollback
    with op.batch_alter_table('initiatives', schema=None) as batch_op:
        batch_op.add_column(sa.Column('frequency', sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY', 'CUSTOM', name='initiativefrequency'), nullable=True))
        batch_op.add_column(sa.Column('interval', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('preferred_start_time', sa.VARCHAR(length=8), nullable=True))
        batch_op.add_column(sa.Column('estimated_duration_minutes', sa.INTEGER(), nullable=True))