# granhotel/backend/alembic/versions/c2d3e4f5a6b7_create_pos_tables_and_enums.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c2d3e4f5a6b7'
down_revision = 'b1c2d3e4f5a6' # Previous migration (housekeeping)
branch_labels = None
depends_on = None

# Define ENUM types for reusability
payment_method_enum_name = 'pos_payment_method_enum'
payment_method_values = ['CASH', 'CARD_DEBIT', 'CARD_CREDIT', 'YAPE', 'PLIN', 'BANK_TRANSFER', 'ROOM_CHARGE', 'OTHER']
pg_payment_method_enum = postgresql.ENUM(*payment_method_values, name=payment_method_enum_name, create_type=False)

pos_sale_status_enum_name = 'pos_sale_status_enum'
pos_sale_status_values = ['COMPLETED', 'VOIDED', 'PENDING_PAYMENT']
pg_pos_sale_status_enum = postgresql.ENUM(*pos_sale_status_values, name=pos_sale_status_enum_name, create_type=False)


def upgrade() -> None:
    # Create ENUM types first
    pg_payment_method_enum.create(op.get_bind(), checkfirst=True)
    pg_pos_sale_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('pos_sales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('cashier_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('guest_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('total_amount_before_tax', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_amount_after_tax', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payment_method', pg_payment_method_enum, nullable=True),
        sa.Column('payment_reference', sa.String(length=100), nullable=True),
        sa.Column('status', pg_pos_sale_status_enum, server_default='COMPLETED', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('void_reason', sa.Text(), nullable=True),
        sa.Column('voided_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.ForeignKeyConstraint(['cashier_user_id'], ['users.id'], name=op.f('fk_pos_sales_cashier_user_id_users')),
        sa.ForeignKeyConstraint(['guest_id'], ['guests.id'], name=op.f('fk_pos_sales_guest_id_guests')),
        sa.ForeignKeyConstraint(['voided_by_user_id'], ['users.id'], name=op.f('fk_pos_sales_voided_by_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_pos_sales'))
    )
    op.create_index(op.f('ix_pos_sales_id'), 'pos_sales', ['id'], unique=False)
    op.create_index(op.f('ix_pos_sales_sale_date'), 'pos_sales', ['sale_date'], unique=False)
    op.create_index(op.f('ix_pos_sales_cashier_user_id'), 'pos_sales', ['cashier_user_id'], unique=False)
    op.create_index(op.f('ix_pos_sales_guest_id'), 'pos_sales', ['guest_id'], unique=False)
    op.create_index(op.f('ix_pos_sales_status'), 'pos_sales', ['status'], unique=False)


    op.create_table('pos_sale_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pos_sale_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price_before_tax', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('tax_rate_applied', sa.Numeric(precision=4, scale=2), server_default='0.18', nullable=False),
        sa.Column('tax_amount_for_item', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_price_for_item_after_tax', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.ForeignKeyConstraint(['pos_sale_id'], ['pos_sales.id'], name=op.f('fk_pos_sale_items_pos_sale_id_pos_sales')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name=op.f('fk_pos_sale_items_product_id_products')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_pos_sale_items'))
    )
    op.create_index(op.f('ix_pos_sale_items_id'), 'pos_sale_items', ['id'], unique=False)
    op.create_index(op.f('ix_pos_sale_items_pos_sale_id'), 'pos_sale_items', ['pos_sale_id'], unique=False)
    op.create_index(op.f('ix_pos_sale_items_product_id'), 'pos_sale_items', ['product_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_pos_sale_items_product_id'), table_name='pos_sale_items')
    op.drop_index(op.f('ix_pos_sale_items_pos_sale_id'), table_name='pos_sale_items')
    op.drop_index(op.f('ix_pos_sale_items_id'), table_name='pos_sale_items')
    op.drop_table('pos_sale_items')

    op.drop_index(op.f('ix_pos_sales_status'), table_name='pos_sales')
    op.drop_index(op.f('ix_pos_sales_guest_id'), table_name='pos_sales')
    op.drop_index(op.f('ix_pos_sales_cashier_user_id'), table_name='pos_sales')
    op.drop_index(op.f('ix_pos_sales_sale_date'), table_name='pos_sales')
    op.drop_index(op.f('ix_pos_sales_id'), table_name='pos_sales')
    op.drop_table('pos_sales')

    pg_pos_sale_status_enum.drop(op.get_bind(), checkfirst=False)
    pg_payment_method_enum.drop(op.get_bind(), checkfirst=False)
