"""add email to students

Revision ID: 11a5bdea170c
Revises: 3c12f0b7d1aa
Create Date: 2026-03-05 21:48:49.859242

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11a5bdea170c'
down_revision: Union[str, Sequence[str], None] = '3c12f0b7d1aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add as nullable first, backfill existing rows, then enforce NOT NULL.
    op.add_column('students', sa.Column('email', sa.String(length=255), nullable=True))
    op.execute("UPDATE students SET email = student_card || '@usb.ve' WHERE email IS NULL")
    op.alter_column('students', 'email', nullable=False)
    op.create_index(op.f('ix_students_email'), 'students', ['email'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_students_email'), table_name='students')
    op.drop_column('students', 'email')
