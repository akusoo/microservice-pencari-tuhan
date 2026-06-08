"""create loans table

Revision ID: 0001_create_loans
Revises:
Create Date: 2026-06-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_create_loans"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "loans",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("member_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("book_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("loan_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "returned", "overdue", name="loanstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_loans_member_id", "loans", ["member_id"])
    op.create_index("ix_loans_book_id", "loans", ["book_id"])


def downgrade() -> None:
    op.drop_index("ix_loans_book_id", table_name="loans")
    op.drop_index("ix_loans_member_id", table_name="loans")
    op.drop_table("loans")
    op.execute("DROP TYPE IF EXISTS loanstatus")
