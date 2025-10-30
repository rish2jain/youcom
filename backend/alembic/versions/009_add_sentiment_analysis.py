"""Add sentiment analysis models

Revision ID: 009_add_sentiment_analysis
Revises: 008_add_benchmarking_models
Create Date: 2025-10-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sentiment_analyses table
    op.create_table('sentiment_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('entity_name', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('sentiment_label', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('processing_timestamp', sa.DateTime(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('analysis_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sentiment_entity_time', 'sentiment_analyses', ['entity_name', 'processing_timestamp'])
    op.create_index('idx_sentiment_content_type', 'sentiment_analyses', ['content_type', 'processing_timestamp'])
    op.create_index('idx_sentiment_score_confidence', 'sentiment_analyses', ['sentiment_score', 'confidence'])
    op.create_index(op.f('ix_sentiment_analyses_content_id'), 'sentiment_analyses', ['content_id'])
    op.create_index(op.f('ix_sentiment_analyses_entity_name'), 'sentiment_analyses', ['entity_name'])
    op.create_index(op.f('ix_sentiment_analyses_id'), 'sentiment_analyses', ['id'])
    
    # Add CHECK constraints for sentiment_analyses
    op.create_check_constraint('ck_sentiment_score_range', 'sentiment_analyses', 'sentiment_score >= -1 AND sentiment_score <= 1')
    op.create_check_constraint('ck_confidence_range', 'sentiment_analyses', 'confidence >= 0 AND confidence <= 1')

    # Create sentiment_trends table
    op.create_table('sentiment_trends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_name', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('timeframe', sa.String(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('average_sentiment', sa.Float(), nullable=False),
        sa.Column('sentiment_volatility', sa.Float(), nullable=False),
        sa.Column('total_mentions', sa.Integer(), nullable=False),
        sa.Column('positive_mentions', sa.Integer(), nullable=True),
        sa.Column('negative_mentions', sa.Integer(), nullable=True),
        sa.Column('neutral_mentions', sa.Integer(), nullable=True),
        sa.Column('trend_direction', sa.String(), nullable=True),
        sa.Column('trend_strength', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('sentiment_analysis_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['sentiment_analysis_id'], ['sentiment_analyses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trend_entity_timeframe', 'sentiment_trends', ['entity_name', 'timeframe', 'period_start'])
    op.create_index('idx_trend_period', 'sentiment_trends', ['period_start', 'period_end'])
    op.create_index('idx_trend_direction', 'sentiment_trends', ['trend_direction', 'trend_strength'])
    op.create_index(op.f('ix_sentiment_trends_entity_name'), 'sentiment_trends', ['entity_name'])
    op.create_index(op.f('ix_sentiment_trends_id'), 'sentiment_trends', ['id'])

    # Create sentiment_alerts table
    op.create_table('sentiment_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_name', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('alert_severity', sa.String(), nullable=False),
        sa.Column('current_sentiment', sa.Float(), nullable=False),
        sa.Column('previous_sentiment', sa.Float(), nullable=True),
        sa.Column('sentiment_change', sa.Float(), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=True),
        sa.Column('alert_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alert_entity_severity', 'sentiment_alerts', ['entity_name', 'alert_severity'])
    op.create_index('idx_alert_triggered', 'sentiment_alerts', ['triggered_at', 'is_resolved'])
    op.create_index('idx_alert_type', 'sentiment_alerts', ['alert_type', 'triggered_at'])
    op.create_index(op.f('ix_sentiment_alerts_entity_name'), 'sentiment_alerts', ['entity_name'])
    op.create_index(op.f('ix_sentiment_alerts_id'), 'sentiment_alerts', ['id'])

    # Create sentiment_processing_queue table
    op.create_table('sentiment_processing_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('queue_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_id')
    )
    op.create_index('idx_queue_status_priority', 'sentiment_processing_queue', ['status', 'priority', 'created_at'])
    op.create_index('idx_queue_processing', 'sentiment_processing_queue', ['status', 'started_at'])
    op.create_index(op.f('ix_sentiment_processing_queue_id'), 'sentiment_processing_queue', ['id'])


def downgrade() -> None:
    # Drop sentiment analysis tables in reverse order
    op.drop_table('sentiment_processing_queue')
    op.drop_table('sentiment_alerts')
    op.drop_table('sentiment_trends')
    
    # Drop CHECK constraints before dropping table
    op.drop_constraint('ck_confidence_range', 'sentiment_analyses', type_='check')
    op.drop_constraint('ck_sentiment_score_range', 'sentiment_analyses', type_='check')
    op.drop_table('sentiment_analyses')