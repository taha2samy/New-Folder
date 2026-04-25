"""rename_bed_number_to_bed_id

Revision ID: 71c5ce460ae1
Revises: 89edadbb3397
Create Date: 2026-04-25 20:48:35.619014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71c5ce460ae1'
down_revision: Union[str, None] = '89edadbb3397'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('encounters', 'bed_number', new_column_name='bed_id', existing_type=sa.String(length=20))


def downgrade() -> None:
    op.alter_column('encounters', 'bed_id', new_column_name='bed_number', existing_type=sa.String(length=20))