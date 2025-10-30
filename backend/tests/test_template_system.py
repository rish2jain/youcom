"""
Unit tests for Industry Template System

This module tests the template system components including:
- Template application and customization logic
- Industry data accuracy and updates
- Template versioning and migration procedures
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select

# Import models and services
from app.database import Base
from app.models.industry_template import IndustryTemplate, TemplateApplication
from app.services.industry_template_service import (
    IndustryTemplateService, TemplateStatus, TemplateMetadata, TemplateApplicationInfo
)
from app.services.template_engine import TemplateEngine, TemplateApplicationResult
from app.services.industry_data_provider import IndustryDataProvider
from app.schemas.industry_template import (
    IndustryTemplateCreate, IndustryTemplateUpdate, TemplateApplicationCreate,
    TemplateRating
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
            },
            {
                "trigger": "funding_announcement",
                "channels": ["email"],
                "priority": "medium"
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
        
        # Verify it doesn't appear in active template lists
        active_templates = await service.list_templates(is_active=True)
        assert len(active_templates) == 0
        
        # But appears in inactive template lists
        inactive_templates = await service.list_templates(is_active=False)
        assert len(inactive_templates) == 1

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
    async def test_apply_template_twice_updates_existing(self, db_session: AsyncSession, sample_template_data):
        """Test applying the same template twice updates the existing application."""
        service = IndustryTemplateService(db_session)
        
        # Create template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        workspace_id = "test_workspace_123"
        user_id = "test_user_456"
        
        # Apply template first time
        first_customizations = {"setting1": "value1"}
        first_application_id = await service.apply_template(
            template_id=template_id,
            workspace_id=workspace_id,
            user_id=user_id,
            customizations=first_customizations
        )
        
        # Apply template second time with different customizations
        second_customizations = {"setting1": "updated_value1", "setting2": "value2"}
        second_application_id = await service.apply_template(
            template_id=template_id,
            workspace_id=workspace_id,
            user_id=user_id,
            customizations=second_customizations
        )
        
        # Should be the same application ID (updated, not new)
        assert first_application_id == second_application_id
        
        # Verify customizations were updated
        result = await db_session.execute(
            select(TemplateApplication).where(TemplateApplication.id == first_application_id)
        )
        application = result.scalar_one_or_none()
        assert application.customizations == second_customizations
        
        # Usage count should be incremented twice
        template = await service.get_template(template_id)
        assert template.usage_count == 2

    @pytest.mark.asyncio
    async def test_get_workspace_templates(self, db_session: AsyncSession, sample_template_data):
        """Test retrieving all templates applied to a workspace."""
        service = IndustryTemplateService(db_session)
        
        # Create multiple templates
        template1_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        template2_data = sample_template_data.copy()
        template2_data["name"] = "Second Template"
        template2_data["industry_sector"] = "FinTech"
        template2_id = await service.create_template(**template2_data, created_by="test_user")
        
        workspace_id = "test_workspace_123"
        user_id = "test_user_456"
        
        # Apply both templates to the same workspace
        await service.apply_template(template1_id, workspace_id, user_id)
        await service.apply_template(template2_id, workspace_id, user_id)
        
        # Get workspace templates
        workspace_templates = await service.get_workspace_templates(workspace_id)
        
        assert len(workspace_templates) == 2
        
        # Verify template information
        template_ids = {app.template_id for app in workspace_templates}
        assert template1_id in template_ids
        assert template2_id in template_ids
        
        # Verify application info
        for app in workspace_templates:
            assert app.workspace_id == workspace_id
            assert app.user_id == user_id
            assert app.status == TemplateStatus.ACTIVE.value
            assert app.template_name in ["SaaS Startup Template", "Second Template"]

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
    async def test_rate_template_multiple_ratings_average(self, db_session: AsyncSession, sample_template_data):
        """Test that multiple ratings correctly calculate average."""
        service = IndustryTemplateService(db_session)
        
        # Create template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        # Apply template to multiple workspaces
        app1_id = await service.apply_template(template_id, "workspace1", "user1")
        app2_id = await service.apply_template(template_id, "workspace2", "user2")
        app3_id = await service.apply_template(template_id, "workspace3", "user3")
        
        # Rate the template from different applications
        await service.rate_template(template_id, app1_id, 5.0)
        await service.rate_template(template_id, app2_id, 3.0)
        await service.rate_template(template_id, app3_id, 4.0)
        
        # Verify average rating
        template = await service.get_template(template_id)
        expected_average = (5.0 + 3.0 + 4.0) / 3
        assert abs(template.rating - expected_average) < 0.01

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
        
        template3_data = sample_template_data.copy()
        template3_data["name"] = "FinTech Startup Template"
        template3_data["description"] = "Template for financial technology startups"
        template3_data["industry_sector"] = "FinTech"
        await service.create_template(**template3_data, created_by="test_user")
        
        # Search by name
        saas_results = await service.search_templates("SaaS")
        assert len(saas_results) == 1
        assert "SaaS" in saas_results[0].name
        
        # Search by description
        template_results = await service.search_templates("template")
        assert len(template_results) == 3  # All have "template" in description
        
        # Search with industry filter
        fintech_results = await service.search_templates("template", industry_sector="FinTech")
        assert len(fintech_results) == 1
        assert fintech_results[0].industry_sector == "FinTech"
        
        # Search for non-existent term
        no_results = await service.search_templates("nonexistent")
        assert len(no_results) == 0

    @pytest.mark.asyncio
    async def test_get_popular_templates(self, db_session: AsyncSession, sample_template_data):
        """Test getting popular templates by usage and rating."""
        service = IndustryTemplateService(db_session)
        
        # Create templates with different usage and ratings
        template1_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        template2_data = sample_template_data.copy()
        template2_data["name"] = "Popular Template"
        template2_id = await service.create_template(**template2_data, created_by="test_user")
        
        template3_data = sample_template_data.copy()
        template3_data["name"] = "Unpopular Template"
        template3_id = await service.create_template(**template3_data, created_by="test_user")
        
        # Apply templates different numbers of times and rate them
        # Template 2: High usage, high rating
        for i in range(5):
            app_id = await service.apply_template(template2_id, f"workspace{i}", f"user{i}")
            await service.rate_template(template2_id, app_id, 4.5)
        
        # Template 1: Medium usage, medium rating
        for i in range(3):
            app_id = await service.apply_template(template1_id, f"workspace{i+10}", f"user{i+10}")
            await service.rate_template(template1_id, app_id, 3.5)
        
        # Template 3: Low usage, low rating
        app_id = await service.apply_template(template3_id, "workspace20", "user20")
        await service.rate_template(template3_id, app_id, 2.0)
        
        # Get popular templates
        popular_templates = await service.get_popular_templates(limit=3)
        
        assert len(popular_templates) == 3
        
        # Should be ordered by rating first, then usage
        assert popular_templates[0].name == "Popular Template"  # Highest rating
        assert popular_templates[1].name == "SaaS Startup Template"  # Medium rating
        assert popular_templates[2].name == "Unpopular Template"  # Lowest rating

    @pytest.mark.asyncio
    async def test_get_template_statistics(self, db_session: AsyncSession, sample_template_data):
        """Test getting comprehensive template statistics."""
        service = IndustryTemplateService(db_session)
        
        # Create template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        # Apply template multiple times with different statuses and ratings
        app1_id = await service.apply_template(template_id, "workspace1", "user1")
        app2_id = await service.apply_template(template_id, "workspace2", "user2")
        app3_id = await service.apply_template(template_id, "workspace3", "user3")
        
        # Rate some applications
        await service.rate_template(template_id, app1_id, 5.0, "Excellent!")
        await service.rate_template(template_id, app2_id, 3.0, "Good but could be better")
        # Leave app3 unrated
        
        # Update one application status
        await service.update_template_application(app2_id, status=TemplateStatus.MODIFIED)
        
        # Get statistics
        stats = await service.get_template_statistics(template_id)
        
        assert stats["template_id"] == template_id
        assert stats["name"] == sample_template_data["name"]
        assert stats["industry_sector"] == sample_template_data["industry_sector"]
        assert stats["total_usage"] == 3
        
        # Check status counts
        assert stats["status_counts"]["active"] == 2  # app1 and app3
        assert stats["status_counts"]["modified"] == 1  # app2
        
        # Check rating statistics
        rating_stats = stats["rating_stats"]
        assert rating_stats["count"] == 2  # Only 2 rated
        assert rating_stats["average"] == 4.0  # (5.0 + 3.0) / 2
        assert rating_stats["min"] == 3.0
        assert rating_stats["max"] == 5.0

    @pytest.mark.asyncio
    async def test_cleanup_old_applications(self, db_session: AsyncSession, sample_template_data):
        """Test cleanup of old archived template applications."""
        service = IndustryTemplateService(db_session)
        
        # Create template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        # Create applications with different ages and statuses
        old_date = datetime.utcnow() - timedelta(days=400)  # Older than 365 days
        recent_date = datetime.utcnow() - timedelta(days=30)  # Recent
        
        # Old archived application (should be cleaned up)
        old_app = TemplateApplication(
            template_id=template_id,
            workspace_id="old_workspace",
            user_id="old_user",
            status=TemplateStatus.ARCHIVED.value,
            applied_at=old_date
        )
        db_session.add(old_app)
        
        # Recent archived application (should not be cleaned up)
        recent_app = TemplateApplication(
            template_id=template_id,
            workspace_id="recent_workspace",
            user_id="recent_user",
            status=TemplateStatus.ARCHIVED.value,
            applied_at=recent_date
        )
        db_session.add(recent_app)
        
        # Old active application (should not be cleaned up)
        old_active_app = TemplateApplication(
            template_id=template_id,
            workspace_id="old_active_workspace",
            user_id="old_active_user",
            status=TemplateStatus.ACTIVE.value,
            applied_at=old_date
        )
        db_session.add(old_active_app)
        
        await db_session.commit()
        
        # Verify all applications exist
        result = await db_session.execute(select(TemplateApplication))
        all_apps = result.scalars().all()
        assert len(all_apps) == 3
        
        # Cleanup old applications
        cleanup_count = await service.cleanup_old_applications(days=365)
        
        assert cleanup_count == 1  # Only the old archived application
        
        # Verify only old archived application was deleted
        result = await db_session.execute(select(TemplateApplication))
        remaining_apps = result.scalars().all()
        assert len(remaining_apps) == 2
        
        # Verify the correct applications remain
        workspace_ids = {app.workspace_id for app in remaining_apps}
        assert "recent_workspace" in workspace_ids
        assert "old_active_workspace" in workspace_ids
        assert "old_workspace" not in workspace_ids


class TestTemplateValidationAndEdgeCases:
    """Test template validation and edge cases."""

    @pytest.mark.asyncio
    async def test_retrieve_template_by_name_and_industry(self, db_session: AsyncSession, sample_template_data):
        """Test retrieving a template by name and industry."""
        service = IndustryTemplateService(db_session)
        
        # Create template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        assert template_id is not None
        
        # Retrieve template by name and industry
        retrieved_template = await service.get_template_by_name(
            sample_template_data["name"], 
            sample_template_data["industry_sector"]
        )
        assert retrieved_template is not None
        assert retrieved_template.id == template_id

    @pytest.mark.asyncio
    async def test_create_same_name_different_industry(self, db_session: AsyncSession, sample_template_data):
        """Test that same template name in different industries is allowed."""
        service = IndustryTemplateService(db_session)
        
        # Create first template
        template1_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        # Create template with same name but different industry
        different_industry_data = sample_template_data.copy()
        different_industry_data["industry_sector"] = "FinTech"
        template2_id = await service.create_template(**different_industry_data, created_by="test_user")
        
        assert template1_id != template2_id
        
        # Verify both templates exist
        template1 = await service.get_template(template1_id)
        template2 = await service.get_template(template2_id)
        
        assert template1.name == template2.name
        assert template1.industry_sector != template2.industry_sector

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

    @pytest.mark.asyncio
    async def test_update_nonexistent_template(self, db_session: AsyncSession):
        """Test updating a non-existent template returns False."""
        service = IndustryTemplateService(db_session)
        
        success = await service.update_template(
            template_id=99999,  # Non-existent ID
            name="Updated Name"
        )
        
        assert success is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent_template(self, db_session: AsyncSession):
        """Test deleting a non-existent template returns False."""
        service = IndustryTemplateService(db_session)
        
        success = await service.delete_template(99999)  # Non-existent ID
        assert success is False

    @pytest.mark.asyncio
    async def test_get_industries_list(self, db_session: AsyncSession, sample_template_data):
        """Test getting list of available industries."""
        service = IndustryTemplateService(db_session)
        
        # Initially no industries
        industries = await service.get_industries()
        assert len(industries) == 0
        
        # Create templates in different industries
        await service.create_template(**sample_template_data, created_by="test_user")
        
        fintech_data = sample_template_data.copy()
        fintech_data["industry_sector"] = "FinTech"
        fintech_data["name"] = "FinTech Template"
        await service.create_template(**fintech_data, created_by="test_user")
        
        ecommerce_data = sample_template_data.copy()
        ecommerce_data["industry_sector"] = "E-commerce"
        ecommerce_data["name"] = "E-commerce Template"
        await service.create_template(**ecommerce_data, created_by="test_user")
        
        # Get industries
        industries = await service.get_industries()
        assert len(industries) == 3
        assert "SaaS" in industries
        assert "FinTech" in industries
        assert "E-commerce" in industries
        assert industries == sorted(industries)  # Should be sorted

    @pytest.mark.asyncio
    async def test_template_config_json_serialization(self, db_session: AsyncSession, sample_template_config):
        """Test that complex template configurations are properly serialized."""
        service = IndustryTemplateService(db_session)
        
        # Create template with complex nested configuration
        complex_config = {
            "nested_object": {
                "level1": {
                    "level2": {
                        "array": [1, 2, 3, {"nested_in_array": True}],
                        "boolean": True,
                        "null_value": None,
                        "number": 42.5
                    }
                }
            },
            "array_of_objects": [
                {"id": 1, "name": "Object 1"},
                {"id": 2, "name": "Object 2"}
            ]
        }
        
        template_id = await service.create_template(
            name="Complex Config Template",
            industry_sector="Test",
            template_config=complex_config,
            created_by="test_user"
        )
        
        # Retrieve and verify configuration
        template = await service.get_template(template_id)
        assert template.template_config == complex_config
        
        # Verify nested access works
        assert template.template_config["nested_object"]["level1"]["level2"]["boolean"] is True
        assert template.template_config["array_of_objects"][0]["name"] == "Object 1"

    @pytest.mark.asyncio
    async def test_template_metadata_dataclass(self, db_session: AsyncSession, sample_template_data):
        """Test TemplateMetadata dataclass creation and usage."""
        service = IndustryTemplateService(db_session)
        
        # Create template
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        
        # Get template metadata
        templates = await service.list_templates()
        assert len(templates) == 1
        
        metadata = templates[0]
        assert isinstance(metadata, TemplateMetadata)
        assert metadata.id == template_id
        assert metadata.name == sample_template_data["name"]
        assert metadata.industry_sector == sample_template_data["industry_sector"]
        assert metadata.description == sample_template_data["description"]
        assert metadata.usage_count == 0
        assert metadata.rating == 0.0
        assert metadata.is_active is True
        assert metadata.created_by == "test_user"
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)


class TestTemplateApplicationInfo:
    """Test TemplateApplicationInfo functionality."""

    @pytest.mark.asyncio
    async def test_template_application_info_dataclass(self, db_session: AsyncSession, sample_template_data):
        """Test TemplateApplicationInfo dataclass creation."""
        service = IndustryTemplateService(db_session)
        
        # Create template and apply it
        template_id = await service.create_template(**sample_template_data, created_by="test_user")
        application_id = await service.apply_template(template_id, "workspace1", "user1")
        
        # Rate the application
        await service.rate_template(template_id, application_id, 4.0, "Good template")
        
        # Get workspace templates
        workspace_templates = await service.get_workspace_templates("workspace1")
        assert len(workspace_templates) == 1
        
        app_info = workspace_templates[0]
        assert isinstance(app_info, TemplateApplicationInfo)
        assert app_info.id == application_id
        assert app_info.template_id == template_id
        assert app_info.workspace_id == "workspace1"
        assert app_info.user_id == "user1"
        assert app_info.status == TemplateStatus.ACTIVE.value
        assert app_info.rating == 4.0
        assert app_info.feedback == "Good template"
        assert app_info.template_name == sample_template_data["name"]
        assert app_info.industry_sector == sample_template_data["industry_sector"]
        assert isinstance(app_info.applied_at, datetime)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])