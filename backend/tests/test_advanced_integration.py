"""Integration tests for advanced features"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.main import app
from app.models.integration import Integration, IntegrationType
from app.models.workspace import Workspace
from app.models.user import User, UserRole
from app.services.auth_service import get_current_user

# Mock user for testing
def get_mock_user():
    """Return a mock user for testing"""
    user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        role=UserRole.ADMIN,
        is_active=True
    )
    return user

# Override the dependency for testing
app.dependency_overrides[get_current_user] = get_mock_user


@pytest.mark.asyncio
async def test_notion_integration_workflow():
    """Test complete Notion integration workflow"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test Notion connection
        with patch('app.services.notion_service.NotionService.test_connection') as mock_test:
            mock_test.return_value = {
                "status": "success",
                "user": "Test User",
                "workspace": "Test Workspace"
            }
            
            response = await client.post(
                "/api/v1/integrations/notion/test",
                json={"api_token": "test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["user"] == "Test User"


@pytest.mark.asyncio
async def test_salesforce_integration_workflow():
    """Test complete Salesforce integration workflow"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test Salesforce connection
        with patch('app.services.salesforce_service.SalesforceService.test_connection') as mock_test:
            mock_test.return_value = {
                "status": "success",
                "message": "Successfully connected to Salesforce"
            }
            
            response = await client.post(
                "/api/v1/integrations/salesforce/test",
                json={
                    "instance_url": "https://test.salesforce.com",
                    "access_token": "test_token"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"


@pytest.mark.asyncio
async def test_predictive_analytics_workflow():
    """Test predictive analytics endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test market landscape analysis
        with patch('app.services.analytics_service.PredictiveAnalyticsService.market_landscape_analysis') as mock_analysis:
            mock_analysis.return_value = {
                "status": "success",
                "market_overview": {
                    "total_competitive_activities": 25,
                    "average_market_risk": 65.5,
                    "market_temperature": "warm",
                    "unique_competitors": 8
                },
                "top_competitors": [
                    {"name": "OpenAI", "activity_count": 12, "average_risk_score": 78.5}
                ],
                "insights": ["Market shows moderate competitive activity"]
            }
            
            response = await client.get("/api/v1/analytics/market-landscape")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["market_overview"]["market_temperature"] == "warm"


@pytest.mark.asyncio
async def test_competitor_trend_analysis():
    """Test competitor trend analysis"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        with patch('app.services.analytics_service.PredictiveAnalyticsService.analyze_competitor_trends') as mock_trends:
            mock_trends.return_value = {
                "status": "success",
                "competitor": "OpenAI",
                "risk_trend": "increasing",
                "activity_frequency_per_week": 2.5,
                "average_risk_score": 75.2,
                "prediction": "High competitive pressure expected"
            }
            
            response = await client.get("/api/v1/analytics/competitor-trends/OpenAI")
            
            assert response.status_code == 200
            data = response.json()
            assert data["competitor"] == "OpenAI"
            assert data["risk_trend"] == "increasing"


@pytest.mark.asyncio
async def test_executive_summary_generation():
    """Test executive summary generation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        with patch('app.services.analytics_service.PredictiveAnalyticsService.market_landscape_analysis') as mock_market:
            with patch('app.services.analytics_service.PredictiveAnalyticsService.api_usage_predictions') as mock_usage:
                mock_market.return_value = {
                    "status": "success",
                    "market_overview": {
                        "total_competitive_activities": 30,
                        "market_temperature": "hot",
                        "unique_competitors": 10,
                        "average_market_risk": 82.5
                    },
                    "top_competitors": [
                        {"name": "OpenAI", "activity_count": 15, "average_risk_score": 85.0}
                    ]
                }
                
                mock_usage.return_value = {
                    "status": "success",
                    "current_usage": {"total_api_calls": 150},
                    "predictions": {"estimated_monthly_cost": 15.50}
                }
                
                response = await client.get("/api/v1/analytics/executive-summary")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "executive_summary" in data
                assert data["executive_summary"]["key_metrics"]["market_temperature"] == "hot"


@pytest.mark.asyncio
async def test_integration_management_crud():
    """Test integration management CRUD operations"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test listing integrations (empty initially)
        response = await client.get("/api/v1/integrations/?workspace_id=1")
        assert response.status_code == 200
        integrations = response.json()
        assert isinstance(integrations, list)


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete end-to-end workflow with all features"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Test You.com API health
        response = await client.get("/api/v1/health/you-apis")
        assert response.status_code == 200
        
        # 2. Test resilience status
        response = await client.get("/api/v1/health/resilience")
        assert response.status_code == 200
        
        # 3. Test analytics endpoints
        with patch('app.services.analytics_service.PredictiveAnalyticsService.market_landscape_analysis') as mock_analysis:
            mock_analysis.return_value = {"status": "success", "market_overview": {}}
            response = await client.get("/api/v1/analytics/market-landscape")
            assert response.status_code == 200
        
        # 4. Test integration endpoints
        response = await client.get("/api/v1/integrations/?workspace_id=1")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_orchestration():
    """Test that all APIs work together in orchestration"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test the demo endpoint that showcases API integration
        response = await client.get("/api/v1/demo/you-apis")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "workflow" in data
        assert len(data["workflow"]) == 5  # All 5 workflow steps


@pytest.mark.asyncio
async def test_feature_integration_status():
    """Test that all implemented features are accessible"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test all major endpoints are accessible
        endpoints_to_test = [
            "/health",
            "/api/v1/health/you-apis",
            "/api/v1/health/resilience",
            "/api/v1/demo/you-apis",
            "/api/v1/integrations/?workspace_id=1",
        ]
        
        for endpoint in endpoints_to_test:
            response = await client.get(endpoint)
            assert response.status_code in [200, 401]  # 401 for auth-required endpoints is OK


if __name__ == "__main__":
    pytest.main([__file__, "-v"])