"""Create users table and user_role_enum

Revision ID: e2097728e0a1
Revises: 736754f3b0d8
Create Date: 2025-06-19 05:53:24.454800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql # For UUID type


# revision identifiers, used by Alembic.
revision: str = 'e2097728e0a1'
down_revision: Union[str, Sequence[str], None] = '736754f3b0d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Define enum type name and values for reusability
user_role_enum_name = 'user_role_enum'
user_role_enum_values = ['ADMIN', 'MANAGER', 'RECEPTIONIST', 'HOUSEKEEPER']

def upgrade() -> None:
    """Upgrade schema."""
    # Create the ENUM type for user_role
    user_role_type = sa.Enum(*user_role_enum_values, name=user_role_enum_name)
    user_role_type.create(op.get_bind(), checkfirst=True)

    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true_(), nullable=False),
        sa.Column('role', user_role_type, server_default='RECEPTIONIST', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), # Model handles onupdate
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False) # Index on PK is usually automatic, but explicit for f('ix_...') consistency


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Drop the ENUM type
    user_role_type = sa.Enum(*user_role_enum_values, name=user_role_enum_name)
    user_role_type.drop(op.get_bind(), checkfirst=False)
