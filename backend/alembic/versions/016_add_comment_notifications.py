"""Add comment notification and conflict detection models

Revision ID: 016_add_comment_notifications
Revises: 015_add_annotation_model
Create Date: 2025-10-31 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '016_add_comment_notifications'
down_revision = '015_add_annotation_model'
branch_labels = None
depends_on = None


def upgrade():
    # Create comment_notifications table
    op.create_table('comment_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('comment_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('context_type', sa.String(length=50), nullable=False),
        sa.Column('context_id', sa.Integer(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comment_notifications_id'), 'comment_notifications', ['id'], unique=False)

    # Create conflict_detections table
    op.create_table('conflict_detections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('context_type', sa.String(length=50), nullable=False),
        sa.Column('context_id', sa.Integer(), nullable=False),
        sa.Column('comment_1_id', sa.Integer(), nullable=False),
        sa.Column('comment_2_id', sa.Integer(), nullable=False),
        sa.Column('conflict_type', sa.String(length=50), nullable=False),
        sa.Column('confidence_score', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=False),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['comment_1_id'], ['comments.id'], ),
        sa.ForeignKeyConstraint(['comment_2_id'], ['comments.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conflict_detections_id'), 'conflict_detections', ['id'], unique=False)

    # Add indexes for better query performance
    op.create_index('ix_comment_notifications_recipient_id', 'comment_notifications', ['recipient_id'], unique=False)
    op.create_index('ix_comment_notifications_is_read', 'comment_notifications', ['is_read'], unique=False)
    op.create_index('ix_comment_notifications_notification_type', 'comment_notifications', ['notification_type'], unique=False)
    
    op.create_index('ix_conflict_detections_context', 'conflict_detections', ['context_type', 'context_id'], unique=False)
    op.create_index('ix_conflict_detections_is_resolved', 'conflict_detections', ['is_resolved'], unique=False)
    op.create_index('ix_conflict_detections_confidence_score', 'conflict_detections', ['confidence_score'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('ix_conflict_detections_confidence_score', table_name='conflict_detections')
    op.drop_index('ix_conflict_detections_is_resolved', table_name='conflict_detections')
    op.drop_index('ix_conflict_detections_context', table_name='conflict_detections')
    
    op.drop_index('ix_comment_notifications_notification_type', table_name='comment_notifications')
    op.drop_index('ix_comment_notifications_is_read', table_name='comment_notifications')
    op.drop_index('ix_comment_notifications_recipient_id', table_name='comment_notifications')
    
    op.drop_index(op.f('ix_conflict_detections_id'), table_name='conflict_detections')
    op.drop_index(op.f('ix_comment_notifications_id'), table_name='comment_notifications')
    
    # Drop tables
    op.drop_table('conflict_detections')
    op.drop_table('comment_notifications')