"""add_decision_engine_tables

Revision ID: b123456789ab
Revises: a846a2559ecc
Create Date: 2025-10-31 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b123456789ab'
down_revision = 'a846a2559ecc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create action_recommendations table
    op.create_table('action_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('impact_card_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('timeline', sa.String(length=100), nullable=False),
        sa.Column('estimated_hours', sa.Integer(), nullable=True),
        sa.Column('team_members_required', sa.Integer(), nullable=True),
        sa.Column('budget_impact', sa.String(length=20), nullable=False),
        sa.Column('dependencies', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('impact_score', sa.Float(), nullable=False),
        sa.Column('effort_score', sa.Float(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('reasoning', sa.JSON(), nullable=True),
        sa.Column('evidence_links', sa.JSON(), nullable=True),
        sa.Column('okr_alignment', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('owner_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['impact_card_id'], ['impact_cards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_action_recommendations_id'), 'action_recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_action_recommendations_impact_card_id'), 'action_recommendations', ['impact_card_id'], unique=False)
    op.create_index(op.f('ix_action_recommendations_category'), 'action_recommendations', ['category'], unique=False)
    op.create_index(op.f('ix_action_recommendations_priority'), 'action_recommendations', ['priority'], unique=False)
    op.create_index(op.f('ix_action_recommendations_status'), 'action_recommendations', ['status'], unique=False)
    op.create_index(op.f('ix_action_recommendations_created_at'), 'action_recommendations', ['created_at'], unique=False)

    # Create resource_estimates table
    op.create_table('resource_estimates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action_recommendation_id', sa.Integer(), nullable=False),
        sa.Column('time_required', sa.String(length=100), nullable=False),
        sa.Column('estimated_hours_min', sa.Integer(), nullable=True),
        sa.Column('estimated_hours_max', sa.Integer(), nullable=True),
        sa.Column('team_members', sa.Integer(), nullable=False),
        sa.Column('skill_requirements', sa.JSON(), nullable=True),
        sa.Column('budget_impact', sa.String(length=20), nullable=False),
        sa.Column('budget_estimate_min', sa.Float(), nullable=True),
        sa.Column('budget_estimate_max', sa.Float(), nullable=True),
        sa.Column('dependencies', sa.JSON(), nullable=True),
        sa.Column('constraints', sa.JSON(), nullable=True),
        sa.Column('risks', sa.JSON(), nullable=True),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('estimation_method', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['action_recommendation_id'], ['action_recommendations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resource_estimates_id'), 'resource_estimates', ['id'], unique=False)
    op.create_index(op.f('ix_resource_estimates_action_recommendation_id'), 'resource_estimates', ['action_recommendation_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resource_estimates_action_recommendation_id'), table_name='resource_estimates')
    op.drop_index(op.f('ix_resource_estimates_id'), table_name='resource_estimates')
    op.drop_table('resource_estimates')
    op.drop_index(op.f('ix_action_recommendations_created_at'), table_name='action_recommendations')
    op.drop_index(op.f('ix_action_recommendations_status'), table_name='action_recommendations')
    op.drop_index(op.f('ix_action_recommendations_priority'), table_name='action_recommendations')
    op.drop_index(op.f('ix_action_recommendations_category'), table_name='action_recommendations')
    op.drop_index(op.f('ix_action_recommendations_impact_card_id'), table_name='action_recommendations')
    op.drop_index(op.f('ix_action_recommendations_id'), table_name='action_recommendations')
    op.drop_table('action_recommendations')