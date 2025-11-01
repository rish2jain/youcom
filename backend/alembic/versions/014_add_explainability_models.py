"""Add explainability models

Revision ID: 014_add_explainability_models
Revises: 013_add_predictive_intelligence_models
Create Date: 2025-10-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_add_explainability_models'
down_revision = '013_add_predictive_intelligence_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create reasoning_steps table
    op.create_table('reasoning_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('impact_card_id', sa.Integer(), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('step_type', sa.String(length=50), nullable=False),
        sa.Column('step_name', sa.String(length=255), nullable=False),
        sa.Column('factor_name', sa.String(length=255), nullable=False),
        sa.Column('factor_weight', sa.Float(), nullable=False),
        sa.Column('factor_contribution', sa.Float(), nullable=False),
        sa.Column('evidence_sources', sa.JSON(), nullable=True),
        sa.Column('reasoning_text', sa.Text(), nullable=False),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('uncertainty_flags', sa.JSON(), nullable=True),
        sa.Column('conflicting_evidence', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['impact_card_id'], ['impact_cards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reasoning_steps_id'), 'reasoning_steps', ['id'], unique=False)
    op.create_index(op.f('ix_reasoning_steps_impact_card_id'), 'reasoning_steps', ['impact_card_id'], unique=False)

    # Create source_credibility_analysis table
    op.create_table('source_credibility_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('impact_card_id', sa.Integer(), nullable=False),
        sa.Column('source_url', sa.String(length=2048), nullable=False),
        sa.Column('source_title', sa.String(length=512), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('tier_level', sa.String(length=20), nullable=False),
        sa.Column('credibility_score', sa.Float(), nullable=False),
        sa.Column('authority_score', sa.Float(), nullable=False),
        sa.Column('recency_score', sa.Float(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('validation_method', sa.String(length=100), nullable=False),
        sa.Column('quality_flags', sa.JSON(), nullable=True),
        sa.Column('warning_flags', sa.JSON(), nullable=True),
        sa.Column('conflicts_with', sa.JSON(), nullable=True),
        sa.Column('conflict_severity', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['impact_card_id'], ['impact_cards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_source_credibility_analysis_id'), 'source_credibility_analysis', ['id'], unique=False)
    op.create_index(op.f('ix_source_credibility_analysis_impact_card_id'), 'source_credibility_analysis', ['impact_card_id'], unique=False)

    # Create uncertainty_detections table
    op.create_table('uncertainty_detections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('impact_card_id', sa.Integer(), nullable=False),
        sa.Column('uncertainty_type', sa.String(length=50), nullable=False),
        sa.Column('uncertainty_level', sa.String(length=20), nullable=False),
        sa.Column('confidence_threshold', sa.Float(), nullable=False),
        sa.Column('affected_components', sa.JSON(), nullable=True),
        sa.Column('uncertainty_description', sa.Text(), nullable=False),
        sa.Column('human_validation_required', sa.Boolean(), nullable=True),
        sa.Column('recommended_actions', sa.JSON(), nullable=True),
        sa.Column('validation_priority', sa.String(length=20), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('resolution_method', sa.String(length=100), nullable=True),
        sa.Column('resolved_by', sa.String(length=100), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['impact_card_id'], ['impact_cards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_uncertainty_detections_id'), 'uncertainty_detections', ['id'], unique=False)
    op.create_index(op.f('ix_uncertainty_detections_impact_card_id'), 'uncertainty_detections', ['impact_card_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_uncertainty_detections_impact_card_id'), table_name='uncertainty_detections')
    op.drop_index(op.f('ix_uncertainty_detections_id'), table_name='uncertainty_detections')
    op.drop_table('uncertainty_detections')
    
    op.drop_index(op.f('ix_source_credibility_analysis_impact_card_id'), table_name='source_credibility_analysis')
    op.drop_index(op.f('ix_source_credibility_analysis_id'), table_name='source_credibility_analysis')
    op.drop_table('source_credibility_analysis')
    
    op.drop_index(op.f('ix_reasoning_steps_impact_card_id'), table_name='reasoning_steps')
    op.drop_index(op.f('ix_reasoning_steps_id'), table_name='reasoning_steps')
    op.drop_table('reasoning_steps')