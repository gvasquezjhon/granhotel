"""Create guests table

Revision ID: 1a9ecb4e4668
Revises: 8bb8904368f7
Create Date: 2025-06-19 05:17:07.913590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a9ecb4e4668'
down_revision: Union[str, Sequence[str], None] = '8bb8904368f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('guests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('document_type', sa.Enum('DNI', 'RUC', 'PASSPORT', 'CE', name='document_type_enum'), nullable=True),
        sa.Column('document_number', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('address_street', sa.String(), nullable=True),
        sa.Column('address_city', sa.String(), nullable=True),
        sa.Column('address_state_province', sa.String(), nullable=True),
        sa.Column('address_postal_code', sa.String(), nullable=True),
        sa.Column('address_country', sa.String(), nullable=True, server_default='Perú'),
        sa.Column('nationality', sa.String(), nullable=True, server_default='Peruana'),
        sa.Column('preferences', sa.String(), nullable=True),
        sa.Column('is_blacklisted', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), # Model handles onupdate
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_guests_email'), 'guests', ['email'], unique=True)
    op.create_index(op.f('ix_guests_document_number'), 'guests', ['document_number'], unique=True)
    op.create_index(op.f('ix_guests_first_name'), 'guests', ['first_name'], unique=False)
    op.create_index(op.f('ix_guests_id'), 'guests', ['id'], unique=False)
    op.create_index(op.f('ix_guests_last_name'), 'guests', ['last_name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_guests_last_name'), table_name='guests')
    op.drop_index(op.f('ix_guests_id'), table_name='guests')
    op.drop_index(op.f('ix_guests_first_name'), table_name='guests')
    op.drop_index(op.f('ix_guests_document_number'), table_name='guests')
    op.drop_index(op.f('ix_guests_email'), table_name='guests')
    op.drop_table('guests')
    # For PostgreSQL, the enum type should be dropped explicitly.
    # Ensure the Enum type name matches the one in the model ('document_type_enum')
    sa.Enum(name='document_type_enum').drop(op.get_bind(), checkfirst=False)
