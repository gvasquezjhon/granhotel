"""Add timezone-aware timestamps to rooms table

Revision ID: 8bb8904368f7
Revises: d24192e91e8b
Create Date: 2025-06-19 05:11:53.639773

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bb8904368f7'
down_revision: Union[str, Sequence[str], None] = 'd24192e91e8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('rooms', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('rooms', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('rooms', 'updated_at')
    op.drop_column('rooms', 'created_at')
