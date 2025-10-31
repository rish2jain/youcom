#!/usr/bin/env python3
"""
Setup script for enhancement features demo data.
Creates sample data for timeline, evidence badges, playbooks, and actions.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import get_db
from app.services.insight_timeline_service import InsightTimelineService
from app.services.evidence_badge_service import EvidenceBadgeService
from app.services.personal_playbook_service import PersonalPlaybookService
from app.services.action_tracker_service import ActionTrackerService
from app.models.impact_card import ImpactCard
from app.schemas.insight_timeline import InsightTimelineCreate, DeltaHighlightCreate
from app.schemas.action_tracker import ActionItemCreate
from sqlalchemy.orm import Session

async def create_sample_timeline_data(db: Session, impact_card_id: int, company_name: str):
    """Create sample timeline and delta data."""
    print(f"Creating timeline data for {company_name}...")
    
    service = InsightTimelineService(db)
    
    # Create a timeline entry with sample data
    timeline_data = InsightTimelineCreate(
        impact_card_id=impact_card_id,
        company_name=company_name,
        current_risk_score=75.0,
        previous_risk_score=68.0,
        previous_analysis_date=datetime.utcnow() - timedelta(days=3),
        new_stories_count=5,
        updated_stories_count=2,
        new_evidence_count=7,
        key_changes=[
            "Risk score increased by 7 points",
            "5 new competitive announcements detected",
            "2 existing stories updated with new information"
        ],
        fresh_insights=[
            "New product launch announced with advanced AI capabilities",
            "Strategic partnership with major enterprise client",
            "Significant funding round completed at higher valuation"
        ],
        trend_shifts=[
            "Competitive activity accelerating in Q4",
            "Shift from consumer to enterprise focus detected"
        ],
        confidence_score=0.85
    )
    
    # Create highlights
    highlights = [
        DeltaHighlightCreate(
            highlight_type="new_story",
            title="5 new competitive stories detected",
            description="Fresh intelligence gathered from multiple sources",
            importance_score=0.8,
            freshness_hours=2,
            badge_type="new",
            badge_color="green"
        ),
        DeltaHighlightCreate(
            highlight_type="risk_change",
            title="Risk score increased by 7 points",
            description="Significant increase in competitive threat level",
            importance_score=0.9,
            freshness_hours=0,
            badge_type="alert",
            badge_color="red"
        ),
        DeltaHighlightCreate(
            highlight_type="trend_shift",
            title="Market trend shift detected",
            description="Competitor pivoting from consumer to enterprise focus",
            importance_score=0.7,
            freshness_hours=1,
            badge_type="trending",
            badge_color="blue"
        )
    ]
    
    timeline = await service.create_timeline_entry(timeline_data, highlights)
    print(f"✅ Created timeline entry with {len(highlights)} highlights")
    return timeline

def create_sample_evidence_badges(db: Session, impact_card_id: int):
    """Create sample evidence badges."""
    print("Creating evidence badges...")
    
    service = EvidenceBadgeService(db)
    
    # Sample sources with different tiers
    sources = [
        {
            "name": "Wall Street Journal",
            "url": "https://wsj.com/sample-article",
            "title": "Tech Giant Announces Major AI Breakthrough",
            "excerpt": "In a significant development for the AI industry...",
            "publish_date": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "relevance_score": 0.95,
            "credibility_score": 0.98,
            "you_api_source": "news"
        },
        {
            "name": "TechCrunch",
            "url": "https://techcrunch.com/sample-article",
            "title": "Startup Raises $100M Series B",
            "excerpt": "The company plans to use the funding to expand...",
            "publish_date": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
            "relevance_score": 0.88,
            "credibility_score": 0.85,
            "you_api_source": "search"
        },
        {
            "name": "Hacker News",
            "url": "https://news.ycombinator.com/sample",
            "title": "Discussion: New AI Model Performance",
            "excerpt": "Community discussion about recent AI developments...",
            "publish_date": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
            "relevance_score": 0.72,
            "credibility_score": 0.65,
            "you_api_source": "search"
        },
        {
            "name": "Company Blog",
            "url": "https://company.com/blog/announcement",
            "title": "Official Product Announcement",
            "excerpt": "We're excited to announce our latest product...",
            "publish_date": (datetime.utcnow() - timedelta(hours=24)).isoformat(),
            "relevance_score": 0.90,
            "credibility_score": 0.60,
            "you_api_source": "ari"
        }
    ]
    
    badge = service.create_evidence_badge(
        entity_type="impact_card",
        entity_id=impact_card_id,
        sources=sources
    )
    
    print(f"✅ Created evidence badge with {len(sources)} sources")
    return badge

async def create_sample_actions(db: Session, impact_card_id: int):
    """Create sample action items."""
    print("Creating sample actions...")
    
    service = ActionTrackerService(db)
    
    # Initialize templates
    await service.initialize_builtin_templates()
    
    # Create individual actions
    actions_data = [
        ActionItemCreate(
            impact_card_id=impact_card_id,
            title="Analyze competitive feature gaps",
            description="Compare new competitor features with our current roadmap",
            category="research",
            priority="high",
            assigned_to="product-team@company.com",
            due_date=datetime.utcnow() + timedelta(days=7),
            estimated_hours=8,
            source_insight="New product launch detected with advanced capabilities",
            success_criteria=["Gap analysis completed", "Roadmap impact assessed"]
        ),
        ActionItemCreate(
            impact_card_id=impact_card_id,
            title="Brief leadership on competitive threat",
            description="Present findings and strategic recommendations to executive team",
            category="communication",
            priority="urgent",
            assigned_to="strategy-lead@company.com",
            due_date=datetime.utcnow() + timedelta(days=3),
            estimated_hours=4,
            source_insight="Significant risk score increase detected",
            success_criteria=["Executive briefing delivered", "Strategic direction confirmed"]
        ),
        ActionItemCreate(
            impact_card_id=impact_card_id,
            title="Update competitive positioning",
            description="Revise messaging and positioning based on new competitive landscape",
            category="strategy",
            priority="medium",
            assigned_to="marketing-team@company.com",
            due_date=datetime.utcnow() + timedelta(days=14),
            estimated_hours=12,
            source_insight="Competitor shift to enterprise focus",
            success_criteria=["Positioning updated", "Sales team briefed"]
        ),
        ActionItemCreate(
            impact_card_id=impact_card_id,
            title="Monitor competitor response",
            description="Set up enhanced monitoring for competitor's next moves",
            category="monitoring",
            priority="low",
            assigned_to="analyst@company.com",
            due_date=datetime.utcnow() + timedelta(days=21),
            estimated_hours=2,
            source_insight="Trend acceleration detected",
            success_criteria=["Monitoring alerts configured", "Review schedule set"]
        )
    ]
    
    created_actions = []
    for action_data in actions_data:
        action = await service.create_action_item(action_data)
        created_actions.append(action)
    
    print(f"✅ Created {len(created_actions)} action items")
    return created_actions

async def setup_demo_data():
    """Set up all demo data for enhancement features."""
    print("🚀 Setting up enhancement features demo data...")
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Check if we have an impact card to work with
        impact_card = db.query(ImpactCard).first()
        
        if not impact_card:
            print("❌ No impact cards found. Please create an impact card first.")
            return
        
        print(f"📊 Using impact card: {impact_card.competitor_name} (ID: {impact_card.id})")
        
        # Create timeline data
        timeline = await create_sample_timeline_data(
            db, impact_card.id, impact_card.competitor_name
        )
        
        # Create evidence badges
        badge = create_sample_evidence_badges(db, impact_card.id)
        
        # Create action items
        actions = await create_sample_actions(db, impact_card.id)
        
        # Initialize playbook service and built-in personas
        playbook_service = PersonalPlaybookService(db)
        personas = await playbook_service.initialize_builtin_personas()
        print(f"✅ Initialized {len(personas)} persona presets")
        
        # Create a sample user playbook
        if personas:
            demo_playbook = await playbook_service.create_user_playbook(
                user_id=1,
                persona_preset_id=personas[0].id,
                custom_name="Demo Competitive Analysis Playbook"
            )
            print(f"✅ Created demo playbook: {demo_playbook.custom_name}")
        
        print("\n🎉 Enhancement features demo data setup complete!")
        print("\n📋 Summary:")
        print(f"   • Timeline entries: 1 with {len(timeline.delta_highlights)} highlights")
        print(f"   • Evidence badges: 1 with {badge.total_sources} sources")
        print(f"   • Action items: {len(actions)}")
        print(f"   • Persona presets: {len(personas)}")
        print(f"   • User playbooks: 1")
        
        print("\n🌐 Access the enhancements at:")
        print("   • Frontend: http://localhost:3456 (Enhancements tab)")
        print("   • API Demo: http://localhost:8765/api/v1/enhancements/demo/status")
        
    except Exception as e:
        print(f"❌ Error setting up demo data: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(setup_demo_data())