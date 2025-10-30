"""Add enhancement features: timeline, evidence badges, playbooks, action tracking

Revision ID: 004
Revises: 003
Create Date: 2025-10-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create insight timeline tables
    op.create_table('insight_timelines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('impact_card_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('previous_analysis_date', sa.DateTime(), nullable=True),
        sa.Column('current_risk_score', sa.Float(), nullable=False),
        sa.Column('previous_risk_score', sa.Float(), nullable=True),
        sa.Column('risk_score_delta', sa.Float(), nullable=True),
        sa.Column('new_stories_count', sa.Integer(), nullable=True),
        sa.Column('updated_stories_count', sa.Integer(), nullable=True),
        sa.Column('new_evidence_count', sa.Integer(), nullable=True),
        sa.Column('key_changes', sa.JSON(), nullable=True),
        sa.Column('fresh_insights', sa.JSON(), nullable=True),
        sa.Column('trend_shifts', sa.JSON(), nullable=True),
        sa.Column('analysis_version', sa.String(length=50), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['impact_card_id'], ['impact_cards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_insight_timelines_id'), 'insight_timelines', ['id'], unique=False)
    op.create_index(op.f('ix_insight_timelines_company_name'), 'insight_timelines', ['company_name'], unique=False)

    op.create_table('delta_highlights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timeline_id', sa.Integer(), nullable=False),
        sa.Column('highlight_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True),
        sa.Column('freshness_hours', sa.Integer(), nullable=True),
        sa.Column('badge_type', sa.String(length=20), nullable=True),
        sa.Column('badge_color', sa.String(length=20), nullable=True),
        sa.Column('source_url', sa.String(length=1000), nullable=True),
        sa.Column('source_name', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_dismissed', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['timeline_id'], ['insight_timelines.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_delta_highlights_id'), 'delta_highlights', ['id'], unique=False)

    op.create_table('trend_sparklines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('data_points', sa.JSON(), nullable=False),
        sa.Column('time_range', sa.String(length=20), nullable=False),
        sa.Column('trend_direction', sa.String(length=20), nullable=True),
        sa.Column('trend_strength', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trend_sparklines_id'), 'trend_sparklines', ['id'], unique=False)
    op.create_index(op.f('ix_trend_sparklines_company_name'), 'trend_sparklines', ['company_name'], unique=False)

    # Create evidence badge tables
    op.create_table('evidence_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('confidence_percentage', sa.Float(), nullable=False),
        sa.Column('confidence_level', sa.String(length=20), nullable=False),
        sa.Column('total_sources', sa.Integer(), nullable=True),
        sa.Column('tier_1_sources', sa.Integer(), nullable=True),
        sa.Column('tier_2_sources', sa.Integer(), nullable=True),
        sa.Column('tier_3_sources', sa.Integer(), nullable=True),
        sa.Column('tier_4_sources', sa.Integer(), nullable=True),
        sa.Column('freshness_score', sa.Float(), nullable=False),
        sa.Column('oldest_source_hours', sa.Integer(), nullable=True),
        sa.Column('newest_source_hours', sa.Integer(), nullable=True),
        sa.Column('average_source_age_hours', sa.Float(), nullable=True),
        sa.Column('cross_validation_score', sa.Float(), nullable=True),
        sa.Column('bias_detection_score', sa.Float(), nullable=True),
        sa.Column('fact_check_score', sa.Float(), nullable=True),
        sa.Column('top_sources', sa.JSON(), nullable=True),
        sa.Column('badge_color', sa.String(length=20), nullable=True),
        sa.Column('badge_icon', sa.String(length=50), nullable=True),
        sa.Column('display_text', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_badges_id'), 'evidence_badges', ['id'], unique=False)

    op.create_table('source_evidence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('badge_id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(length=200), nullable=False),
        sa.Column('source_url', sa.String(length=1000), nullable=False),
        sa.Column('source_tier', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('publish_date', sa.DateTime(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('credibility_score', sa.Float(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(), nullable=False),
        sa.Column('you_api_source', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['badge_id'], ['evidence_badges.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_source_evidence_id'), 'source_evidence', ['id'], unique=False)

    # Create personal playbook tables
    op.create_table('persona_presets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('default_data_slices', sa.JSON(), nullable=True),
        sa.Column('export_templates', sa.JSON(), nullable=True),
        sa.Column('follow_up_tasks', sa.JSON(), nullable=True),
        sa.Column('key_questions', sa.JSON(), nullable=True),
        sa.Column('priority_sources', sa.JSON(), nullable=True),
        sa.Column('analysis_depth', sa.String(length=20), nullable=True),
        sa.Column('dashboard_layout', sa.JSON(), nullable=True),
        sa.Column('notification_preferences', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_persona_presets_id'), 'persona_presets', ['id'], unique=False)

    op.create_table('user_playbooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('persona_preset_id', sa.Integer(), nullable=False),
        sa.Column('custom_name', sa.String(length=100), nullable=True),
        sa.Column('custom_config', sa.JSON(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('current_step', sa.Integer(), nullable=True),
        sa.Column('completed_tasks', sa.JSON(), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['persona_preset_id'], ['persona_presets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_playbooks_id'), 'user_playbooks', ['id'], unique=False)

    op.create_table('playbook_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_playbook_id', sa.Integer(), nullable=False),
        sa.Column('target_company', sa.String(length=255), nullable=True),
        sa.Column('execution_type', sa.String(length=50), nullable=False),
        sa.Column('generated_artifacts', sa.JSON(), nullable=True),
        sa.Column('completion_status', sa.String(length=20), nullable=True),
        sa.Column('completion_percentage', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('user_satisfaction_score', sa.Integer(), nullable=True),
        sa.Column('time_saved_minutes', sa.Integer(), nullable=True),
        sa.Column('execution_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_playbook_id'], ['user_playbooks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_playbook_executions_id'), 'playbook_executions', ['id'], unique=False)

    op.create_table('playbook_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('template_config', sa.JSON(), nullable=False),
        sa.Column('customization_options', sa.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_playbook_templates_id'), 'playbook_templates', ['id'], unique=False)

    # Create action tracking tables
    op.create_table('action_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('impact_card_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('PLANNED', 'IN_PROGRESS', 'DONE', 'CANCELLED', name='actionstatus'), nullable=True),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='actionpriority'), nullable=True),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('owner_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('estimated_hours', sa.Integer(), nullable=True),
        sa.Column('actual_hours', sa.Integer(), nullable=True),
        sa.Column('source_insight', sa.Text(), nullable=True),
        sa.Column('evidence_links', sa.JSON(), nullable=True),
        sa.Column('success_criteria', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status_updates', sa.JSON(), nullable=True),
        sa.Column('ai_generated', sa.Boolean(), nullable=True),
        sa.Column('user_modified', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['impact_card_id'], ['impact_cards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_action_items_id'), 'action_items', ['id'], unique=False)

    op.create_table('action_reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action_item_id', sa.Integer(), nullable=False),
        sa.Column('reminder_type', sa.String(length=50), nullable=False),
        sa.Column('reminder_time', sa.DateTime(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('is_sent', sa.Boolean(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('recurring', sa.Boolean(), nullable=True),
        sa.Column('recurrence_pattern', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['action_item_id'], ['action_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_action_reminders_id'), 'action_reminders', ['id'], unique=False)

    op.create_table('action_boards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('board_type', sa.String(length=50), nullable=True),
        sa.Column('columns', sa.JSON(), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('sort_order', sa.JSON(), nullable=True),
        sa.Column('is_shared', sa.Boolean(), nullable=True),
        sa.Column('shared_with', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_action_boards_id'), 'action_boards', ['id'], unique=False)

    op.create_table('action_board_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('board_id', sa.Integer(), nullable=False),
        sa.Column('action_item_id', sa.Integer(), nullable=False),
        sa.Column('column_id', sa.String(length=100), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('custom_title', sa.String(length=500), nullable=True),
        sa.Column('custom_color', sa.String(length=20), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.Column('moved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['action_item_id'], ['action_items.id'], ),
        sa.ForeignKeyConstraint(['board_id'], ['action_boards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_action_board_items_id'), 'action_board_items', ['id'], unique=False)

    op.create_table('action_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('template_actions', sa.JSON(), nullable=False),
        sa.Column('default_assignments', sa.JSON(), nullable=True),
        sa.Column('estimated_timeline', sa.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_action_templates_id'), 'action_templates', ['id'], unique=False)


def downgrade():
    # Drop action tracking tables
    op.drop_index(op.f('ix_action_templates_id'), table_name='action_templates')
    op.drop_table('action_templates')
    op.drop_index(op.f('ix_action_board_items_id'), table_name='action_board_items')
    op.drop_table('action_board_items')
    op.drop_index(op.f('ix_action_boards_id'), table_name='action_boards')
    op.drop_table('action_boards')
    op.drop_index(op.f('ix_action_reminders_id'), table_name='action_reminders')
    op.drop_table('action_reminders')
    op.drop_index(op.f('ix_action_items_id'), table_name='action_items')
    op.drop_table('action_items')

    # Drop personal playbook tables
    op.drop_index(op.f('ix_playbook_templates_id'), table_name='playbook_templates')
    op.drop_table('playbook_templates')
    op.drop_index(op.f('ix_playbook_executions_id'), table_name='playbook_executions')
    op.drop_table('playbook_executions')
    op.drop_index(op.f('ix_user_playbooks_id'), table_name='user_playbooks')
    op.drop_table('user_playbooks')
    op.drop_index(op.f('ix_persona_presets_id'), table_name='persona_presets')
    op.drop_table('persona_presets')

    # Drop evidence badge tables
    op.drop_index(op.f('ix_source_evidence_id'), table_name='source_evidence')
    op.drop_table('source_evidence')
    op.drop_index(op.f('ix_evidence_badges_id'), table_name='evidence_badges')
    op.drop_table('evidence_badges')

    # Drop insight timeline tables
    op.drop_index(op.f('ix_trend_sparklines_company_name'), table_name='trend_sparklines')
    op.drop_index(op.f('ix_trend_sparklines_id'), table_name='trend_sparklines')
    op.drop_table('trend_sparklines')
    op.drop_index(op.f('ix_delta_highlights_id'), table_name='delta_highlights')
    op.drop_table('delta_highlights')
    op.drop_index(op.f('ix_insight_timelines_company_name'), table_name='insight_timelines')
    op.drop_index(op.f('ix_insight_timelines_id'), table_name='insight_timelines')
    op.drop_table('insight_timelines')