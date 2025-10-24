#!/usr/bin/env python3
"""
Demo Data Seeding Script
Populates database with impressive sample data for hackathon demo
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random

from app.models.user import User, UserRole
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.models.watch import WatchItem
from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch
from app.models.api_call_log import ApiCallLog
from app.services.auth_service import AuthService
from app.database import Base
from app.config import settings

# Impressive demo data
DEMO_COMPETITORS = [
    {
        "name": "OpenAI",
        "keywords": ["GPT-5", "ChatGPT", "API", "DALL-E", "GPT-4 Turbo"],
        "description": "Leading AI research company - track product launches and API updates",
        "risk_score": 85,
        "risk_level": "critical",
        "impact_summary": "OpenAI launched GPT-4 Turbo with 128K context window, significantly expanding capabilities. Major competitive threat to existing LLM providers.",
        "total_sources": 156
    },
    {
        "name": "Anthropic",
        "keywords": ["Claude", "Claude 2", "AI safety", "Constitutional AI"],
        "description": "AI safety-focused competitor with strong enterprise traction",
        "risk_score": 72,
        "risk_level": "high",
        "impact_summary": "Anthropic raised $450M Series C, now valued at $4.5B. Claude 2 showing strong enterprise adoption with 100K context window.",
        "total_sources": 124
    },
    {
        "name": "Google AI",
        "keywords": ["Gemini", "Bard", "PaLM 2", "AI", "DeepMind"],
        "description": "Tech giant's AI division - massive R&D budget and distribution",
        "risk_score": 78,
        "risk_level": "high",
        "impact_summary": "Google launched Gemini Pro with multimodal capabilities. Integration with Google Workspace threatens productivity AI market.",
        "total_sources": 203
    },
    {
        "name": "Perplexity AI",
        "keywords": ["AI search", "answer engine", "citations"],
        "description": "AI-powered search engine with strong product-market fit",
        "risk_score": 65,
        "risk_level": "medium",
        "impact_summary": "Perplexity raised $73.6M Series B at $520M valuation. 10M monthly users, 500M+ queries served.",
        "total_sources": 89
    },
    {
        "name": "Mistral AI",
        "keywords": ["Mistral", "open source", "LLM", "European AI"],
        "description": "European open-source LLM competitor with strong technical talent",
        "risk_score": 58,
        "risk_level": "medium",
        "impact_summary": "Mistral AI released Mixtral 8x7B, matching GPT-3.5 performance. $415M Series A makes it Europe's most valuable AI startup.",
        "total_sources": 67
    },
    {
        "name": "Cohere",
        "keywords": ["enterprise AI", "embedding", "RAG"],
        "description": "Enterprise-focused LLM platform with strong B2B traction",
        "risk_score": 54,
        "risk_level": "medium",
        "impact_summary": "Cohere expanded Command model capabilities, focusing on enterprise RAG use cases. $270M Series C funding.",
        "total_sources": 45
    },
]

DEMO_RESEARCH = [
    {
        "company_name": "Runway ML",
        "total_sources": 112,
        "api_usage": {"search_calls": 1, "ari_calls": 1, "total_calls": 2}
    },
    {
        "company_name": "Stability AI",
        "total_sources": 98,
        "api_usage": {"search_calls": 1, "ari_calls": 1, "total_calls": 2}
    },
    {
        "company_name": "Hugging Face",
        "total_sources": 145,
        "api_usage": {"search_calls": 1, "ari_calls": 1, "total_calls": 2}
    },
]


async def seed_demo_data():
    """Seed database with impressive demo data"""

    # Create async engine
    engine = create_async_engine(settings.database_url, echo=True)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("\n🌱 Seeding demo data...")

        # 1. Create demo user
        print("\n👤 Creating demo user...")
        demo_user = User(
            email="demo@enterprisecia.com",
            username="demo",
            full_name="Demo User",
            hashed_password=AuthService.get_password_hash("demo2024"),
            role=UserRole.ANALYST,
            is_active=True,
            is_verified=True
        )
        session.add(demo_user)
        await session.flush()
        print(f"✅ Demo user created: {demo_user.email}")

        # 2. Create demo workspace
        print("\n🏢 Creating demo workspace...")
        demo_workspace = Workspace(
            name="Demo Workspace",
            slug="demo-workspace",
            description="Hackathon demonstration workspace with sample data",
            max_members=10,
            allow_guest_access=True
        )
        session.add(demo_workspace)
        await session.flush()

        # Add user as owner
        workspace_member = WorkspaceMember(
            workspace_id=demo_workspace.id,
            user_id=demo_user.id,
            role=WorkspaceRole.OWNER
        )
        session.add(workspace_member)
        print(f"✅ Workspace created: {demo_workspace.name}")

        # 3. Create watch items and impact cards
        print("\n👀 Creating competitors and impact cards...")
        for i, competitor in enumerate(DEMO_COMPETITORS):
            # Create watch item
            watch_item = WatchItem(
                competitor_name=competitor["name"],
                keywords=competitor["keywords"],
                description=competitor["description"],
                is_active=True,
                last_checked=datetime.utcnow() - timedelta(hours=random.randint(1, 24))
            )
            session.add(watch_item)
            await session.flush()

            # Create impact card
            impact_card = ImpactCard(
                watch_item_id=watch_item.id,
                competitor_name=competitor["name"],
                risk_score=competitor["risk_score"],
                risk_level=competitor["risk_level"],
                impact_summary={
                    "summary": competitor["impact_summary"],
                    "key_findings": [
                        f"Finding {j+1} for {competitor['name']}"
                        for j in range(3)
                    ]
                },
                news_articles={
                    "articles": [
                        {
                            "title": f"Article {j+1} about {competitor['name']}",
                            "url": f"https://example.com/article-{j}",
                            "published_date": (datetime.utcnow() - timedelta(days=j)).isoformat()
                        }
                        for j in range(min(5, competitor["total_sources"] // 30))
                    ]
                },
                search_context={
                    "results": [
                        {
                            "snippet": f"Context snippet {j+1}",
                            "url": f"https://example.com/source-{j}"
                        }
                        for j in range(10)
                    ]
                },
                research_report={
                    "report": f"Comprehensive research report for {competitor['name']}...",
                    "sections": ["Overview", "Analysis", "Recommendations"]
                },
                total_sources=competitor["total_sources"],
                confidence_score=random.uniform(0.85, 0.95),
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            session.add(impact_card)
            print(f"  ✅ {competitor['name']}: Risk {competitor['risk_score']}/100 ({competitor['risk_level'].upper()})")

        # 4. Create company research records
        print("\n🔬 Creating company research records...")
        for research in DEMO_RESEARCH:
            research_record = CompanyResearch(
                company_name=research["company_name"],
                search_results={
                    "results": [
                        {"title": f"Result {i}", "snippet": f"Info about {research['company_name']}"}
                        for i in range(10)
                    ]
                },
                research_report={
                    "report": f"Deep research analysis of {research['company_name']}..."
                },
                total_sources=research["total_sources"],
                api_usage=research["api_usage"]
            )
            session.add(research_record)
            print(f"  ✅ {research['company_name']}: {research['total_sources']} sources")

        # 5. Create API call logs for impressive metrics
        print("\n📊 Creating API usage metrics...")
        api_calls = []
        base_time = datetime.utcnow() - timedelta(days=7)

        for day in range(7):
            for hour in range(24):
                timestamp = base_time + timedelta(days=day, hours=hour)

                # News API calls
                for _ in range(random.randint(2, 8)):
                    api_calls.append(ApiCallLog(
                        service="news",
                        endpoint="/livenews",
                        status_code=200,
                        response_time_ms=random.randint(300, 800),
                        created_at=timestamp + timedelta(minutes=random.randint(0, 59))
                    ))

                # Search API calls
                for _ in range(random.randint(3, 10)):
                    api_calls.append(ApiCallLog(
                        service="search",
                        endpoint="/v1/search",
                        status_code=200,
                        response_time_ms=random.randint(400, 1000),
                        created_at=timestamp + timedelta(minutes=random.randint(0, 59))
                    ))

                # Chat API calls
                for _ in range(random.randint(2, 6)):
                    api_calls.append(ApiCallLog(
                        service="chat",
                        endpoint="/agents/runs",
                        status_code=200,
                        response_time_ms=random.randint(800, 2000),
                        created_at=timestamp + timedelta(minutes=random.randint(0, 59))
                    ))

                # ARI API calls
                for _ in range(random.randint(1, 4)):
                    api_calls.append(ApiCallLog(
                        service="ari",
                        endpoint="/agents/runs",
                        status_code=200,
                        response_time_ms=random.randint(2000, 5000),
                        created_at=timestamp + timedelta(minutes=random.randint(0, 59))
                    ))

        session.add_all(api_calls)
        print(f"  ✅ Created {len(api_calls)} API call logs")

        # Commit all changes
        await session.commit()

        print("\n" + "=" * 60)
        print("✨ Demo data seeding complete!")
        print("=" * 60)
        print("\n📊 Summary:")
        print(f"  • Demo User: demo@enterprisecia.com / demo2024")
        print(f"  • Competitors: {len(DEMO_COMPETITORS)}")
        print(f"  • Impact Cards: {len(DEMO_COMPETITORS)}")
        print(f"  • Company Research: {len(DEMO_RESEARCH)}")
        print(f"  • API Calls: {len(api_calls)}")
        print(f"  • Total Risk Score Range: 54-85/100")
        print(f"  • Total Sources Aggregated: {sum(c['total_sources'] for c in DEMO_COMPETITORS)}")
        print("\n🎬 Ready for demo!")
        print("\n🚀 Next steps:")
        print("  1. Start backend: uvicorn app.main:socket_app --reload")
        print("  2. Start frontend: npm run dev")
        print("  3. Login with demo credentials")
        print("  4. Run: python scripts/record_demo.py")

    await engine.dispose()


if __name__ == "__main__":
    print("🌱 Enterprise CIA - Demo Data Seeder")
    print("=" * 60)
    print("\n⚠️  This will:")
    print("  1. Create demo user (demo@enterprisecia.com)")
    print("  2. Add 6 competitors with impact cards")
    print("  3. Add 3 company research records")
    print("  4. Generate 1,000+ API call logs")
    print("\n⚠️  WARNING: This will modify your database!")
    print("\nContinue? (yes/no): ", end="")

    response = input().strip().lower()
    if response == "yes":
        asyncio.run(seed_demo_data())
    else:
        print("❌ Cancelled")
