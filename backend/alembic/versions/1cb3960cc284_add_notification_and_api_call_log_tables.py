"""add_notification_and_api_call_log_tables

Revision ID: 1cb3960cc284
Revises: 016_add_comment_notifications
Create Date: 2025-11-01 09:10:15.279913

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1cb3960cc284'
down_revision = '016_add_comment_notifications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notification_rules table
    op.create_table(
        'notification_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('competitor_name', sa.String(length=255), nullable=False),
        sa.Column('condition_type', sa.String(length=50), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('target', sa.String(length=255), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_rules_id'), 'notification_rules', ['id'], unique=False)
    op.create_index('ix_notification_rules_competitor_name', 'notification_rules', ['competitor_name'], unique=False)

    # Create notification_logs table
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=True),
        sa.Column('competitor_name', sa.String(length=255), nullable=False),
        sa.Column('message', sa.String(length=1024), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('target', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_logs_id'), 'notification_logs', ['id'], unique=False)
    op.create_index('ix_notification_logs_rule_id', 'notification_logs', ['rule_id'], unique=False)
    op.create_index('ix_notification_logs_created_at', 'notification_logs', ['created_at'], unique=False)

    # Create api_call_logs table
    op.create_table(
        'api_call_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_type', sa.String(length=50), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_call_logs_id'), 'api_call_logs', ['id'], unique=False)
    op.create_index('ix_api_call_logs_api_type', 'api_call_logs', ['api_type'], unique=False)
    op.create_index('ix_api_call_logs_success', 'api_call_logs', ['success'], unique=False)
    op.create_index('ix_api_call_logs_created_at', 'api_call_logs', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_api_call_logs_created_at', table_name='api_call_logs')
    op.drop_index('ix_api_call_logs_success', table_name='api_call_logs')
    op.drop_index('ix_api_call_logs_api_type', table_name='api_call_logs')
    op.drop_index(op.f('ix_api_call_logs_id'), table_name='api_call_logs')
    
    op.drop_index('ix_notification_logs_created_at', table_name='notification_logs')
    op.drop_index('ix_notification_logs_rule_id', table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_id'), table_name='notification_logs')
    
    op.drop_index('ix_notification_rules_competitor_name', table_name='notification_rules')
    op.drop_index(op.f('ix_notification_rules_id'), table_name='notification_rules')
    
    # Drop tables
    op.drop_table('api_call_logs')
    op.drop_table('notification_logs')
    op.drop_table('notification_rules')