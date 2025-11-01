"""Add annotation model for collaboration features

Revision ID: 015_add_annotation_model
Revises: 014_add_explainability_models
Create Date: 2025-10-31 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '015_add_annotation_model'
down_revision = '014_add_explainability_models'
branch_labels = None
depends_on = None


def upgrade():
    # Create annotations table
    op.create_table('annotations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('impact_card_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('annotation_type', sa.String(length=50), nullable=False),
        sa.Column('position', sa.JSON(), nullable=True),
        sa.Column('target_element', sa.String(length=255), nullable=True),
        sa.Column('target_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_resolved', sa.Integer(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['impact_card_id'], ['impact_cards.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_annotations_id'), 'annotations', ['id'], unique=False)

    # Add indexes for better query performance
    op.create_index('ix_annotations_impact_card_id', 'annotations', ['impact_card_id'], unique=False)
    op.create_index('ix_annotations_user_id', 'annotations', ['user_id'], unique=False)
    op.create_index('ix_annotations_annotation_type', 'annotations', ['annotation_type'], unique=False)
    op.create_index('ix_annotations_is_resolved', 'annotations', ['is_resolved'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('ix_annotations_is_resolved', table_name='annotations')
    op.drop_index('ix_annotations_annotation_type', table_name='annotations')
    op.drop_index('ix_annotations_user_id', table_name='annotations')
    op.drop_index('ix_annotations_impact_card_id', table_name='annotations')
    op.drop_index(op.f('ix_annotations_id'), table_name='annotations')
    
    # Drop table
    op.drop_table('annotations')