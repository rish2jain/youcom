"""add_hubspot_integration_models

Revision ID: 010_add_hubspot_integration_models
Revises: 009_add_sentiment_analysis
Create Date: 2024-10-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    # Create hubspot_integrations table
    op.create_table('hubspot_integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hubspot_portal_id', sa.String(length=50), nullable=False),
        sa.Column('hubspot_account_name', sa.String(length=255), nullable=True),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('sync_enabled', sa.Boolean(), nullable=True),
        sa.Column('sync_frequency_minutes', sa.Integer(), nullable=True),
        sa.Column('custom_properties_created', sa.JSON(), nullable=True),
        sa.Column('workflow_mappings', sa.JSON(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_successful_sync_at', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=True),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=True),
        sa.Column('total_contacts_synced', sa.Integer(), nullable=True),
        sa.Column('total_companies_synced', sa.Integer(), nullable=True),
        sa.Column('total_workflows_triggered', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create hubspot_sync_logs table
    op.create_table('hubspot_sync_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sync_type', sa.String(length=50), nullable=False),
        sa.Column('direction', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('records_processed', sa.Integer(), nullable=True),
        sa.Column('records_successful', sa.Integer(), nullable=True),
        sa.Column('records_failed', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('sync_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['hubspot_integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create hubspot_custom_properties table
    op.create_table('hubspot_custom_properties',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hubspot_property_name', sa.String(length=255), nullable=False),
        sa.Column('hubspot_property_type', sa.String(length=50), nullable=False),
        sa.Column('hubspot_object_type', sa.String(length=50), nullable=False),
        sa.Column('cia_field_name', sa.String(length=255), nullable=False),
        sa.Column('cia_field_type', sa.String(length=50), nullable=False),
        sa.Column('property_label', sa.String(length=255), nullable=True),
        sa.Column('property_description', sa.Text(), nullable=True),
        sa.Column('property_options', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_in_hubspot_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['hubspot_integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create hubspot_workflow_triggers table
    op.create_table('hubspot_workflow_triggers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', sa.String(length=50), nullable=False),
        sa.Column('workflow_name', sa.String(length=255), nullable=True),
        sa.Column('trigger_type', sa.String(length=100), nullable=False),
        sa.Column('hubspot_object_type', sa.String(length=50), nullable=False),
        sa.Column('hubspot_object_id', sa.String(length=50), nullable=False),
        sa.Column('impact_card_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('competitive_event_type', sa.String(length=100), nullable=True),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('response_status_code', sa.Integer(), nullable=True),
        sa.Column('response_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['impact_card_id'], ['impact_cards.id'], ),
        sa.ForeignKeyConstraint(['integration_id'], ['hubspot_integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('hubspot_workflow_triggers')
    op.drop_table('hubspot_custom_properties')
    op.drop_table('hubspot_sync_logs')
    op.drop_table('hubspot_integrations')