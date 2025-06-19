"""Create reservations table and reservation_status_enum

Revision ID: 736754f3b0d8
Revises: 1a9ecb4e4668
Create Date: 2025-06-19 05:37:01.883414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '736754f3b0d8'
down_revision: Union[str, Sequence[str], None] = '1a9ecb4e4668'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Define enum type name and values for reusability
reservation_status_enum_name = 'reservation_status_enum'
reservation_status_enum_values = ['PENDING', 'CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT', 'CANCELLED', 'NO_SHOW', 'WAITLIST']

def upgrade() -> None:
    """Upgrade schema."""
    # Create the ENUM type for reservation_status
    reservation_status_type = sa.Enum(*reservation_status_enum_values, name=reservation_status_enum_name)
    reservation_status_type.create(op.get_bind(), checkfirst=True)

    op.create_table('reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guest_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('check_in_date', sa.Date(), nullable=False),
        sa.Column('check_out_date', sa.Date(), nullable=False),
        sa.Column('reservation_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', reservation_status_type, nullable=False, server_default='PENDING'),
        sa.Column('total_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        # sa.Column('booked_by_user_id', sa.Integer(), nullable=True), # If adding later
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), # Model handles onupdate
        sa.ForeignKeyConstraint(['guest_id'], ['guests.id'], ),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
        # sa.ForeignKeyConstraint(['booked_by_user_id'], ['users.id'], ), # If adding later
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reservations_guest_id'), 'reservations', ['guest_id'], unique=False)
    op.create_index(op.f('ix_reservations_id'), 'reservations', ['id'], unique=False)
    op.create_index(op.f('ix_reservations_room_id'), 'reservations', ['room_id'], unique=False)
    op.create_index(op.f('ix_reservations_status'), 'reservations', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_reservations_status'), table_name='reservations')
    op.drop_index(op.f('ix_reservations_room_id'), table_name='reservations')
    op.drop_index(op.f('ix_reservations_id'), table_name='reservations')
    op.drop_index(op.f('ix_reservations_guest_id'), table_name='reservations')
    op.drop_table('reservations')

    # Drop the ENUM type
    reservation_status_type = sa.Enum(*reservation_status_enum_values, name=reservation_status_enum_name)
    reservation_status_type.drop(op.get_bind(), checkfirst=False)
