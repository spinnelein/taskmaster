"""merge recurring events and initiative fixes

Revision ID: e5380ce294e7
Revises: 0552a18454b2, fix_initiative_as_container
Create Date: 2025-09-14 23:10:05.381635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5380ce294e7'
down_revision: Union[str, None] = ('0552a18454b2', 'fix_initiative_as_container')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
