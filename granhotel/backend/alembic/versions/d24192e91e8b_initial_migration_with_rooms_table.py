"""Initial migration with rooms table

Revision ID: d24192e91e8b
Revises:
Create Date: 2025-06-19 04:16:26.605324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd24192e91e8b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_number", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="Available"),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("building", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_rooms_id", "rooms", ["id"], unique=False)
    op.create_index("ix_rooms_name", "rooms", ["name"], unique=False)
    op.create_index("ix_rooms_room_number", "rooms", ["room_number"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_rooms_room_number", table_name="rooms")
    op.drop_index("ix_rooms_name", table_name="rooms")
    op.drop_index("ix_rooms_id", table_name="rooms")
    op.drop_table("rooms")
