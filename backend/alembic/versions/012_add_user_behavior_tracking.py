"""add user behavior tracking tables

Revision ID: 012_add_user_behavior_tracking
Revises: b123456789ab
Create Date: 2025-10-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012_add_user_behavior_tracking'
down_revision = 'b123456789ab'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_actions table
    op.create_table('user_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.String(length=255), nullable=False),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('outcome', sa.String(length=255), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('page_load_time_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_actions_user_id'), 'user_actions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_actions_action_type'), 'user_actions', ['action_type'], unique=False)
    op.create_index(op.f('ix_user_actions_target_type'), 'user_actions', ['target_type'], unique=False)
    op.create_index(op.f('ix_user_actions_timestamp'), 'user_actions', ['timestamp'], unique=False)

    # Create behavior_patterns table
    op.create_table('behavior_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pattern_type', sa.String(length=50), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('total_interactions', sa.Integer(), nullable=True),
        sa.Column('dismissal_rate', sa.Float(), nullable=True),
        sa.Column('action_rate', sa.Float(), nullable=True),
        sa.Column('escalation_rate', sa.Float(), nullable=True),
        sa.Column('average_response_time', sa.Float(), nullable=True),
        sa.Column('peak_activity_hours', sa.JSON(), nullable=True),
        sa.Column('suggested_threshold', sa.Float(), nullable=True),
        sa.Column('current_threshold', sa.Float(), nullable=True),
        sa.Column('threshold_confidence', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('pattern_strength', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_behavior_patterns_user_id'), 'behavior_patterns', ['user_id'], unique=False)
    op.create_index(op.f('ix_behavior_patterns_pattern_type'), 'behavior_patterns', ['pattern_type'], unique=False)

    # Create alert_fatigue_metrics table
    op.create_table('alert_fatigue_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=True),
        sa.Column('alerts_received', sa.Integer(), nullable=True),
        sa.Column('alerts_dismissed', sa.Integer(), nullable=True),
        sa.Column('alerts_acted_upon', sa.Integer(), nullable=True),
        sa.Column('alerts_escalated', sa.Integer(), nullable=True),
        sa.Column('dismissal_rate', sa.Float(), nullable=True),
        sa.Column('consecutive_dismissals', sa.Integer(), nullable=True),
        sa.Column('time_to_first_action', sa.Float(), nullable=True),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('suggested_threshold_adjustment', sa.Float(), nullable=True),
        sa.Column('threshold_adjustment_reason', sa.Text(), nullable=True),
        sa.Column('adjustment_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_fatigue_detected', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_fatigue_metrics_user_id'), 'alert_fatigue_metrics', ['user_id'], unique=False)
    op.create_index(op.f('ix_alert_fatigue_metrics_period_start'), 'alert_fatigue_metrics', ['period_start'], unique=False)

    # Create learning_loop_states table
    op.create_table('learning_loop_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_actions_recorded', sa.Integer(), nullable=True),
        sa.Column('patterns_identified', sa.Integer(), nullable=True),
        sa.Column('threshold_adjustments_made', sa.Integer(), nullable=True),
        sa.Column('learning_phase', sa.String(length=50), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=True),
        sa.Column('auto_threshold_adjustment', sa.Boolean(), nullable=True),
        sa.Column('requires_user_approval', sa.Boolean(), nullable=True),
        sa.Column('accuracy_improvement', sa.Float(), nullable=True),
        sa.Column('user_satisfaction_score', sa.Float(), nullable=True),
        sa.Column('last_pattern_update', sa.DateTime(), nullable=True),
        sa.Column('last_threshold_adjustment', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('learning_loop_states')
    
    op.drop_index(op.f('ix_alert_fatigue_metrics_period_start'), table_name='alert_fatigue_metrics')
    op.drop_index(op.f('ix_alert_fatigue_metrics_user_id'), table_name='alert_fatigue_metrics')
    op.drop_table('alert_fatigue_metrics')
    
    op.drop_index(op.f('ix_behavior_patterns_pattern_type'), table_name='behavior_patterns')
    op.drop_index(op.f('ix_behavior_patterns_user_id'), table_name='behavior_patterns')
    op.drop_table('behavior_patterns')
    
    op.drop_index(op.f('ix_user_actions_timestamp'), table_name='user_actions')
    op.drop_index(op.f('ix_user_actions_target_type'), table_name='user_actions')
    op.drop_index(op.f('ix_user_actions_action_type'), table_name='user_actions')
    op.drop_index(op.f('ix_user_actions_user_id'), table_name='user_actions')
    op.drop_table('user_actions')