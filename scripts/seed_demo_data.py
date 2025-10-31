#!/usr/bin/env python3
"""Seed the database with current competitive intelligence data using You.com APIs.
Updated October 2025 with GPT-5, Claude 4, $300B+ valuations, and latest market developments."""

import asyncio
import os
import sys
from typing import List
from sqlalchemy import select, delete

# Ensure backend package is importable
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.config import settings
from app.database import AsyncSessionLocal, Base, engine
from app.models.watch import WatchItem
from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch
from app.services.you_client import YouComOrchestrator, YouComAPIError
from sqlalchemy import delete, select


COMPETITORS = [
    {
        "name": "OpenAI",
        "keywords": ["GPT-5", "GPT-5 mini", "o3", "o4-mini", "ChatGPT", "Sora", "Agent Mode"],
        "description": "AI industry leader with GPT-5 release and $300B valuation driving $13B ARR."
    },
    {
        "name": "Anthropic",
        "keywords": ["Claude 4", "Claude Sonnet 4.5", "Claude Code", "Computer Use", "Model Context Protocol"],
        "description": "AI safety leader with $183B valuation and fastest-growing enterprise AI platform."
    },
    {
        "name": "Cursor",
        "keywords": ["AI coding", "vibe coding", "Composer", "IDE", "developer tools", "Anysphere"],
        "description": "Fastest-growing AI startup ever with $9.9B valuation and revolutionary coding experience."
    },
    {
        "name": "Google DeepMind",
        "keywords": ["Gemini 2.5 Pro", "Gemini 3.0", "Deep Think", "Deep Research", "Veo 3", "NotebookLM"],
        "description": "Tech giant's unified AI with massive distribution and upcoming Gemini 3.0."
    },
    {
        "name": "Perplexity AI",
        "keywords": ["AI search", "Comet browser", "Pro Search", "Shopping Hub", "Perplexity Assistant"],
        "description": "AI-powered search challenger reaching $20B valuation with 780M+ monthly queries."
    },
    {
        "name": "Databricks",
        "keywords": ["Data Intelligence Platform", "IPO", "Mosaic ML", "Apache Spark", "AI platform"],
        "description": "Data and AI giant valued at $100B+ preparing for blockbuster IPO with $3.7B ARR."
    },
]

RESEARCH_TARGETS = [
    "Databricks",
    "Scale AI", 
    "Canva",
    "Notion",
    "Figma",
    "Stripe",
    "Airtable",
    "Linear",
]


async def ensure_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def upsert_watch_items(session) -> List[WatchItem]:
    watch_items: List[WatchItem] = []

    for competitor in COMPETITORS:
        existing = await session.execute(
            select(WatchItem).where(WatchItem.competitor_name == competitor["name"])
        )
        watch_item = existing.scalars().first()
        if watch_item is None:
            watch_item = WatchItem(
                competitor_name=competitor["name"],
                keywords=competitor["keywords"],
                description=competitor["description"],
            )
            session.add(watch_item)
            await session.flush()
        watch_items.append(watch_item)

    await session.commit()
    return watch_items


async def generate_impact_cards(session, watch_items: List[WatchItem]) -> None:
    for watch in watch_items:
        async with YouComOrchestrator() as orchestrator:
            try:
                impact_data = await orchestrator.generate_impact_card(
                    competitor=watch.competitor_name,
                    keywords=watch.keywords or [],
                    progress_room=None,
                    db_session=session,
                )
            except YouComAPIError as exc:
                print(f"⚠️  Skipping {watch.competitor_name}: {exc}")
                await session.rollback()
                continue

        await session.execute(
            delete(ImpactCard).where(ImpactCard.watch_item_id == watch.id)
        )

        impact_card = ImpactCard(
            watch_item_id=watch.id,
            competitor_name=watch.competitor_name,
            risk_score=impact_data["risk_score"],
            risk_level=impact_data["risk_level"],
            confidence_score=impact_data.get("confidence_score", 0),
            impact_areas=impact_data.get("impact_areas", []),
            key_insights=impact_data.get("key_insights", []),
            recommended_actions=impact_data.get("recommended_actions", []),
            total_sources=impact_data.get("total_sources", 0),
            source_breakdown=impact_data.get("source_breakdown", {}),
            api_usage=impact_data.get("api_usage", {}),
            processing_time=impact_data.get("processing_time"),
            raw_data=impact_data.get("raw_data", {}),
        )

        session.add(impact_card)
        await session.commit()
        print(f"✅ Impact card stored for {watch.competitor_name}")


async def generate_company_research(session) -> None:
    for company in RESEARCH_TARGETS:
        async with YouComOrchestrator() as orchestrator:
            try:
                research = await orchestrator.quick_company_research(company)
            except YouComAPIError as exc:
                print(f"⚠️  Skipping research for {company}: {exc}")
                await session.rollback()
                continue

        existing = await session.execute(
            select(CompanyResearch).where(CompanyResearch.company_name == company)
        )
        entry = existing.scalars().first()
        if entry is None:
            entry = CompanyResearch(
                company_name=company,
                search_results=research.get("search_results", {}),
                research_report=research.get("research_report", {}),
                total_sources=research.get("total_sources", 0),
                api_usage=research.get("api_usage", {}),
            )
            session.add(entry)
        else:
            entry.search_results = research.get("search_results", {})
            entry.research_report = research.get("research_report", {})
            entry.total_sources = research.get("total_sources", 0)
            entry.api_usage = research.get("api_usage", {})

        await session.commit()
        print(f"✅ Company research stored for {company}")


async def main() -> None:
    if not settings.you_api_key or settings.you_api_key == "your_you_api_key_here":
        raise RuntimeError("YOU_API_KEY must be set in the environment before seeding.")

    await ensure_schema()

    async with AsyncSessionLocal() as session:
        watch_items = await upsert_watch_items(session)
        await generate_impact_cards(session, watch_items)
        await generate_company_research(session)


if __name__ == "__main__":
    asyncio.run(main())
