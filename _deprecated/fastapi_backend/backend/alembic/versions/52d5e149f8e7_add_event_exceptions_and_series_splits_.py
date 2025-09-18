"""add event exceptions and series splits tables

Revision ID: 52d5e149f8e7
Revises: 7694f9c015c7
Create Date: 2025-09-14 23:20:32.459896

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52d5e149f8e7'
down_revision: Union[str, None] = '7694f9c015c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
