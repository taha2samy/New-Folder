"""add_is_deleted_to_beds

Revision ID: e1020686ec7e
Revises: c56f9358de58
Create Date: 2026-04-25 20:47:36.623079
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'e1020686ec7e'
down_revision: Union[str, None] = 'c56f9358de58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('beds', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('beds', 'is_deleted')
