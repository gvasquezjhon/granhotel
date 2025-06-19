# granhotel/backend/alembic/versions/d3e4f5a6b7c8_create_billing_folio_tables_and_enums.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd3e4f5a6b7c8'
down_revision = 'c2d3e4f5a6b7' # Previous migration (POS)
branch_labels = None
depends_on = None

# Define ENUM types for reusability
folio_status_enum_name = 'folio_status_enum'
folio_status_values = ['OPEN', 'CLOSED', 'SETTLED', 'VOIDED']
pg_folio_status_enum = postgresql.ENUM(*folio_status_values, name=folio_status_enum_name, create_type=False)

folio_transaction_type_enum_name = 'folio_transaction_type_enum'
folio_transaction_type_values = ['ROOM_CHARGE', 'POS_CHARGE', 'SERVICE_CHARGE', 'PAYMENT', 'REFUND', 'DISCOUNT_ADJUSTMENT', 'TAX_CHARGE']
pg_folio_transaction_type_enum = postgresql.ENUM(*folio_transaction_type_values, name=folio_transaction_type_enum_name, create_type=False)


def upgrade() -> None:
    # Create ENUM types first
    pg_folio_status_enum.create(op.get_bind(), checkfirst=True)
    pg_folio_transaction_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('guest_folios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guest_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reservation_id', sa.Integer(), nullable=True),
        sa.Column('status', pg_folio_status_enum, server_default='OPEN', nullable=False),
        sa.Column('total_charges', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('total_payments', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('opened_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.ForeignKeyConstraint(['guest_id'], ['guests.id'], name=op.f('fk_guest_folios_guest_id_guests')),
        sa.ForeignKeyConstraint(['reservation_id'], ['reservations.id'], name=op.f('fk_guest_folios_reservation_id_reservations')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_guest_folios'))
    )
    op.create_index(op.f('ix_guest_folios_id'), 'guest_folios', ['id'], unique=False)
    op.create_index(op.f('ix_guest_folios_guest_id'), 'guest_folios', ['guest_id'], unique=False)
    op.create_index(op.f('ix_guest_folios_reservation_id'), 'guest_folios', ['reservation_id'], unique=False)
    op.create_index(op.f('ix_guest_folios_status'), 'guest_folios', ['status'], unique=False)

    op.create_table('folio_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guest_folio_id', sa.Integer(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('charge_amount', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False),
        sa.Column('payment_amount', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False),
        sa.Column('transaction_type', pg_folio_transaction_type_enum, nullable=False),
        sa.Column('related_pos_sale_id', sa.Integer(), nullable=True),
        sa.Column('related_reservation_id', sa.Integer(), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        # No updated_at for transactions

        sa.ForeignKeyConstraint(['guest_folio_id'], ['guest_folios.id'], name=op.f('fk_folio_transactions_guest_folio_id_guest_folios')),
        sa.ForeignKeyConstraint(['related_pos_sale_id'], ['pos_sales.id'], name=op.f('fk_folio_transactions_related_pos_sale_id_pos_sales')),
        sa.ForeignKeyConstraint(['related_reservation_id'], ['reservations.id'], name=op.f('fk_folio_transactions_related_reservation_id_reservations')),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_folio_transactions_created_by_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_folio_transactions'))
    )
    op.create_index(op.f('ix_folio_transactions_id'), 'folio_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_folio_transactions_guest_folio_id'), 'folio_transactions', ['guest_folio_id'], unique=False)
    op.create_index(op.f('ix_folio_transactions_transaction_type'), 'folio_transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_folio_transactions_related_pos_sale_id'), 'folio_transactions', ['related_pos_sale_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_folio_transactions_related_pos_sale_id'), table_name='folio_transactions')
    op.drop_index(op.f('ix_folio_transactions_transaction_type'), table_name='folio_transactions')
    op.drop_index(op.f('ix_folio_transactions_guest_folio_id'), table_name='folio_transactions')
    op.drop_index(op.f('ix_folio_transactions_id'), table_name='folio_transactions')
    op.drop_table('folio_transactions')

    op.drop_index(op.f('ix_guest_folios_status'), table_name='guest_folios')
    op.drop_index(op.f('ix_guest_folios_reservation_id'), table_name='guest_folios')
    op.drop_index(op.f('ix_guest_folios_guest_id'), table_name='guest_folios')
    op.drop_index(op.f('ix_guest_folios_id'), table_name='guest_folios')
    op.drop_table('guest_folios')

    pg_folio_transaction_type_enum.drop(op.get_bind(), checkfirst=False)
    pg_folio_status_enum.drop(op.get_bind(), checkfirst=False)
