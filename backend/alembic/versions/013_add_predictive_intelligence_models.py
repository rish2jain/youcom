"""Add predictive intelligence models

Revision ID: 013_add_predictive_intelligence_models
Revises: 012_add_user_behavior_tracking
Create Date: 2025-10-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_add_predictive_intelligence_models'
down_revision = '012_add_user_behavior_tracking'
branch_labels = None
depends_on = None


def upgrade():
    # Create competitor_patterns table
    op.create_table('competitor_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('competitor_name', sa.String(length=255), nullable=False),
        sa.Column('pattern_type', sa.String(length=100), nullable=False),
        sa.Column('sequence', sa.JSON(), nullable=False),
        sa.Column('frequency', sa.Integer(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('average_duration', sa.Integer(), nullable=True),
        sa.Column('typical_intervals', sa.JSON(), nullable=True),
        sa.Column('first_observed', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_observed', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('contributing_factors', sa.JSON(), nullable=True),
        sa.Column('success_indicators', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_competitor_patterns_id'), 'competitor_patterns', ['id'], unique=False)
    op.create_index(op.f('ix_competitor_patterns_competitor_name'), 'competitor_patterns', ['competitor_name'], unique=False)
    op.create_index(op.f('ix_competitor_patterns_pattern_type'), 'competitor_patterns', ['pattern_type'], unique=False)
    op.create_index(op.f('ix_competitor_patterns_is_active'), 'competitor_patterns', ['is_active'], unique=False)
    op.create_index(op.f('ix_competitor_patterns_created_at'), 'competitor_patterns', ['created_at'], unique=False)

    # Create predicted_events table
    op.create_table('predicted_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pattern_id', sa.Integer(), nullable=False),
        sa.Column('competitor_name', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('predicted_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timeframe', sa.String(length=100), nullable=False),
        sa.Column('earliest_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('latest_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reasoning', sa.JSON(), nullable=True),
        sa.Column('trigger_events', sa.JSON(), nullable=True),
        sa.Column('supporting_evidence', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('actual_outcome', sa.Text(), nullable=True),
        sa.Column('validation_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pattern_id'], ['competitor_patterns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_predicted_events_id'), 'predicted_events', ['id'], unique=False)
    op.create_index(op.f('ix_predicted_events_pattern_id'), 'predicted_events', ['pattern_id'], unique=False)
    op.create_index(op.f('ix_predicted_events_competitor_name'), 'predicted_events', ['competitor_name'], unique=False)
    op.create_index(op.f('ix_predicted_events_event_type'), 'predicted_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_predicted_events_status'), 'predicted_events', ['status'], unique=False)
    op.create_index(op.f('ix_predicted_events_created_at'), 'predicted_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_predicted_events_expires_at'), 'predicted_events', ['expires_at'], unique=False)

    # Create pattern_events table
    op.create_table('pattern_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pattern_id', sa.Integer(), nullable=False),
        sa.Column('impact_card_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('impact_areas', sa.JSON(), nullable=True),
        sa.Column('key_metrics', sa.JSON(), nullable=True),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['impact_card_id'], ['impact_cards.id'], ),
        sa.ForeignKeyConstraint(['pattern_id'], ['competitor_patterns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pattern_events_id'), 'pattern_events', ['id'], unique=False)
    op.create_index(op.f('ix_pattern_events_pattern_id'), 'pattern_events', ['pattern_id'], unique=False)
    op.create_index(op.f('ix_pattern_events_impact_card_id'), 'pattern_events', ['impact_card_id'], unique=False)
    op.create_index(op.f('ix_pattern_events_event_type'), 'pattern_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_pattern_events_event_date'), 'pattern_events', ['event_date'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('pattern_events')
    op.drop_table('predicted_events')
    op.drop_table('competitor_patterns')