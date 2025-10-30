"""Add industry template tables

Revision ID: 007_add_industry_templates
Revises: 006_add_model_registry
Create Date: 2025-10-30 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create industry_templates table
    op.create_table('industry_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('industry_sector', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_config', sa.JSON(), nullable=False),
        sa.Column('default_competitors', sa.JSON(), nullable=True),
        sa.Column('default_keywords', sa.JSON(), nullable=True),
        sa.Column('risk_categories', sa.JSON(), nullable=True),
        sa.Column('kpi_metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for industry_templates
    op.create_index(op.f('ix_industry_templates_id'), 'industry_templates', ['id'], unique=False)
    op.create_index(op.f('ix_industry_templates_name'), 'industry_templates', ['name'], unique=False)
    op.create_index(op.f('ix_industry_templates_industry_sector'), 'industry_templates', ['industry_sector'], unique=False)
    op.create_index(op.f('ix_industry_templates_created_at'), 'industry_templates', ['created_at'], unique=False)
    
    # Create template_applications table
    op.create_table('template_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('customizations', sa.JSON(), nullable=True),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['industry_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for template_applications
    op.create_index(op.f('ix_template_applications_id'), 'template_applications', ['id'], unique=False)
    op.create_index(op.f('ix_template_applications_template_id'), 'template_applications', ['template_id'], unique=False)
    op.create_index(op.f('ix_template_applications_workspace_id'), 'template_applications', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_template_applications_user_id'), 'template_applications', ['user_id'], unique=False)
    op.create_index(op.f('ix_template_applications_applied_at'), 'template_applications', ['applied_at'], unique=False)
    op.create_index(op.f('ix_template_applications_status'), 'template_applications', ['status'], unique=False)


def downgrade() -> None:
    # Drop template_applications table and indexes
    op.drop_index(op.f('ix_template_applications_status'), table_name='template_applications')
    op.drop_index(op.f('ix_template_applications_applied_at'), table_name='template_applications')
    op.drop_index(op.f('ix_template_applications_user_id'), table_name='template_applications')
    op.drop_index(op.f('ix_template_applications_workspace_id'), table_name='template_applications')
    op.drop_index(op.f('ix_template_applications_template_id'), table_name='template_applications')
    op.drop_index(op.f('ix_template_applications_id'), table_name='template_applications')
    op.drop_table('template_applications')
    
    # Drop industry_templates table and indexes
    op.drop_index(op.f('ix_industry_templates_created_at'), table_name='industry_templates')
    op.drop_index(op.f('ix_industry_templates_industry_sector'), table_name='industry_templates')
    op.drop_index(op.f('ix_industry_templates_name'), table_name='industry_templates')
    op.drop_index(op.f('ix_industry_templates_id'), table_name='industry_templates')
    op.drop_table('industry_templates')