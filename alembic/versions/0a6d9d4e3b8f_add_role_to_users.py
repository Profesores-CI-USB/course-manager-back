"""add role to users

Revision ID: 0a6d9d4e3b8f
Revises: afde166906d5
Create Date: 2026-03-04 22:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0a6d9d4e3b8f"
down_revision: Union[str, Sequence[str], None] = "afde166906d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="professor"),
    )
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('admin', 'professor')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
