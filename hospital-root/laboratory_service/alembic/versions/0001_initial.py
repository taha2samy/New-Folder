"""Initial laboratory schema: lab_requests and lab_results tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lab_requests",
        sa.Column("id",           sa.String(),  primary_key=True),
        sa.Column("patient_id",   sa.String(),  nullable=False),
        sa.Column("admission_id", sa.String(),  nullable=True),
        sa.Column("exam_type_id", sa.String(),  nullable=False),
        sa.Column("material",     sa.String(),  nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "COMPLETED", "CANCELLED", name="teststatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "request_date",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_lab_requests_patient_id",   "lab_requests", ["patient_id"])
    op.create_index("ix_lab_requests_exam_type_id", "lab_requests", ["exam_type_id"])

    op.create_table(
        "lab_results",
        sa.Column("id",            sa.String(), primary_key=True),
        sa.Column(
            "request_id",
            sa.String(),
            sa.ForeignKey("lab_requests.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("description",   sa.Text(),   nullable=False),
        sa.Column("value",         sa.Text(),   nullable=False),
        sa.Column(
            "result_date",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("technician_id", sa.String(), nullable=False),
    )
    op.create_index("ix_lab_results_request_id", "lab_results", ["request_id"])


def downgrade() -> None:
    op.drop_table("lab_results")
    op.drop_index("ix_lab_requests_patient_id",   table_name="lab_requests")
    op.drop_index("ix_lab_requests_exam_type_id", table_name="lab_requests")
    op.drop_table("lab_requests")
    op.execute("DROP TYPE IF EXISTS teststatus")
