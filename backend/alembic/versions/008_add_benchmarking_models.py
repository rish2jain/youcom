"""add_benchmarking_models

Revision ID: 008
Revises: 007
Create Date: 2025-10-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Create benchmark_metrics table
    op.create_table('benchmark_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_category', sa.String(length=50), nullable=False),
        sa.Column('source_system', sa.String(length=50), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('measurement_timestamp', sa.DateTime(), nullable=False),
        sa.Column('time_period', sa.String(length=20), nullable=False),
        sa.Column('workspace_id', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.String(length=50), nullable=True),
        sa.Column('industry_sector', sa.String(length=50), nullable=True),
        sa.Column('metric_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_benchmark_metrics_created_at'), 'benchmark_metrics', ['created_at'], unique=False)
    op.create_index(op.f('ix_benchmark_metrics_id'), 'benchmark_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_benchmark_metrics_industry_sector'), 'benchmark_metrics', ['industry_sector'], unique=False)
    op.create_index(op.f('ix_benchmark_metrics_measurement_timestamp'), 'benchmark_metrics', ['measurement_timestamp'], unique=False)
    op.create_index(op.f('ix_benchmark_metrics_metric_category'), 'benchmark_metrics', ['metric_category'], unique=False)
    op.create_index(op.f('ix_benchmark_metrics_metric_id'), 'benchmark_metrics', ['metric_id'], unique=True)
    op.create_index(op.f('ix_benchmark_metrics_metric_name'), 'benchmark_metrics', ['metric_name'], unique=False)
    op.create_index(op.f('ix_benchmark_metrics_source_system'), 'benchmark_metrics', ['source_system'], unique=False)
    op.create_index(op.f('ix_benchmark_metrics_user_id'), 'benchmark_metrics', ['user_id'], unique=False)
    op.create_index(op.f('ix_benchmark_metrics_workspace_id'), 'benchmark_metrics', ['workspace_id'], unique=False)
    op.create_index('idx_industry_metric', 'benchmark_metrics', ['industry_sector', 'metric_name'], unique=False)
    op.create_index('idx_metric_time_category', 'benchmark_metrics', ['metric_name', 'measurement_timestamp', 'metric_category'], unique=False)
    op.create_index('idx_workspace_time', 'benchmark_metrics', ['workspace_id', 'measurement_timestamp'], unique=False)

    # Create industry_benchmarks table
    op.create_table('industry_benchmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('benchmark_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('industry_sector', sa.String(length=50), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('benchmark_type', sa.String(length=30), nullable=False),
        sa.Column('benchmark_value', sa.Float(), nullable=False),
        sa.Column('percentile_rank', sa.Integer(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('data_freshness_days', sa.Integer(), nullable=False),
        sa.Column('benchmark_period_start', sa.DateTime(), nullable=False),
        sa.Column('benchmark_period_end', sa.DateTime(), nullable=False),
        sa.Column('data_sources', sa.JSON(), nullable=True),
        sa.Column('calculation_method', sa.Text(), nullable=True),
        sa.Column('benchmark_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_industry_benchmarks_benchmark_id'), 'industry_benchmarks', ['benchmark_id'], unique=True)
    op.create_index(op.f('ix_industry_benchmarks_benchmark_type'), 'industry_benchmarks', ['benchmark_type'], unique=False)
    op.create_index(op.f('ix_industry_benchmarks_created_at'), 'industry_benchmarks', ['created_at'], unique=False)
    op.create_index(op.f('ix_industry_benchmarks_id'), 'industry_benchmarks', ['id'], unique=False)
    op.create_index(op.f('ix_industry_benchmarks_industry_sector'), 'industry_benchmarks', ['industry_sector'], unique=False)
    op.create_index(op.f('ix_industry_benchmarks_metric_name'), 'industry_benchmarks', ['metric_name'], unique=False)
    op.create_index('idx_benchmark_period', 'industry_benchmarks', ['benchmark_period_start', 'benchmark_period_end'], unique=False)
    op.create_index('idx_industry_metric_type', 'industry_benchmarks', ['industry_sector', 'metric_name', 'benchmark_type'], unique=False)

    # Create trend_analyses table
    op.create_table('trend_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=50), nullable=True),
        sa.Column('entity_type', sa.String(length=20), nullable=False),
        sa.Column('trend_direction', sa.String(length=20), nullable=False),
        sa.Column('trend_strength', sa.Float(), nullable=False),
        sa.Column('trend_confidence', sa.Float(), nullable=False),
        sa.Column('slope', sa.Float(), nullable=True),
        sa.Column('r_squared', sa.Float(), nullable=True),
        sa.Column('volatility', sa.Float(), nullable=False),
        sa.Column('analysis_period_start', sa.DateTime(), nullable=False),
        sa.Column('analysis_period_end', sa.DateTime(), nullable=False),
        sa.Column('data_points_count', sa.Integer(), nullable=False),
        sa.Column('key_insights', sa.JSON(), nullable=True),
        sa.Column('anomalies_detected', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('analysis_method', sa.String(length=50), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trend_analyses_analysis_id'), 'trend_analyses', ['analysis_id'], unique=True)
    op.create_index(op.f('ix_trend_analyses_analysis_period_end'), 'trend_analyses', ['analysis_period_end'], unique=False)
    op.create_index(op.f('ix_trend_analyses_analysis_period_start'), 'trend_analyses', ['analysis_period_start'], unique=False)
    op.create_index(op.f('ix_trend_analyses_created_at'), 'trend_analyses', ['created_at'], unique=False)
    op.create_index(op.f('ix_trend_analyses_entity_id'), 'trend_analyses', ['entity_id'], unique=False)
    op.create_index(op.f('ix_trend_analyses_entity_type'), 'trend_analyses', ['entity_type'], unique=False)
    op.create_index(op.f('ix_trend_analyses_id'), 'trend_analyses', ['id'], unique=False)
    op.create_index(op.f('ix_trend_analyses_metric_name'), 'trend_analyses', ['metric_name'], unique=False)
    op.create_index('idx_entity_metric_period', 'trend_analyses', ['entity_id', 'metric_name', 'analysis_period_start'], unique=False)
    op.create_index('idx_trend_direction_strength', 'trend_analyses', ['trend_direction', 'trend_strength'], unique=False)

    # Create anomaly_detections table
    op.create_table('anomaly_detections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('anomaly_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=50), nullable=True),
        sa.Column('entity_type', sa.String(length=20), nullable=False),
        sa.Column('anomaly_type', sa.String(length=30), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('anomaly_score', sa.Float(), nullable=False),
        sa.Column('expected_value', sa.Float(), nullable=True),
        sa.Column('actual_value', sa.Float(), nullable=False),
        sa.Column('deviation_percentage', sa.Float(), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('anomaly_start', sa.DateTime(), nullable=True),
        sa.Column('anomaly_end', sa.DateTime(), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('root_cause_analysis', sa.Text(), nullable=True),
        sa.Column('resolution_status', sa.String(length=20), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('alert_sent', sa.Boolean(), nullable=True),
        sa.Column('alert_recipients', sa.JSON(), nullable=True),
        sa.Column('alert_timestamp', sa.DateTime(), nullable=True),
        sa.Column('detection_method', sa.String(length=50), nullable=False),
        sa.Column('detection_parameters', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_anomaly_detections_alert_sent'), 'anomaly_detections', ['alert_sent'], unique=False)
    op.create_index(op.f('ix_anomaly_detections_anomaly_id'), 'anomaly_detections', ['anomaly_id'], unique=True)
    op.create_index(op.f('ix_anomaly_detections_anomaly_type'), 'anomaly_detections', ['anomaly_type'], unique=False)
    op.create_index(op.f('ix_anomaly_detections_created_at'), 'anomaly_detections', ['created_at'], unique=False)
    op.create_index(op.f('ix_anomaly_detections_detected_at'), 'anomaly_detections', ['detected_at'], unique=False)
    op.create_index(op.f('ix_anomaly_detections_entity_id'), 'anomaly_detections', ['entity_id'], unique=False)
    op.create_index(op.f('ix_anomaly_detections_entity_type'), 'anomaly_detections', ['entity_type'], unique=False)
    op.create_index(op.f('ix_anomaly_detections_id'), 'anomaly_detections', ['id'], unique=False)
    op.create_index(op.f('ix_anomaly_detections_metric_name'), 'anomaly_detections', ['metric_name'], unique=False)
    op.create_index(op.f('ix_anomaly_detections_resolution_status'), 'anomaly_detections', ['resolution_status'], unique=False)
    op.create_index(op.f('ix_anomaly_detections_severity'), 'anomaly_detections', ['severity'], unique=False)
    op.create_index('idx_detected_at_severity', 'anomaly_detections', ['detected_at', 'severity'], unique=False)
    op.create_index('idx_entity_anomaly_type', 'anomaly_detections', ['entity_id', 'anomaly_type'], unique=False)
    op.create_index('idx_metric_severity_status', 'anomaly_detections', ['metric_name', 'severity', 'resolution_status'], unique=False)

    # Create benchmark_comparisons table
    op.create_table('benchmark_comparisons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('comparison_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('entity_id', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=20), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('entity_value', sa.Float(), nullable=False),
        sa.Column('benchmark_value', sa.Float(), nullable=False),
        sa.Column('percentile_rank', sa.Float(), nullable=False),
        sa.Column('performance_rating', sa.String(length=20), nullable=False),
        sa.Column('improvement_potential', sa.Float(), nullable=False),
        sa.Column('industry_sector', sa.String(length=50), nullable=True),
        sa.Column('comparison_period_start', sa.DateTime(), nullable=False),
        sa.Column('comparison_period_end', sa.DateTime(), nullable=False),
        sa.Column('key_insights', sa.JSON(), nullable=True),
        sa.Column('improvement_recommendations', sa.JSON(), nullable=True),
        sa.Column('competitive_position', sa.String(length=50), nullable=True),
        sa.Column('benchmark_source', sa.String(length=50), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('comparison_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_benchmark_comparisons_comparison_id'), 'benchmark_comparisons', ['comparison_id'], unique=True)
    op.create_index(op.f('ix_benchmark_comparisons_created_at'), 'benchmark_comparisons', ['created_at'], unique=False)
    op.create_index(op.f('ix_benchmark_comparisons_entity_id'), 'benchmark_comparisons', ['entity_id'], unique=False)
    op.create_index(op.f('ix_benchmark_comparisons_entity_type'), 'benchmark_comparisons', ['entity_type'], unique=False)
    op.create_index(op.f('ix_benchmark_comparisons_id'), 'benchmark_comparisons', ['id'], unique=False)
    op.create_index(op.f('ix_benchmark_comparisons_industry_sector'), 'benchmark_comparisons', ['industry_sector'], unique=False)
    op.create_index(op.f('ix_benchmark_comparisons_metric_name'), 'benchmark_comparisons', ['metric_name'], unique=False)
    op.create_index('idx_entity_metric_period', 'benchmark_comparisons', ['entity_id', 'metric_name', 'comparison_period_start'], unique=False)
    op.create_index('idx_industry_comparison', 'benchmark_comparisons', ['industry_sector', 'metric_name'], unique=False)
    op.create_index('idx_performance_rating', 'benchmark_comparisons', ['performance_rating', 'percentile_rank'], unique=False)


def downgrade():
    # Drop benchmark_comparisons table
    op.drop_index('idx_performance_rating', table_name='benchmark_comparisons')
    op.drop_index('idx_industry_comparison', table_name='benchmark_comparisons')
    op.drop_index('idx_entity_metric_period', table_name='benchmark_comparisons')
    op.drop_index(op.f('ix_benchmark_comparisons_metric_name'), table_name='benchmark_comparisons')
    op.drop_index(op.f('ix_benchmark_comparisons_industry_sector'), table_name='benchmark_comparisons')
    op.drop_index(op.f('ix_benchmark_comparisons_id'), table_name='benchmark_comparisons')
    op.drop_index(op.f('ix_benchmark_comparisons_entity_type'), table_name='benchmark_comparisons')
    op.drop_index(op.f('ix_benchmark_comparisons_entity_id'), table_name='benchmark_comparisons')
    op.drop_index(op.f('ix_benchmark_comparisons_created_at'), table_name='benchmark_comparisons')
    op.drop_index(op.f('ix_benchmark_comparisons_comparison_id'), table_name='benchmark_comparisons')
    op.drop_table('benchmark_comparisons')

    # Drop anomaly_detections table
    op.drop_index('idx_metric_severity_status', table_name='anomaly_detections')
    op.drop_index('idx_entity_anomaly_type', table_name='anomaly_detections')
    op.drop_index('idx_detected_at_severity', table_name='anomaly_detections')
    op.drop_index(op.f('ix_anomaly_detections_severity'), table_name='anomaly_detections')
    op.drop_index(op.f('ix_anomaly_detections_resolution_status'), table_name='anomaly_detections')
    op.drop_index(op.f('ix_anomaly_detections_metric_name'), table_name='anomaly_detections')
    op.drop_index(op.f('ix_anomaly_detections_id'), table_name='anomaly_detections')
    op.drop_index(op.f('ix_anomaly_detections_entity_type'), table_name='anomaly_detections')
    op.drop_index(op.f('ix_anomaly_detections_entity_id'), table_name='anomaly_detections')
    op.drop_index(op.f('ix_anomaly_detections_detected_at'), table_name='anomaly_detections')
    op.drop_index(op.f('ix_anomaly_detections_created_at'), table_name='anomaly_detections')
    op.drop_index(op.f('ix_anomaly_detections_anomaly_type'), table_name='anomaly_detections')
    op.drop_index(op.f('ix_anomaly_detections_anomaly_id'), table_name='anomaly_detections')
    op.drop_index(op.f('ix_anomaly_detections_alert_sent'), table_name='anomaly_detections')
    op.drop_table('anomaly_detections')

    # Drop trend_analyses table
    op.drop_index('idx_trend_direction_strength', table_name='trend_analyses')
    op.drop_index('idx_entity_metric_period', table_name='trend_analyses')
    op.drop_index(op.f('ix_trend_analyses_metric_name'), table_name='trend_analyses')
    op.drop_index(op.f('ix_trend_analyses_id'), table_name='trend_analyses')
    op.drop_index(op.f('ix_trend_analyses_entity_type'), table_name='trend_analyses')
    op.drop_index(op.f('ix_trend_analyses_entity_id'), table_name='trend_analyses')
    op.drop_index(op.f('ix_trend_analyses_created_at'), table_name='trend_analyses')
    op.drop_index(op.f('ix_trend_analyses_analysis_period_start'), table_name='trend_analyses')
    op.drop_index(op.f('ix_trend_analyses_analysis_period_end'), table_name='trend_analyses')
    op.drop_index(op.f('ix_trend_analyses_analysis_id'), table_name='trend_analyses')
    op.drop_table('trend_analyses')

    # Drop industry_benchmarks table
    op.drop_index('idx_industry_metric_type', table_name='industry_benchmarks')
    op.drop_index('idx_benchmark_period', table_name='industry_benchmarks')
    op.drop_index(op.f('ix_industry_benchmarks_metric_name'), table_name='industry_benchmarks')
    op.drop_index(op.f('ix_industry_benchmarks_industry_sector'), table_name='industry_benchmarks')
    op.drop_index(op.f('ix_industry_benchmarks_id'), table_name='industry_benchmarks')
    op.drop_index(op.f('ix_industry_benchmarks_created_at'), table_name='industry_benchmarks')
    op.drop_index(op.f('ix_industry_benchmarks_benchmark_type'), table_name='industry_benchmarks')
    op.drop_index(op.f('ix_industry_benchmarks_benchmark_id'), table_name='industry_benchmarks')
    op.drop_table('industry_benchmarks')

    # Drop benchmark_metrics table
    op.drop_index('idx_workspace_time', table_name='benchmark_metrics')
    op.drop_index('idx_metric_time_category', table_name='benchmark_metrics')
    op.drop_index('idx_industry_metric', table_name='benchmark_metrics')
    op.drop_index(op.f('ix_benchmark_metrics_workspace_id'), table_name='benchmark_metrics')
    op.drop_index(op.f('ix_benchmark_metrics_user_id'), table_name='benchmark_metrics')
    op.drop_index(op.f('ix_benchmark_metrics_source_system'), table_name='benchmark_metrics')
    op.drop_index(op.f('ix_benchmark_metrics_metric_name'), table_name='benchmark_metrics')
    op.drop_index(op.f('ix_benchmark_metrics_metric_id'), table_name='benchmark_metrics')
    op.drop_index(op.f('ix_benchmark_metrics_metric_category'), table_name='benchmark_metrics')
    op.drop_index(op.f('ix_benchmark_metrics_measurement_timestamp'), table_name='benchmark_metrics')
    op.drop_index(op.f('ix_benchmark_metrics_industry_sector'), table_name='benchmark_metrics')
    op.drop_index(op.f('ix_benchmark_metrics_id'), table_name='benchmark_metrics')
    op.drop_index(op.f('ix_benchmark_metrics_created_at'), table_name='benchmark_metrics')
    op.drop_table('benchmark_metrics')