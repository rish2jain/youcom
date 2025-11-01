"""
Standalone unit tests for Industry Template System

This module tests the template system components without importing the full app.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select

# Import only the models and services we need for testing
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base
from app.models.industry_template import IndustryTemplate, TemplateApplication
from app.services.industry_template_service import (
    IndustryTemplateService, TemplateStatus, TemplateMetadata, TemplateApplicationInfo
)

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def sample_template_config():
    """Sample template configuration for testing."""
    return {
        "watchlist_config": {
            "auto_create_competitors": True,
            "monitoring_frequency": "daily",
            "alert_thresholds": {
                "high_risk": 80,
                "medium_risk": 50,
                "low_risk": 20
            }
        },
        "notification_rules": [
            {
                "trigger": "new_competitor",
                "channels": ["email", "slack"],
                "priority": "high"
            }
        ],
        "analysis_settings": {
            "sentiment_analysis": True,
            "trend_detection": True,
            "impact_scoring": True,
            "confidence_threshold": 0.7
        }
    }

@pytest.fixture
def sample_template_data(sample_template_config):
    """Sample template data for testing."""
    return {
        "name": "SaaS Startup Template",
        "industry_sector": "SaaS",
        "description": "Comprehensive template for SaaS startup competitive intelligence",
        "template_config": sample_template_config,
        "default_competitors": ["Slack", "Zoom", "Notion", "Figma"],
        "default_keywords": ["saas", "software", "cloud", "subscription", "enterprise"],
        "risk_categories": ["product_launch", "funding", "partnership", "acquisition"],
        "kpi_metrics": ["mrr", "churn_rate", "cac", "ltv", "growth_rate"]
    }


class TestIndustryTemplateService:
    """Test industry template service functionality."""

    @pytest.mark.asyncio
    async def test_create_template(self, db_session: AsyncSession, sample_template_data):
        """Test creating a new industry template."""
        service = IndustryTemplateService(db_session)
        
        template_id = await service.create_template(
            name=sample_template_data["name"],
            industry_sector=sample_template_data["industry_sector"],
            template_config=sample_template_data["template_config"],
            description=sample_template_data["description"],
            default_competitors=sample_template_data["default_competitors"],
            default_keywords=sample_template_data["default_keywords"],
            risk_categories=sample_template_data["risk_categories"],
            kpi_metrics=sample_template_data["kpi_metrics"],
            created_by="test_user"
        )
        
        assert template_id is not None
        
        # Verify template was created
        template = await service.get_template(template_id)
        assert template is not None
        assert template.name == sample_template_data["name"]
        assert template.industry_sector == sample_template_data["industry_sector"]
        assert template.template_config == sample_template_data["template_config"]
        assert template.default_competitors == sample_template_data["default_competitors"]
        assert template.is_active is True
        assert template.usage_count == 0
        assert template.rating == 0.0

    @pytest.mark.asyncio
    async def test_get_template_by_name(self, db_session: AsyncSession, sample_template_data):
        """Test retrieving template by name and industry."""
        service = IndustryTemplateService(db_session)
        
        # Create template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        # Retrieve by name
        template = await service.get_template_by_name(
            sample_template_data["name"], 
            sample_template_data["industry_sector"]
        )
        
        assert template is not None
        assert template.id == template_id
        assert template.name == sample_template_data["name"]

    @pytest.mark.asyncio
    async def test_list_templates_with_filtering(self, db_session: AsyncSession, sample_template_data):
        """Test listing templates with industry filtering."""
        service = IndustryTemplateService(db_session)
        
        # Create templates for different industries
        saas_template_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        fintech_data = sample_template_data.copy()
        fintech_data["name"] = "FinTech Template"
        fintech_data["industry_sector"] = "FinTech"
        fintech_template_id = await service.create_template(**fintech_data, created_by="test_user")
        
        # List all templates
        all_templates = await service.list_templates()
        assert len(all_templates) == 2
        
        # List SaaS templates only
        saas_templates = await service.list_templates(industry_sector="SaaS")
        assert len(saas_templates) == 1
        assert saas_templates[0].id == saas_template_id
        assert saas_templates[0].industry_sector == "SaaS"
        
        # List FinTech templates only
        fintech_templates = await service.list_templates(industry_sector="FinTech")
        assert len(fintech_templates) == 1
        assert fintech_templates[0].id == fintech_template_id
        assert fintech_templates[0].industry_sector == "FinTech"

    @pytest.mark.asyncio
    async def test_update_template(self, db_session: AsyncSession, sample_template_data):
        """Test updating an existing template."""
        service = IndustryTemplateService(db_session)
        
        # Create template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        # Update template
        new_description = "Updated description for SaaS template"
        new_keywords = ["updated", "keywords", "list"]
        
        success = await service.update_template(
            template_id=template_id,
            description=new_description,
            default_keywords=new_keywords,
            is_active=False
        )
        
        assert success is True
        
        # Verify updates
        updated_template = await service.get_template(template_id)
        assert updated_template.description == new_description
        assert updated_template.default_keywords == new_keywords
        assert updated_template.is_active is False
        assert updated_template.updated_at > updated_template.created_at

    @pytest.mark.asyncio
    async def test_apply_template_to_workspace(self, db_session: AsyncSession, sample_template_data):
        """Test applying a template to a workspace."""
        service = IndustryTemplateService(db_session)
        
        # Create template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        # Apply template to workspace
        workspace_id = "test_workspace_123"
        user_id = "test_user_456"
        customizations = {"custom_setting": "custom_value"}
        
        application_id = await service.apply_template(
            template_id=template_id,
            workspace_id=workspace_id,
            user_id=user_id,
            customizations=customizations
        )
        
        assert application_id is not None
        
        # Verify application was created
        result = await db_session.execute(
            select(TemplateApplication).where(TemplateApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        assert application is not None
        assert application.template_id == template_id
        assert application.workspace_id == workspace_id
        assert application.user_id == user_id
        assert application.customizations == customizations
        assert application.status == TemplateStatus.ACTIVE.value
        
        # Verify usage count was incremented
        template = await service.get_template(template_id)
        assert template.usage_count == 1

    @pytest.mark.asyncio
    async def test_rate_template_and_update_average(self, db_session: AsyncSession, sample_template_data):
        """Test rating a template and updating the average rating."""
        service = IndustryTemplateService(db_session)
        
        # Create template and apply it
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        application_id = await service.apply_template(template_id, "workspace1", "user1")
        
        # Rate the template
        rating = 4.5
        feedback = "Great template, very helpful!"
        
        success = await service.rate_template(
            template_id=template_id,
            application_id=application_id,
            rating=rating,
            feedback=feedback
        )
        
        assert success is True
        
        # Verify application rating was updated
        result = await db_session.execute(
            select(TemplateApplication).where(TemplateApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        assert application.rating == rating
        assert application.feedback == feedback
        
        # Verify template average rating was updated
        template = await service.get_template(template_id)
        assert template.rating == rating  # Only one rating, so average equals the rating

    @pytest.mark.asyncio
    async def test_search_templates(self, db_session: AsyncSession, sample_template_data):
        """Test searching templates by name and description."""
        service = IndustryTemplateService(db_session)
        
        # Create templates with different names and descriptions
        template1_data = sample_template_data.copy()
        template1_data["name"] = "SaaS Analytics Template"
        template1_data["description"] = "Template for analytics and reporting SaaS companies"
        await service.create_template(**template1_data, created_by="test_user")
        
        template2_data = sample_template_data.copy()
        template2_data["name"] = "E-commerce Template"
        template2_data["description"] = "Comprehensive template for e-commerce businesses"
        template2_data["industry_sector"] = "E-commerce"
        await service.create_template(**template2_data, created_by="test_user")
        
        # Search by name
        saas_results = await service.search_templates("SaaS")
        assert len(saas_results) == 1
        assert "SaaS" in saas_results[0].name
        
        # Search by description
        template_results = await service.search_templates("template")
        assert len(template_results) == 2  # Both have "template" in description
        
        # Search with industry filter
        ecommerce_results = await service.search_templates("template", industry_sector="E-commerce")
        assert len(ecommerce_results) == 1
        assert ecommerce_results[0].industry_sector == "E-commerce"

    @pytest.mark.asyncio
    async def test_get_template_statistics(self, db_session: AsyncSession, sample_template_data):
        """Test getting comprehensive template statistics."""
        service = IndustryTemplateService(db_session)
        
        # Create template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        # Apply template multiple times with different ratings
        app1_id = await service.apply_template(template_id, "workspace1", "user1")
        app2_id = await service.apply_template(template_id, "workspace2", "user2")
        
        # Rate some applications
        await service.rate_template(template_id, app1_id, 5.0, "Excellent!")
        await service.rate_template(template_id, app2_id, 3.0, "Good but could be better")
        
        # Get statistics
        stats = await service.get_template_statistics(template_id)
        
        assert stats["template_id"] == template_id
        assert stats["name"] == sample_template_data["name"]
        assert stats["industry_sector"] == sample_template_data["industry_sector"]
        assert stats["total_usage"] == 2
        
        # Check rating statistics
        rating_stats = stats["rating_stats"]
        assert rating_stats["count"] == 2
        assert rating_stats["average"] == 4.0  # (5.0 + 3.0) / 2
        assert rating_stats["min"] == 3.0
        assert rating_stats["max"] == 5.0

    @pytest.mark.asyncio
    async def test_delete_template_soft_delete(self, db_session: AsyncSession, sample_template_data):
        """Test soft deletion of templates."""
        service = IndustryTemplateService(db_session)
        
        # Create template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        # Verify template is active
        template = await service.get_template(template_id)
        assert template.is_active is True
        
        # Delete template
        success = await service.delete_template(template_id)
        assert success is True
        
        # Verify soft deletion
        deleted_template = await service.get_template(template_id)
        assert deleted_template.is_active is False

    @pytest.mark.asyncio
    async def test_apply_inactive_template_fails(self, db_session: AsyncSession, sample_template_data):
        """Test that applying an inactive template fails."""
        service = IndustryTemplateService(db_session)
        
        # Create and deactivate template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        await service.update_template(template_id, is_active=False)
        
        # Try to apply inactive template
        with pytest.raises(ValueError, match="not found or inactive"):
            await service.apply_template(template_id, "workspace1", "user1")

    @pytest.mark.asyncio
    async def test_rate_template_invalid_rating_range(self, db_session: AsyncSession, sample_template_data):
        """Test that invalid rating ranges are rejected."""
        service = IndustryTemplateService(db_session)
        
        # Create template and application
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        application_id = await service.apply_template(template_id, "workspace1", "user1")
        
        # Test invalid ratings
        with pytest.raises(ValueError, match="Rating must be between 0.0 and 5.0"):
            await service.rate_template(template_id, application_id, -1.0)
        
        with pytest.raises(ValueError, match="Rating must be between 0.0 and 5.0"):
            await service.rate_template(template_id, application_id, 6.0)


class TestTemplateModels:
    """Test template database models."""

    @pytest.mark.asyncio
    async def test_industry_template_model_creation(self, db_session: AsyncSession, sample_template_config):
        """Test IndustryTemplate model creation and constraints."""
        template = IndustryTemplate(
            name="Test Template",
            industry_sector="Technology",
            description="A test template",
            template_config=sample_template_config,
            default_competitors=["Competitor1", "Competitor2"],
            default_keywords=["keyword1", "keyword2"],
            risk_categories=["risk1", "risk2"],
            kpi_metrics=["metric1", "metric2"],
            created_by="test_user"
        )
        
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        
        assert template.id is not None
        assert template.name == "Test Template"
        assert template.industry_sector == "Technology"
        assert template.template_config == sample_template_config
        assert template.is_active is True
        assert template.usage_count == 0
        assert template.rating == 0.0
        assert template.created_at is not None
        assert template.updated_at is not None

    @pytest.mark.asyncio
    async def test_template_application_model_creation(self, db_session: AsyncSession, sample_template_data):
        """Test TemplateApplication model creation and relationships."""
        # Create template first
        template = IndustryTemplate(
            name=sample_template_data["name"],
            industry_sector=sample_template_data["industry_sector"],
            template_config=sample_template_data["template_config"],
            created_by="test_user"
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        
        # Create application
        application = TemplateApplication(
            template_id=template.id,
            workspace_id="test_workspace",
            user_id="test_user",
            customizations={"custom": "value"},
            status=TemplateStatus.ACTIVE.value
        )
        
        db_session.add(application)
        await db_session.commit()
        await db_session.refresh(application)
        
        assert application.id is not None
        assert application.template_id == template.id
        assert application.workspace_id == "test_workspace"
        assert application.user_id == "test_user"
        assert application.customizations == {"custom": "value"}
        assert application.status == TemplateStatus.ACTIVE.value
        assert application.applied_at is not None
        assert application.rating is None
        assert application.feedback is None

    @pytest.mark.asyncio
    async def test_template_application_relationship(self, db_session: AsyncSession, sample_template_data):
        """Test relationship between template and application models."""
        # Create template
        template = IndustryTemplate(
            name=sample_template_data["name"],
            industry_sector=sample_template_data["industry_sector"],
            template_config=sample_template_data["template_config"],
            created_by="test_user"
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        
        # Create multiple applications
        app1 = TemplateApplication(
            template_id=template.id,
            workspace_id="workspace1",
            user_id="user1",
            status=TemplateStatus.ACTIVE.value
        )
        app2 = TemplateApplication(
            template_id=template.id,
            workspace_id="workspace2",
            user_id="user2",
            status=TemplateStatus.ACTIVE.value
        )
        
        db_session.add(app1)
        db_session.add(app2)
        await db_session.commit()
        
        # Test relationship access
        result = await db_session.execute(
            select(IndustryTemplate).where(IndustryTemplate.id == template.id)
        )
        template_with_apps = result.scalar_one()
        
        # Note: In a real scenario, you'd need to configure the relationship loading
        # For this test, we'll verify the foreign key relationship works
        result = await db_session.execute(
            select(TemplateApplication).where(TemplateApplication.template_id == template.id)
        )
        applications = result.scalars().all()
        
        assert len(applications) == 2
        assert all(app.template_id == template.id for app in applications)


class TestTemplateEnums:
    """Test template-related enums and constants."""

    def test_template_status_enum(self):
        """Test TemplateStatus enum values."""
        assert TemplateStatus.ACTIVE == "active"
        assert TemplateStatus.MODIFIED == "modified"
        assert TemplateStatus.ARCHIVED == "archived"
        
        # Test enum can be used in comparisons
        status = TemplateStatus.ACTIVE
        assert status.value == "active"
        assert str(status) == "TemplateStatus.ACTIVE"

    def test_template_metadata_dataclass(self):
        """Test TemplateMetadata dataclass creation."""
        metadata = TemplateMetadata(
            id=1,
            name="Test Template",
            industry_sector="Technology",
            description="A test template",
            usage_count=5,
            rating=4.2,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test_user"
        )
        
        assert metadata.id == 1
        assert metadata.name == "Test Template"
        assert metadata.industry_sector == "Technology"
        assert metadata.usage_count == 5
        assert metadata.rating == 4.2
        assert metadata.is_active is True
        assert metadata.created_by == "test_user"

    def test_template_application_info_dataclass(self):
        """Test TemplateApplicationInfo dataclass creation."""
        app_info = TemplateApplicationInfo(
            id=1,
            template_id=10,
            workspace_id="workspace123",
            user_id="user456",
            status="active",
            applied_at=datetime.utcnow(),
            rating=4.5,
            feedback="Great template!",
            template_name="Test Template",
            industry_sector="Technology"
        )
        
        assert app_info.id == 1
        assert app_info.template_id == 10
        assert app_info.workspace_id == "workspace123"
        assert app_info.user_id == "user456"
        assert app_info.status == "active"
        assert app_info.rating == 4.5
        assert app_info.feedback == "Great template!"
        assert app_info.template_name == "Test Template"
        assert app_info.industry_sector == "Technology"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])