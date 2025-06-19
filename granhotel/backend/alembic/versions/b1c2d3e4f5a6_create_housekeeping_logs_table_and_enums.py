# granhotel/backend/alembic/versions/b1c2d3e4f5a6_create_housekeeping_logs_table_and_enums.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = 'ee3146902c92' # Previous migration (inventory management)
branch_labels = None
depends_on = None

# Define ENUM types for reusability
hk_task_type_enum_name = 'hk_task_type_enum'
hk_task_type_values = ['FULL_CLEAN', 'STAY_OVER_CLEAN', 'TURNDOWN_SERVICE', 'MAINTENANCE_CHECK', 'LINEN_CHANGE', 'VACANT_ROOM_CHECK']
pg_hk_task_type_enum = postgresql.ENUM(*hk_task_type_values, name=hk_task_type_enum_name, create_type=False)

hk_status_enum_name = 'hk_status_enum'
hk_status_values = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'NEEDS_INSPECTION', 'ISSUE_REPORTED', 'CANCELLED']
pg_hk_status_enum = postgresql.ENUM(*hk_status_values, name=hk_status_enum_name, create_type=False)


def upgrade() -> None:
    # Create ENUM types first
    pg_hk_task_type_enum.create(op.get_bind(), checkfirst=True)
    pg_hk_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('housekeeping_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('task_type', pg_hk_task_type_enum, nullable=False),
        sa.Column('status', pg_hk_status_enum, server_default='PENDING', nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes_instructions', sa.Text(), nullable=True),
        sa.Column('notes_issues_reported', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], name=op.f('fk_housekeeping_logs_room_id_rooms')),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], name=op.f('fk_housekeeping_logs_assigned_to_user_id_users')),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_housekeeping_logs_created_by_user_id_users')),
        sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], name=op.f('fk_housekeeping_logs_updated_by_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_housekeeping_logs'))
    )
    op.create_index(op.f('ix_housekeeping_logs_id'), 'housekeeping_logs', ['id'], unique=False)
    op.create_index(op.f('ix_housekeeping_logs_room_id'), 'housekeeping_logs', ['room_id'], unique=False)
    op.create_index(op.f('ix_housekeeping_logs_assigned_to_user_id'), 'housekeeping_logs', ['assigned_to_user_id'], unique=False)
    op.create_index(op.f('ix_housekeeping_logs_scheduled_date'), 'housekeeping_logs', ['scheduled_date'], unique=False)
    op.create_index(op.f('ix_housekeeping_logs_status'), 'housekeeping_logs', ['status'], unique=False)
    op.create_index(op.f('ix_housekeeping_logs_task_type'), 'housekeeping_logs', ['task_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_housekeeping_logs_task_type'), table_name='housekeeping_logs')
    op.drop_index(op.f('ix_housekeeping_logs_status'), table_name='housekeeping_logs')
    op.drop_index(op.f('ix_housekeeping_logs_scheduled_date'), table_name='housekeeping_logs')
    op.drop_index(op.f('ix_housekeeping_logs_assigned_to_user_id'), table_name='housekeeping_logs')
    op.drop_index(op.f('ix_housekeeping_logs_room_id'), table_name='housekeeping_logs')
    op.drop_index(op.f('ix_housekeeping_logs_id'), table_name='housekeeping_logs')
    op.drop_table('housekeeping_logs')

    # Drop ENUM types last
    pg_hk_status_enum.drop(op.get_bind(), checkfirst=False)
    pg_hk_task_type_enum.drop(op.get_bind(), checkfirst=False)
