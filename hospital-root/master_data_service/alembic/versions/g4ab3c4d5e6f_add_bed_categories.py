"""add_bed_categories

Revision ID: g4ab3c4d5e6f
Revises: f3a1b2c3d4e5
Create Date: 2026-04-26 19:35:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g4ab3c4d5e6f'
down_revision: Union[str, None] = 'f3a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create bed_categories table
    op.create_table('bed_categories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bed_categories_name'), 'bed_categories', ['name'], unique=True)

    # 2. Add category_id to beds
    op.add_column('beds', sa.Column('category_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_bed_category_id', 'beds', 'bed_categories', ['category_id'], ['id'])

    # 3. Drop old category column
    op.drop_column('beds', 'category')


def downgrade() -> None:
    # 1. Re-add category column
    op.add_column('beds', sa.Column('category', sa.VARCHAR(), autoincrement=False, nullable=True))

    # 2. Drop category_id and foreign key
    op.drop_constraint('fk_bed_category_id', 'beds', type_='foreignkey')
    op.drop_column('beds', 'category_id')

    # 3. Drop bed_categories table
    op.drop_index(op.f('ix_bed_categories_name'), table_name='bed_categories')
    op.drop_table('bed_categories')
