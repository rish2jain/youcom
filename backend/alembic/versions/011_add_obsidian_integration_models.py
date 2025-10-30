"""Add Obsidian integration models

Revision ID: 011_add_obsidian_integration_models
Revises: 010_add_hubspot_integration_models
Create Date: 2024-10-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    # Create obsidian_integrations table
    op.create_table('obsidian_integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vault_name', sa.String(length=255), nullable=False),
        sa.Column('vault_path', sa.String(length=500), nullable=False),
        sa.Column('vault_id', sa.String(length=100), nullable=True),
        sa.Column('api_endpoint', sa.String(length=500), nullable=True),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('api_port', sa.Integer(), nullable=True),
        sa.Column('sync_enabled', sa.Boolean(), nullable=True),
        sa.Column('auto_sync', sa.Boolean(), nullable=True),
        sa.Column('sync_frequency_minutes', sa.Integer(), nullable=True),
        sa.Column('base_folder', sa.String(length=255), nullable=True),
        sa.Column('company_folder_template', sa.String(length=255), nullable=True),
        sa.Column('market_folder_template', sa.String(length=255), nullable=True),
        sa.Column('trend_folder_template', sa.String(length=255), nullable=True),
        sa.Column('note_templates', sa.JSON(), nullable=True),
        sa.Column('tag_hierarchy', sa.JSON(), nullable=True),
        sa.Column('enable_backlinks', sa.Boolean(), nullable=True),
        sa.Column('backlink_format', sa.String(length=50), nullable=True),
        sa.Column('auto_create_index', sa.Boolean(), nullable=True),
        sa.Column('include_source_links', sa.Boolean(), nullable=True),
        sa.Column('include_metadata', sa.Boolean(), nullable=True),
        sa.Column('include_timestamps', sa.Boolean(), nullable=True),
        sa.Column('markdown_style', sa.String(length=50), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_successful_sync_at', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=True),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=True),
        sa.Column('total_notes_created', sa.Integer(), nullable=True),
        sa.Column('total_notes_updated', sa.Integer(), nullable=True),
        sa.Column('total_backlinks_created', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_obsidian_integrations_user_id'), 'obsidian_integrations', ['user_id'], unique=False)
    
    # Create obsidian_sync_logs table
    op.create_table('obsidian_sync_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sync_type', sa.String(length=50), nullable=False),
        sa.Column('operation', sa.String(length=20), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=True),
        sa.Column('content_id', sa.String(length=100), nullable=True),
        sa.Column('note_path', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('notes_processed', sa.Integer(), nullable=True),
        sa.Column('notes_created', sa.Integer(), nullable=True),
        sa.Column('notes_updated', sa.Integer(), nullable=True),
        sa.Column('backlinks_created', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('sync_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['obsidian_integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_obsidian_sync_logs_integration_id'), 'obsidian_sync_logs', ['integration_id'], unique=False)
    op.create_index(op.f('ix_obsidian_sync_logs_started_at'), 'obsidian_sync_logs', ['started_at'], unique=False)
    
    # Create obsidian_note_mappings table
    op.create_table('obsidian_note_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('content_id', sa.String(length=100), nullable=False),
        sa.Column('content_title', sa.String(length=500), nullable=True),
        sa.Column('note_path', sa.String(length=500), nullable=False),
        sa.Column('note_filename', sa.String(length=255), nullable=False),
        sa.Column('note_folder', sa.String(length=500), nullable=True),
        sa.Column('obsidian_note_id', sa.String(length=100), nullable=True),
        sa.Column('note_hash', sa.String(length=64), nullable=True),
        sa.Column('created_in_obsidian_at', sa.DateTime(), nullable=False),
        sa.Column('last_updated_in_obsidian_at', sa.DateTime(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('sync_version', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('needs_update', sa.Boolean(), nullable=True),
        sa.Column('backlinks_to', sa.JSON(), nullable=True),
        sa.Column('backlinks_from', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['obsidian_integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_obsidian_note_mappings_content_type'), 'obsidian_note_mappings', ['content_type'], unique=False)
    op.create_index(op.f('ix_obsidian_note_mappings_content_id'), 'obsidian_note_mappings', ['content_id'], unique=False)
    op.create_index(op.f('ix_obsidian_note_mappings_integration_id'), 'obsidian_note_mappings', ['integration_id'], unique=False)
    
    # Create obsidian_note_templates table
    op.create_table('obsidian_note_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_name', sa.String(length=255), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_content', sa.Text(), nullable=False),
        sa.Column('frontmatter_template', sa.Text(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('required_fields', sa.JSON(), nullable=True),
        sa.Column('default_tags', sa.JSON(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['obsidian_integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_obsidian_note_templates_template_type'), 'obsidian_note_templates', ['template_type'], unique=False)
    op.create_index(op.f('ix_obsidian_note_templates_integration_id'), 'obsidian_note_templates', ['integration_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_obsidian_note_templates_integration_id'), table_name='obsidian_note_templates')
    op.drop_index(op.f('ix_obsidian_note_templates_template_type'), table_name='obsidian_note_templates')
    op.drop_table('obsidian_note_templates')
    
    op.drop_index(op.f('ix_obsidian_note_mappings_integration_id'), table_name='obsidian_note_mappings')
    op.drop_index(op.f('ix_obsidian_note_mappings_content_id'), table_name='obsidian_note_mappings')
    op.drop_index(op.f('ix_obsidian_note_mappings_content_type'), table_name='obsidian_note_mappings')
    op.drop_table('obsidian_note_mappings')
    
    op.drop_index(op.f('ix_obsidian_sync_logs_started_at'), table_name='obsidian_sync_logs')
    op.drop_index(op.f('ix_obsidian_sync_logs_integration_id'), table_name='obsidian_sync_logs')
    op.drop_table('obsidian_sync_logs')
    
    op.drop_index(op.f('ix_obsidian_integrations_user_id'), table_name='obsidian_integrations')
    op.drop_table('obsidian_integrations')