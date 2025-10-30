"""Advanced features integration

Revision ID: 003_advanced_features
Revises: 002_enterprise_features
Create Date: 2025-10-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_advanced_features'
down_revision = '002_enterprise_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure integration tables exist with all required columns
    op.execute("""
        CREATE TABLE IF NOT EXISTS integrations (
            id SERIAL PRIMARY KEY,
            workspace_id INTEGER NOT NULL REFERENCES workspaces(id),
            name VARCHAR NOT NULL,
            type VARCHAR NOT NULL,
            config JSON NOT NULL,
            credentials JSON,
            is_active BOOLEAN DEFAULT true,
            is_verified BOOLEAN DEFAULT false,
            last_sync_at TIMESTAMP WITH TIME ZONE,
            last_error TEXT,
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            total_syncs INTEGER DEFAULT 0,
            successful_syncs INTEGER DEFAULT 0,
            failed_syncs INTEGER DEFAULT 0
        );
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS integration_logs (
            id SERIAL PRIMARY KEY,
            integration_id INTEGER NOT NULL REFERENCES integrations(id),
            action VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            message TEXT,
            request_data JSON,
            response_data JSON,
            error_details JSON,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            duration_ms INTEGER
        );
    """)
    
    # Create indexes for better performance
    op.execute("CREATE INDEX IF NOT EXISTS idx_integrations_workspace_id ON integrations(workspace_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(type);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_integration_logs_integration_id ON integration_logs(integration_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_integration_logs_created_at ON integration_logs(created_at);")


def downgrade() -> None:
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_integration_logs_created_at;")
    op.execute("DROP INDEX IF EXISTS idx_integration_logs_integration_id;")
    op.execute("DROP INDEX IF EXISTS idx_integrations_type;")
    op.execute("DROP INDEX IF EXISTS idx_integrations_workspace_id;")
    
    # Drop tables
    op.execute("DROP TABLE IF EXISTS integration_logs;")
    op.execute("DROP TABLE IF EXISTS integrations;")