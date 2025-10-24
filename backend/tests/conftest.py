"""
Test configuration and fixtures for Enterprise CIA
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.database import get_db, Base
from app.config import settings

# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database session override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_you_api_key():
    """Mock You.com API key for testing."""
    return "test_you_api_key_12345"

@pytest.fixture
def sample_competitor_data():
    """Sample competitor data for testing."""
    return {
        "competitor_name": "Test Competitor",
        "keywords": ["AI", "machine learning", "API"],
        "description": "A test competitor for unit testing"
    }

@pytest.fixture
def sample_impact_card_data():
    """Sample impact card data for testing."""
    return {
        "competitor_name": "Test Competitor",
        "risk_score": 75,
        "risk_level": "high",
        "confidence_score": 85,
        "credibility_score": 0.8,
        "requires_review": False,
        "impact_areas": [
            {
                "area": "product",
                "impact_score": 80,
                "description": "Significant product impact"
            }
        ],
        "key_insights": [
            "Test insight 1",
            "Test insight 2"
        ],
        "recommended_actions": [
            {
                "action": "Monitor closely",
                "priority": "high",
                "timeline": "immediate",
                "owner": "Product",
                "okr_goal": "Enhance product differentiation",
                "impact_score": 80,
                "effort_score": 40,
                "score": 60,
                "evidence": [],
                "index": 0,
            }
        ],
        "next_steps_plan": [],
        "total_sources": 25,
        "source_breakdown": {
            "news_articles": 10,
            "search_results": 8,
            "research_citations": 7
        },
        "source_quality": {"score": 0.8, "tiers": {"tier1": 2, "tier2": 1, "tier3": 0}, "total": 3, "top_sources": []},
        "api_usage": {
            "news_calls": 2,
            "search_calls": 2,
            "chat_calls": 1,
            "ari_calls": 1,
            "total_calls": 6
        },
        "processing_time": "4.0s",
        "raw_data": {},
        "explainability": {"reasoning": "", "impact_areas": [], "key_insights": [], "source_summary": {}},
    }

@pytest.fixture
def mock_you_api_responses():
    """Mock responses from You.com APIs."""
    return {
        "news": {
            "query": "Test Competitor announcement",
            "articles": [
                {
                    "title": "Test Competitor Announces New Product",
                    "snippet": "Test Competitor has announced a new AI product...",
                    "url": "https://example.com/news1",
                    "published_date": "2024-01-01T00:00:00Z"
                }
            ],
            "total_count": 1,
            "api_type": "news"
        },
        "search": {
            "query": "Test Competitor business model",
            "results": [
                {
                    "title": "Test Competitor - Company Profile",
                    "snippet": "Test Competitor is a leading AI company...",
                    "url": "https://example.com/profile"
                }
            ],
            "total_count": 1,
            "api_type": "search"
        },
        "chat": {
            "response": {
                "risk_score": 75,
                "risk_level": "high",
                "impact_areas": [
                    {
                        "area": "product",
                        "impact_score": 80,
                        "description": "Significant product impact"
                    }
                ],
                "key_insights": ["Test insight"],
                "recommended_actions": [
                    {
                        "action": "Monitor closely",
                        "priority": "high",
                        "timeline": "immediate"
                    }
                ],
                "confidence_score": 85,
                "reasoning": "Analysis based on available data"
            },
            "api_type": "chat"
        },
        "ari": {
            "query": "Test Competitor analysis",
            "report": "Comprehensive analysis of Test Competitor shows...",
            "citations": [
                {
                    "title": "Industry Report",
                    "url": "https://example.com/report"
                }
            ],
            "source_count": 15,
            "api_type": "ari"
        }
    }
