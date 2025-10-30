"""Add model registry and A/B testing tables

Revision ID: 006_add_model_registry
Revises: 005_add_ml_training_models
Create Date: 2025-10-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ml_model_registry table
    op.create_table('ml_model_registry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.String(length=100), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('version', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deprecated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('performance_metrics', sa.JSON(), nullable=True),
        sa.Column('training_config', sa.JSON(), nullable=True),
        sa.Column('file_paths', sa.JSON(), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deployment_strategy', sa.String(length=20), nullable=True),
        sa.Column('parent_model_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for ml_model_registry
    op.create_index(op.f('ix_ml_model_registry_id'), 'ml_model_registry', ['id'], unique=False)
    op.create_index(op.f('ix_ml_model_registry_model_id'), 'ml_model_registry', ['model_id'], unique=True)
    op.create_index(op.f('ix_ml_model_registry_model_type'), 'ml_model_registry', ['model_type'], unique=False)
    op.create_index(op.f('ix_ml_model_registry_version'), 'ml_model_registry', ['version'], unique=False)
    op.create_index(op.f('ix_ml_model_registry_status'), 'ml_model_registry', ['status'], unique=False)
    op.create_index(op.f('ix_ml_model_registry_created_at'), 'ml_model_registry', ['created_at'], unique=False)
    op.create_index(op.f('ix_ml_model_registry_parent_model_id'), 'ml_model_registry', ['parent_model_id'], unique=False)
    
    # Create ml_ab_tests table
    op.create_table('ml_ab_tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.String(length=100), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('model_a_version', sa.String(length=100), nullable=False),
        sa.Column('model_b_version', sa.String(length=100), nullable=False),
        sa.Column('traffic_split', sa.Float(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('success_metrics', sa.JSON(), nullable=True),
        sa.Column('minimum_samples', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('winner_version', sa.String(length=100), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for ml_ab_tests
    op.create_index(op.f('ix_ml_ab_tests_id'), 'ml_ab_tests', ['id'], unique=False)
    op.create_index(op.f('ix_ml_ab_tests_test_id'), 'ml_ab_tests', ['test_id'], unique=True)
    op.create_index(op.f('ix_ml_ab_tests_model_type'), 'ml_ab_tests', ['model_type'], unique=False)
    op.create_index(op.f('ix_ml_ab_tests_status'), 'ml_ab_tests', ['status'], unique=False)
    
    # Add CHECK constraints for ml_ab_tests
    op.create_check_constraint('ck_ml_ab_tests_traffic_split', 'ml_ab_tests', 'traffic_split >= 0 AND traffic_split <= 1')
    op.create_check_constraint('ck_ml_ab_tests_date_order', 'ml_ab_tests', 'start_date < end_date')
    
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
    
    # Create indexes for ml_feature_store
    op.create_index(op.f('ix_ml_feature_store_id'), 'ml_feature_store', ['id'], unique=False)
    op.create_index(op.f('ix_ml_feature_store_entity_id'), 'ml_feature_store', ['entity_id'], unique=False)
    op.create_index(op.f('ix_ml_feature_store_entity_type'), 'ml_feature_store', ['entity_type'], unique=False)
    op.create_index(op.f('ix_ml_feature_store_feature_hash'), 'ml_feature_store', ['feature_hash'], unique=False)
    op.create_index(op.f('ix_ml_feature_store_extraction_timestamp'), 'ml_feature_store', ['extraction_timestamp'], unique=False)
    op.create_index(op.f('ix_ml_feature_store_created_at'), 'ml_feature_store', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop ml_feature_store table and indexes
    op.drop_index(op.f('ix_ml_feature_store_created_at'), table_name='ml_feature_store')
    op.drop_index(op.f('ix_ml_feature_store_extraction_timestamp'), table_name='ml_feature_store')
    op.drop_index(op.f('ix_ml_feature_store_feature_hash'), table_name='ml_feature_store')
    op.drop_index(op.f('ix_ml_feature_store_entity_type'), table_name='ml_feature_store')
    op.drop_index(op.f('ix_ml_feature_store_entity_id'), table_name='ml_feature_store')
    op.drop_index(op.f('ix_ml_feature_store_id'), table_name='ml_feature_store')
    op.drop_table('ml_feature_store')
    
    # Drop ml_ab_tests table and indexes
    op.drop_constraint('ck_ml_ab_tests_date_order', 'ml_ab_tests', type_='check')
    op.drop_constraint('ck_ml_ab_tests_traffic_split', 'ml_ab_tests', type_='check')
    op.drop_index(op.f('ix_ml_ab_tests_status'), table_name='ml_ab_tests')
    op.drop_index(op.f('ix_ml_ab_tests_model_type'), table_name='ml_ab_tests')
    op.drop_index(op.f('ix_ml_ab_tests_test_id'), table_name='ml_ab_tests')
    op.drop_index(op.f('ix_ml_ab_tests_id'), table_name='ml_ab_tests')
    op.drop_table('ml_ab_tests')
    
    # Drop ml_model_registry table and indexes
    op.drop_index(op.f('ix_ml_model_registry_parent_model_id'), table_name='ml_model_registry')
    op.drop_index(op.f('ix_ml_model_registry_created_at'), table_name='ml_model_registry')
    op.drop_index(op.f('ix_ml_model_registry_status'), table_name='ml_model_registry')
    op.drop_index(op.f('ix_ml_model_registry_version'), table_name='ml_model_registry')
    op.drop_index(op.f('ix_ml_model_registry_model_type'), table_name='ml_model_registry')
    op.drop_index(op.f('ix_ml_model_registry_model_id'), table_name='ml_model_registry')
    op.drop_index(op.f('ix_ml_model_registry_id'), table_name='ml_model_registry')
    op.drop_table('ml_model_registry')