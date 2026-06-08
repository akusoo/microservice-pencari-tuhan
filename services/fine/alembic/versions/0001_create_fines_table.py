"""create fines table

Revision ID: 0001_create_fines
Revises:
Create Date: 2026-06-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_create_fines"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fines",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("loan_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("member_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("is_paid", sa.Boolean(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fines_loan_id", "fines", ["loan_id"], unique=True)
    op.create_index("ix_fines_member_id", "fines", ["member_id"])


def downgrade() -> None:
    op.drop_index("ix_fines_member_id", table_name="fines")
    op.drop_index("ix_fines_loan_id", table_name="fines")
    op.drop_table("fines")
