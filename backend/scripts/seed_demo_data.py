#!/usr/bin/env python3
"""
Demo Data Seeding Script
Populates database with current, realistic competitive intelligence data
Updated October 2025 with latest AI landscape including GPT-5, Claude 4, $300B+ valuations
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

# Current competitive landscape data (Updated October 2025)
DEMO_COMPETITORS = [
    {
        "name": "OpenAI",
        "keywords": ["GPT-5", "GPT-5 mini", "GPT-5 nano", "o3", "o4-mini", "ChatGPT", "Sora", "Agent Mode"],
        "description": "AI industry leader with GPT-5 release and massive enterprise adoption driving $13B ARR",
        "risk_score": 98,
        "risk_level": "critical",
        "impact_summary": "OpenAI released GPT-5 in August 2025, achieving state-of-the-art performance across coding, math, and multimodal tasks. Company raised $40B at $300B valuation (March 2025), reaching $13B ARR with 5M paid business users. GPT-5 unifies reasoning capabilities and sets new benchmarks: 94.6% on AIME 2025, 74.9% on SWE-bench Verified. Dominates enterprise market with adoption by Cursor, Vercel, Factory, JetBrains. 6x reduction in hallucinations vs o3. Represents existential competitive threat.",
        "total_sources": 487
    },
    {
        "name": "Anthropic",
        "keywords": ["Claude 4", "Claude Sonnet 4.5", "Claude Code", "Computer Use", "Model Context Protocol"],
        "description": "AI safety leader with $183B valuation and fastest-growing enterprise AI platform",
        "risk_score": 95,
        "risk_level": "critical",
        "impact_summary": "Anthropic raised $13B at $183B valuation (September 2025), triple its March valuation. Run-rate revenue surged from $1B (January) to $5B+ (August) - one of fastest tech growth trajectories ever. Claude Code generating $500M+ ARR with 10x growth in 3 months. Serves 300K+ business customers. Claude Sonnet 4.5 (September 2025) leads on coding benchmarks (72.5% SWE-bench). Computer Use enables AI to control computers directly. Major threat with enterprise focus and safety-first approach.",
        "total_sources": 412
    },
    {
        "name": "Cursor",
        "keywords": ["AI coding", "vibe coding", "Composer", "IDE", "developer tools", "Anysphere"],
        "description": "Fastest-growing AI startup ever with $9.9B valuation and revolutionary AI-native coding experience",
        "risk_score": 89,
        "risk_level": "critical",
        "impact_summary": "Cursor reached $9.9B valuation in June 2025 (up from $2.6B in December 2024), dubbed 'fastest growing startup ever' by Bloomberg. Surpassed $500M ARR with revenue doubling every 2 months. Generates ~1 billion lines of code daily. Three funding rounds in <1 year totaling $1B+. Disrupting GitHub Copilot with superior AI-native experience. Used by Stripe, Spotify, OpenAI engineers. Rejected OpenAI acquisition attempt. Represents paradigm shift in software development.",
        "total_sources": 193
    },
    {
        "name": "Google DeepMind",
        "keywords": ["Gemini 2.5 Pro", "Gemini 3.0", "Deep Think", "Deep Research", "Veo 3", "NotebookLM"],
        "description": "Tech giant's unified AI with massive distribution, Gemini 2.5 Pro and upcoming Gemini 3.0",
        "risk_score": 92,
        "risk_level": "critical",
        "impact_summary": "Gemini 2.5 Pro with Deep Think achieves gold medal at IMO, ~90% on MMLU. Deep Research transforms hours of research into minutes. NotebookLM viral success with podcast generation. Veo 3 introduces native audio/video generation with sound effects and dialogue. Imagen 4 delivers superior image quality. Gemini 3.0 expected Q4 2025 with enhanced reasoning and multimodal capabilities. AI Overviews integrated into Search affects 1B+ users. Computer Use model enables browser/mobile automation.",
        "total_sources": 456
    },
    {
        "name": "Perplexity AI",
        "keywords": ["AI search", "answer engine", "Comet browser", "Pro Search", "Shopping Hub", "Perplexity Assistant"],
        "description": "AI-powered search challenger reaching $20B valuation with 780M+ monthly queries disrupting Google",
        "risk_score": 87,
        "risk_level": "critical",
        "impact_summary": "Perplexity raised $200M at $20B valuation (September 2025), up from $18B two months prior. Processing 780M+ queries monthly with 30M+ active users. Approaching $200M ARR. Launched Comet browser with AI-powered browsing. Made $34.5B bid for Chrome browser. Perplexity Assistant enables cross-app tasks. Shopping Hub backed by Amazon and Nvidia. Major threat to traditional search with cited, conversational answers. Growing 3x faster than Google Search at comparable stage.",
        "total_sources": 298
    },
    {
        "name": "Databricks",
        "keywords": ["Data Intelligence Platform", "IPO", "Mosaic ML", "Apache Spark", "data analytics", "AI platform"],
        "description": "Data and AI giant valued at $100B+ preparing for blockbuster IPO with $3.7B ARR",
        "risk_score": 84,
        "risk_level": "high",
        "impact_summary": "Databricks raised $10B at $62B valuation (January 2025), then secured $100B+ valuation (August 2025) becoming 4th private company to exceed $100B (after SpaceX, ByteDance, OpenAI). Reaching $3.7B ARR with 50% YoY growth. Free cash flow positive. 500+ customers at $1M+ ARR. Databricks SQL hit $600M ARR (up 150% YoY). Major enterprise adoption. Planning IPO late 2025 or early 2026. Strategic investments from Meta, Nvidia.",
        "total_sources": 387
    },
    {
        "name": "Meta AI",
        "keywords": ["Llama 3.3", "Llama 3.2", "open source", "multimodal", "Ray-Ban Meta", "AI Studio"],
        "description": "Open-source AI leader with 3B+ user distribution across Meta platforms and competitive models",
        "risk_score": 85,
        "risk_level": "high",
        "impact_summary": "Llama 3.2 adds vision capabilities and edge deployment. Meta's open-source strategy commoditizes foundation models, threatening proprietary competitors. Ray-Ban Meta glasses achieved 700K+ units sold with AI integration. 3B+ users across Meta platforms provide unmatched distribution. AI Studio enables custom AI creation. WhatsApp AI integration reaches billions. Meta-Google $10B+ cloud deal over 6 years. Open-source approach accelerates ecosystem while Meta uses models internally for products.",
        "total_sources": 334
    },
    {
        "name": "Mistral AI",
        "keywords": ["Mistral Large 3", "Pixtral 12B", "Le Chat", "European AI", "open source", "Codestral"],
        "description": "European AI champion valued at $6B with competitive models and enterprise focus",
        "risk_score": 73,
        "risk_level": "high",
        "impact_summary": "Mistral raised $1.5B in Q3 2025 at undisclosed valuation (previously $6B June 2024). Mistral Large 3 competes with GPT-4 at lower cost. Strong European enterprise adoption in regulated industries. Pixtral adds vision capabilities. Europe's most valuable AI startup. Strategic positioning for sovereignty-focused markets. Codestral targets developers. Focus on cost-effective, performant models.",
        "total_sources": 198
    },
]

DEMO_RESEARCH = [
    {
        "company_name": "Databricks",
        "total_sources": 387,
        "api_usage": {"search_calls": 4, "ari_calls": 1, "total_calls": 5}
    },
    {
        "company_name": "Scale AI",
        "total_sources": 243,
        "api_usage": {"search_calls": 3, "ari_calls": 1, "total_calls": 4}
    },
    {
        "company_name": "Canva",
        "total_sources": 219,
        "api_usage": {"search_calls": 3, "ari_calls": 1, "total_calls": 4}
    },
    {
        "company_name": "Notion",
        "total_sources": 204,
        "api_usage": {"search_calls": 3, "ari_calls": 1, "total_calls": 4}
    },
    {
        "company_name": "Figma",
        "total_sources": 187,
        "api_usage": {"search_calls": 2, "ari_calls": 1, "total_calls": 3}
    },
    {
        "company_name": "Stripe",
        "total_sources": 267,
        "api_usage": {"search_calls": 3, "ari_calls": 1, "total_calls": 4}
    },
    {
        "company_name": "Airtable",
        "total_sources": 168,
        "api_usage": {"search_calls": 2, "ari_calls": 1, "total_calls": 3}
    },
    {
        "company_name": "Linear",
        "total_sources": 134,
        "api_usage": {"search_calls": 2, "ari_calls": 1, "total_calls": 3}
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
        print(f"  • Total Risk Score Range: 73-98/100")
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
