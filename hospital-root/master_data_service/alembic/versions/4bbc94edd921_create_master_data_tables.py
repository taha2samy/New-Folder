"""create master data tables

Revision ID: 4bbc94edd921
Revises: 
Create Date: 2026-04-25 02:57:26.287666
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '4bbc94edd921'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    procedure_type_enum = sa.Enum('SINGLE_VALUE', 'MULTIPLE_BOOLEAN', 'MANUAL_TEXT', name='proceduretypeenum')
    procedure_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('suppliers',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('contact_info', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_constraint('disease_types_code_key', 'disease_types', type_='unique')
    op.create_index(op.f('ix_disease_types_code'), 'disease_types', ['code'], unique=True)
    op.drop_constraint('diseases_code_key', 'diseases', type_='unique')
    op.create_index(op.f('ix_diseases_code'), 'diseases', ['code'], unique=True)
    op.create_index(op.f('ix_diseases_disease_type_id'), 'diseases', ['disease_type_id'], unique=False)
    
    op.alter_column('exam_types', 'procedure_type',
               existing_type=sa.VARCHAR(),
               type_=procedure_type_enum,
               existing_nullable=False,
               postgresql_using='procedure_type::proceduretypeenum')
               
    op.drop_constraint('exam_types_code_key', 'exam_types', type_='unique')
    op.create_index(op.f('ix_exam_types_code'), 'exam_types', ['code'], unique=True)
    op.drop_constraint('operation_types_code_key', 'operation_types', type_='unique')
    op.create_index(op.f('ix_operation_types_code'), 'operation_types', ['code'], unique=True)
    op.drop_constraint('wards_code_key', 'wards', type_='unique')
    op.create_index(op.f('ix_wards_code'), 'wards', ['code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_wards_code'), table_name='wards')
    op.create_unique_constraint('wards_code_key', 'wards', ['code'])
    op.drop_index(op.f('ix_operation_types_code'), table_name='operation_types')
    op.create_unique_constraint('operation_types_code_key', 'operation_types', ['code'])
    op.drop_index(op.f('ix_exam_types_code'), table_name='exam_types')
    op.create_unique_constraint('exam_types_code_key', 'exam_types', ['code'])
    
    op.alter_column('exam_types', 'procedure_type',
               existing_type=sa.Enum('SINGLE_VALUE', 'MULTIPLE_BOOLEAN', 'MANUAL_TEXT', name='proceduretypeenum'),
               type_=sa.VARCHAR(),
               existing_nullable=False)
               
    op.drop_index(op.f('ix_diseases_disease_type_id'), table_name='diseases')
    op.drop_index(op.f('ix_diseases_code'), table_name='diseases')
    op.create_unique_constraint('diseases_code_key', 'diseases', ['code'])
    op.drop_index(op.f('ix_disease_types_code'), table_name='disease_types')
    op.create_unique_constraint('disease_types_code_key', 'disease_types', ['code'])
    op.drop_table('suppliers')
    
    sa.Enum(name='proceduretypeenum').drop(op.get_bind(), checkfirst=True)