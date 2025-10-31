"""add_performance_indexes

Revision ID: 3509076f29a9
Revises: 58b76129bfc7
Create Date: 2025-10-31

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3509076f29a9'
down_revision = '58b76129bfc7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for frequently queried columns"""

    # Use raw SQL with IF NOT EXISTS to make migration idempotent
    # Impact Cards - Most critical table for performance

    # Composite index for comparison queries (competitor + created_at)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_impact_cards_competitor_created
        ON impact_cards (competitor_name, created_at DESC)
    """)

    # Index for risk level filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_impact_cards_risk_level
        ON impact_cards (risk_level)
    """)

    # Index for credibility score filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_impact_cards_credibility
        ON impact_cards (credibility_score)
    """)

    # Composite index for watch_item queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_impact_cards_watch_created
        ON impact_cards (watch_item_id, created_at DESC)
    """)

    # Watch Items - Frequently queried for watchlists
    # Index on is_active for filtering active watchlist items
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_watch_items_active
        ON watch_items (is_active)
    """)

    # Index on created_at for chronological queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_watch_items_created
        ON watch_items (created_at DESC)
    """)

    # Company Research - Individual user feature
    # Index on company_name for search/filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_company_research_name
        ON company_research (company_name)
    """)

    # Index on created_at for chronological queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_company_research_created
        ON company_research (created_at DESC)
    """)


def downgrade() -> None:
    """Remove performance indexes"""

    # Use raw SQL with IF EXISTS to make migration idempotent
    op.execute("DROP INDEX IF EXISTS idx_company_research_created")
    op.execute("DROP INDEX IF EXISTS idx_company_research_name")
    op.execute("DROP INDEX IF EXISTS idx_watch_items_created")
    op.execute("DROP INDEX IF EXISTS idx_watch_items_active")
    op.execute("DROP INDEX IF EXISTS idx_impact_cards_watch_created")
    op.execute("DROP INDEX IF EXISTS idx_impact_cards_credibility")
    op.execute("DROP INDEX IF EXISTS idx_impact_cards_risk_level")
    op.execute("DROP INDEX IF EXISTS idx_impact_cards_competitor_created")
