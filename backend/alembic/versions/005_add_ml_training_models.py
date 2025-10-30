"""Add ML training data models

Revision ID: 005_add_ml_training_models
Revises: 004_add_enhancement_features
Create Date: 2025-01-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = '001'


def upgrade():
    # Create ml_feedback_records table
    op.create_table('ml_feedback_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('impact_card_id', sa.Integer(), nullable=False),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('original_value', sa.Float(), nullable=True),
        sa.Column('corrected_value', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('feedback_context', sa.JSON(), nullable=True),
        sa.Column('user_expertise_level', sa.String(length=20), nullable=True),
        sa.Column('feedback_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['impact_card_id'], ['impact_cards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_feedback_records_feedback_timestamp'), 'ml_feedback_records', ['feedback_timestamp'], unique=False)
    op.create_index(op.f('ix_ml_feedback_records_feedback_type'), 'ml_feedback_records', ['feedback_type'], unique=False)
    op.create_index(op.f('ix_ml_feedback_records_id'), 'ml_feedback_records', ['id'], unique=False)
    op.create_index(op.f('ix_ml_feedback_records_impact_card_id'), 'ml_feedback_records', ['impact_card_id'], unique=False)
    op.create_index(op.f('ix_ml_feedback_records_processed'), 'ml_feedback_records', ['processed'], unique=False)
    op.create_index(op.f('ix_ml_feedback_records_user_id'), 'ml_feedback_records', ['user_id'], unique=False)
    
    # Create composite indexes for efficient querying
    op.create_index('idx_feedback_user_timestamp', 'ml_feedback_records', ['user_id', 'feedback_timestamp'], unique=False)
    op.create_index('idx_feedback_processed_timestamp', 'ml_feedback_records', ['processed', 'feedback_timestamp'], unique=False)

    # Create ml_performance_metrics table
    op.create_table('ml_performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(length=100), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('metric_name', sa.String(length=50), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('evaluation_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('dataset_size', sa.Integer(), nullable=True),
        sa.Column('evaluation_type', sa.String(length=30), nullable=True),
        sa.Column('metric_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_performance_metrics_evaluation_timestamp'), 'ml_performance_metrics', ['evaluation_timestamp'], unique=False)
    op.create_index(op.f('ix_ml_performance_metrics_id'), 'ml_performance_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_ml_performance_metrics_metric_name'), 'ml_performance_metrics', ['metric_name'], unique=False)
    op.create_index(op.f('ix_ml_performance_metrics_model_type'), 'ml_performance_metrics', ['model_type'], unique=False)
    op.create_index(op.f('ix_ml_performance_metrics_model_version'), 'ml_performance_metrics', ['model_version'], unique=False)
    
    # Create composite index for efficient querying
    op.create_index('idx_performance_model_timestamp', 'ml_performance_metrics', ['model_version', 'evaluation_timestamp'], unique=False)

    # Create ml_training_jobs table
    op.create_table('ml_training_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(length=100), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('previous_model_version', sa.String(length=100), nullable=True),
        sa.Column('new_model_version', sa.String(length=100), nullable=True),
        sa.Column('training_data_size', sa.Integer(), nullable=True),
        sa.Column('validation_data_size', sa.Integer(), nullable=True),
        sa.Column('performance_improvement', sa.Float(), nullable=True),
        sa.Column('baseline_metric_value', sa.Float(), nullable=True),
        sa.Column('new_metric_value', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('training_config', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_training_jobs_created_at'), 'ml_training_jobs', ['created_at'], unique=False)
    op.create_index(op.f('ix_ml_training_jobs_id'), 'ml_training_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_ml_training_jobs_job_id'), 'ml_training_jobs', ['job_id'], unique=True)
    op.create_index(op.f('ix_ml_training_jobs_model_type'), 'ml_training_jobs', ['model_type'], unique=False)
    op.create_index(op.f('ix_ml_training_jobs_status'), 'ml_training_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_ml_training_jobs_trigger_type'), 'ml_training_jobs', ['trigger_type'], unique=False)
    
    # Create composite indexes for efficient querying
    op.create_index('idx_training_status_created', 'ml_training_jobs', ['status', 'created_at'], unique=False)
    op.create_index('idx_training_model_trigger', 'ml_training_jobs', ['model_type', 'trigger_type'], unique=False)

    # Create ml_feature_store table
    op.create_table('ml_feature_store',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('feature_hash', sa.String(length=32), nullable=False),
        sa.Column('features_json', sa.JSON(), nullable=False),
        sa.Column('extraction_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('feature_count', sa.Integer(), nullable=False),
        sa.Column('avg_confidence', sa.Float(), nullable=False),
        sa.Column('feature_types', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ml_feature_store_created_at'), 'ml_feature_store', ['created_at'], unique=False)
    op.create_index(op.f('ix_ml_feature_store_entity_id'), 'ml_feature_store', ['entity_id'], unique=False)
    op.create_index(op.f('ix_ml_feature_store_entity_type'), 'ml_feature_store', ['entity_type'], unique=False)
    op.create_index(op.f('ix_ml_feature_store_extraction_timestamp'), 'ml_feature_store', ['extraction_timestamp'], unique=False)
    op.create_index(op.f('ix_ml_feature_store_feature_hash'), 'ml_feature_store', ['feature_hash'], unique=False)
    op.create_index(op.f('ix_ml_feature_store_id'), 'ml_feature_store', ['id'], unique=False)


def downgrade():
    # Drop indexes first
    op.drop_index('idx_training_model_trigger', table_name='ml_training_jobs')
    op.drop_index('idx_training_status_created', table_name='ml_training_jobs')
    op.drop_index(op.f('ix_ml_training_jobs_trigger_type'), table_name='ml_training_jobs')
    op.drop_index(op.f('ix_ml_training_jobs_status'), table_name='ml_training_jobs')
    op.drop_index(op.f('ix_ml_training_jobs_model_type'), table_name='ml_training_jobs')
    op.drop_index(op.f('ix_ml_training_jobs_job_id'), table_name='ml_training_jobs')
    op.drop_index(op.f('ix_ml_training_jobs_id'), table_name='ml_training_jobs')
    op.drop_index(op.f('ix_ml_training_jobs_created_at'), table_name='ml_training_jobs')
    
    op.drop_index('idx_performance_model_timestamp', table_name='ml_performance_metrics')
    op.drop_index(op.f('ix_ml_performance_metrics_model_version'), table_name='ml_performance_metrics')
    op.drop_index(op.f('ix_ml_performance_metrics_model_type'), table_name='ml_performance_metrics')
    op.drop_index(op.f('ix_ml_performance_metrics_metric_name'), table_name='ml_performance_metrics')
    op.drop_index(op.f('ix_ml_performance_metrics_id'), table_name='ml_performance_metrics')
    op.drop_index(op.f('ix_ml_performance_metrics_evaluation_timestamp'), table_name='ml_performance_metrics')
    
    op.drop_index('idx_feedback_processed_timestamp', table_name='ml_feedback_records')
    op.drop_index('idx_feedback_user_timestamp', table_name='ml_feedback_records')
    op.drop_index(op.f('ix_ml_feedback_records_user_id'), table_name='ml_feedback_records')
    op.drop_index(op.f('ix_ml_feedback_records_processed'), table_name='ml_feedback_records')
    op.drop_index(op.f('ix_ml_feedback_records_impact_card_id'), table_name='ml_feedback_records')
    op.drop_index(op.f('ix_ml_feedback_records_id'), table_name='ml_feedback_records')
    op.drop_index(op.f('ix_ml_feedback_records_feedback_type'), table_name='ml_feedback_records')
    op.drop_index(op.f('ix_ml_feedback_records_feedback_timestamp'), table_name='ml_feedback_records')
    
    # Drop feature store indexes and table
    op.drop_index(op.f('ix_ml_feature_store_id'), table_name='ml_feature_store')
    op.drop_index(op.f('ix_ml_feature_store_feature_hash'), table_name='ml_feature_store')
    op.drop_index(op.f('ix_ml_feature_store_extraction_timestamp'), table_name='ml_feature_store')
    op.drop_index(op.f('ix_ml_feature_store_entity_type'), table_name='ml_feature_store')
    op.drop_index(op.f('ix_ml_feature_store_entity_id'), table_name='ml_feature_store')
    op.drop_index(op.f('ix_ml_feature_store_created_at'), table_name='ml_feature_store')
    
    # Drop tables
    op.drop_table('ml_feature_store')
    op.drop_table('ml_training_jobs')
    op.drop_table('ml_performance_metrics')
    op.drop_table('ml_feedback_records')