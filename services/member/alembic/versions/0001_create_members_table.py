"""create members table

Revision ID: 0001_create_members
Revises:
Create Date: 2026-06-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_create_members"
down_revision = None
branch_labels = None
depends_on = None

member_status = sa.Enum("active", "inactive", "blocked", name="memberstatus")


def upgrade() -> None:
    member_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "members",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("status", member_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_members_user_id", "members", ["user_id"], unique=True)
    op.create_index("ix_members_email", "members", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_members_email", table_name="members")
    op.drop_index("ix_members_user_id", table_name="members")
    op.drop_table("members")
    member_status.drop(op.get_bind(), checkfirst=True)
