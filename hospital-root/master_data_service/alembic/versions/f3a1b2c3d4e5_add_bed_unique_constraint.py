"""add_bed_unique_constraint

Revision ID: f3a1b2c3d4e5
Revises: e1020686ec7e
Create Date: 2026-04-25 22:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a1b2c3d4e5'
down_revision: Union[str, None] = 'e1020686ec7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('uq_bed_code_per_ward', 'beds', ['code', 'ward_id'])


def downgrade() -> None:
    op.drop_constraint('uq_bed_code_per_ward', 'beds', type_='unique')
