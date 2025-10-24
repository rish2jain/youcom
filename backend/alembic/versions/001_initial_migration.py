"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create watch_items table
    op.create_table('watch_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('competitor_name', sa.String(length=255), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_checked', sa.DateTime(timezone=True), nullable=True),
        sa.Column('check_frequency', sa.Integer(), nullable=True),
        sa.Column('risk_threshold', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watch_items_id'), 'watch_items', ['id'], unique=False)
    op.create_index(op.f('ix_watch_items_competitor_name'), 'watch_items', ['competitor_name'], unique=False)
    op.create_index(op.f('ix_watch_items_is_active'), 'watch_items', ['is_active'], unique=False)

    # Create impact_cards table
    op.create_table('impact_cards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('watch_item_id', sa.Integer(), nullable=False),
        sa.Column('competitor_name', sa.String(length=255), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('confidence_score', sa.Integer(), nullable=False),
        sa.Column('impact_areas', sa.JSON(), nullable=True),
        sa.Column('key_insights', sa.JSON(), nullable=True),
        sa.Column('recommended_actions', sa.JSON(), nullable=True),
        sa.Column('total_sources', sa.Integer(), nullable=True),
        sa.Column('source_breakdown', sa.JSON(), nullable=True),
        sa.Column('api_usage', sa.JSON(), nullable=True),
        sa.Column('processing_time', sa.String(length=100), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['watch_item_id'], ['watch_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_impact_cards_id'), 'impact_cards', ['id'], unique=False)
    op.create_index(op.f('ix_impact_cards_watch_item_id'), 'impact_cards', ['watch_item_id'], unique=False)
    op.create_index(op.f('ix_impact_cards_competitor_name'), 'impact_cards', ['competitor_name'], unique=False)
    op.create_index(op.f('ix_impact_cards_risk_score'), 'impact_cards', ['risk_score'], unique=False)
    op.create_index(op.f('ix_impact_cards_created_at'), 'impact_cards', ['created_at'], unique=False)

    # Create company_research table
    op.create_table('company_research',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('search_results', sa.JSON(), nullable=True),
        sa.Column('research_report', sa.JSON(), nullable=True),
        sa.Column('total_sources', sa.Integer(), nullable=True),
        sa.Column('api_usage', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_research_id'), 'company_research', ['id'], unique=False)
    op.create_index(op.f('ix_company_research_company_name'), 'company_research', ['company_name'], unique=False)
    op.create_index(op.f('ix_company_research_created_at'), 'company_research', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_company_research_created_at'), table_name='company_research')
    op.drop_index(op.f('ix_company_research_company_name'), table_name='company_research')
    op.drop_index(op.f('ix_company_research_id'), table_name='company_research')
    op.drop_table('company_research')
    
    op.drop_index(op.f('ix_impact_cards_created_at'), table_name='impact_cards')
    op.drop_index(op.f('ix_impact_cards_risk_score'), table_name='impact_cards')
    op.drop_index(op.f('ix_impact_cards_competitor_name'), table_name='impact_cards')
    op.drop_index(op.f('ix_impact_cards_watch_item_id'), table_name='impact_cards')
    op.drop_index(op.f('ix_impact_cards_id'), table_name='impact_cards')
    op.drop_table('impact_cards')
    
    op.drop_index(op.f('ix_watch_items_is_active'), table_name='watch_items')
    op.drop_index(op.f('ix_watch_items_competitor_name'), table_name='watch_items')
    op.drop_index(op.f('ix_watch_items_id'), table_name='watch_items')
    op.drop_table('watch_items')