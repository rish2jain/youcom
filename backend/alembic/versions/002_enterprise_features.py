"""Add enterprise features: users, workspaces, audit logs, dashboards, integrations

Revision ID: 002_enterprise
Revises: 001_initial_migration
Create Date: 2025-10-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_enterprise'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE userrole AS ENUM ('viewer', 'analyst', 'admin')")
    op.execute("CREATE TYPE workspacerole AS ENUM ('owner', 'admin', 'member', 'guest')")
    op.execute("CREATE TYPE auditaction AS ENUM ('create', 'read', 'update', 'delete', 'login', 'logout', 'export', 'share', 'permission_change', 'api_call')")
    op.execute("CREATE TYPE integrationtype AS ENUM ('slack', 'notion', 'salesforce', 'microsoft_teams', 'jira', 'webhook')")

    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('username', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('viewer', 'analyst', 'admin', name='userrole'), nullable=False, server_default='analyst'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sso_provider', sa.String(), nullable=True),
        sa.Column('sso_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Workspaces table
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_members', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('allow_guest_access', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Workspace members table
    op.create_table(
        'workspace_members',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.Enum('owner', 'admin', 'member', 'guest', name='workspacerole'), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('invited_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )

    # Shared watchlists table
    op.create_table(
        'shared_watchlists',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('watch_item_id', sa.Integer(), sa.ForeignKey('watch_items.id'), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Watchlist assignments table
    op.create_table(
        'watchlist_assignments',
        sa.Column('shared_watchlist_id', sa.Integer(), sa.ForeignKey('shared_watchlists.id'), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Comments table
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('shared_watchlist_id', sa.Integer(), sa.ForeignKey('shared_watchlists.id'), nullable=True),
        sa.Column('impact_card_id', sa.Integer(), sa.ForeignKey('impact_cards.id'), nullable=True),
        sa.Column('company_research_id', sa.Integer(), sa.ForeignKey('company_research.id'), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('annotations', sa.JSON(), nullable=True),
        sa.Column('parent_comment_id', sa.Integer(), sa.ForeignKey('comments.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_edited', sa.Integer(), nullable=False, server_default='0'),
    )

    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.Enum('create', 'read', 'update', 'delete', 'login', 'logout', 'export', 'share', 'permission_change', 'api_call', name='auditaction'), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id'), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('success', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, index=True),
    )

    # Dashboards table
    op.create_table(
        'dashboards',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('layout', sa.JSON(), nullable=False),
        sa.Column('widgets', sa.JSON(), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
    )

    # Scheduled reports table
    op.create_table(
        'scheduled_reports',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('dashboard_id', sa.Integer(), sa.ForeignKey('dashboards.id'), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('report_type', sa.String(), nullable=False),
        sa.Column('schedule_cron', sa.String(), nullable=False),
        sa.Column('timezone', sa.String(), nullable=False, server_default='UTC'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('recipient_emails', sa.JSON(), nullable=False),
        sa.Column('recipient_slack_channels', sa.JSON(), nullable=True),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('format', sa.String(), nullable=False, server_default='pdf'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_runs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_runs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_runs', sa.Integer(), nullable=False, server_default='0'),
    )

    # Integrations table
    op.create_table(
        'integrations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.Enum('slack', 'notion', 'salesforce', 'microsoft_teams', 'jira', 'webhook', name='integrationtype'), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('credentials', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_syncs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_syncs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_syncs', sa.Integer(), nullable=False, server_default='0'),
    )

    # Integration logs table
    op.create_table(
        'integration_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('integration_id', sa.Integer(), sa.ForeignKey('integrations.id'), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('request_data', sa.JSON(), nullable=True),
        sa.Column('response_data', sa.JSON(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('integration_logs')
    op.drop_table('integrations')
    op.drop_table('scheduled_reports')
    op.drop_table('dashboards')
    op.drop_table('audit_logs')
    op.drop_table('comments')
    op.drop_table('watchlist_assignments')
    op.drop_table('shared_watchlists')
    op.drop_table('workspace_members')
    op.drop_table('workspaces')
    op.drop_table('users')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS integrationtype")
    op.execute("DROP TYPE IF EXISTS auditaction")
    op.execute("DROP TYPE IF EXISTS workspacerole")
    op.execute("DROP TYPE IF EXISTS userrole")
