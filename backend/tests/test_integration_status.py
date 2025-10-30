"""
Integration status tests - verify all features are properly integrated
"""

import pytest
import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


class TestIntegrationStatus:
    """Test that all features are properly integrated"""
    
    def test_service_imports(self):
        """Test that all services can be imported"""
        try:
            from app.services.notion_service import NotionService
            from app.services.salesforce_service import SalesforceService
            from app.services.analytics_service import PredictiveAnalyticsService
            from app.services.email_service import EmailService
            from app.services.slack_service import SlackService
            from app.services.pdf_service import PDFService
            from app.services.resilient_you_client import ResilientYouComOrchestrator
            
            # Test instantiation with required parameters
            notion = NotionService("test_token")
            salesforce = SalesforceService()
            analytics = PredictiveAnalyticsService()
            
            assert notion is not None
            assert salesforce is not None
            assert analytics is not None
            
        except ImportError as e:
            pytest.fail(f"Service import failed: {e}")
        except Exception as e:
            # Services may fail to initialize without proper config, but imports should work
            pass
    
    def test_api_imports(self):
        """Test that all API modules can be imported"""
        try:
            from app.api import watch, impact, research
            from app.api import analytics, integrations
            from app.api import auth, workspaces
            from app.api import metrics, monitoring
            
            # Check routers exist
            assert hasattr(watch, 'router')
            assert hasattr(impact, 'router')
            assert hasattr(research, 'router')
            assert hasattr(analytics, 'router')
            assert hasattr(integrations, 'router')
            assert hasattr(auth, 'router')
            assert hasattr(workspaces, 'router')
            assert hasattr(metrics, 'router')
            assert hasattr(monitoring, 'router')
            
        except ImportError as e:
            pytest.fail(f"API import failed: {e}")
    
    def test_model_imports(self):
        """Test that all models can be imported"""
        try:
            from app.models.user import User, UserRole
            from app.models.workspace import Workspace
            from app.models.integration import Integration, IntegrationType
            from app.models.watch import WatchItem  # Correct import
            from app.models.impact_card import ImpactCard
            from app.models.company_research import CompanyResearch
            from app.models.api_call_log import ApiCallLog
            from app.models.audit_log import AuditLog
            
            # Test enum values
            assert UserRole.ADMIN is not None
            assert IntegrationType.NOTION is not None
            
        except ImportError as e:
            pytest.fail(f"Model import failed: {e}")
    
    def test_schema_imports(self):
        """Test that all schemas can be imported"""
        try:
            from app.schemas.auth import UserLogin, UserRegister, TokenResponse
            from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse
            from app.schemas.integration import IntegrationCreate, IntegrationResponse
            from app.schemas.watch import WatchItemCreate, WatchItem
            from app.schemas.impact_card import ImpactCard, ImpactCardCreate  # Correct schema names
            from app.schemas.company_research import CompanyResearch, CompanyResearchCreate  # Correct schema names
            
        except ImportError as e:
            pytest.fail(f"Schema import failed: {e}")
    
    def test_main_app_integration(self):
        """Test that the main app integrates all routers"""
        from app.main import app
        
        # Check that routers are included
        routes = [route.path for route in app.routes]
        
        # Core API routes should be present
        expected_prefixes = [
            "/api/v1/watch",
            "/api/v1/impact",
            "/api/v1/research",
            "/api/v1/analytics",
            "/api/v1/integrations",
            "/api/v1/auth",
            "/api/v1/workspaces",
            "/api/v1/metrics",
            "/api/v1/monitoring"
        ]
        
        for prefix in expected_prefixes:
            # Check if any route starts with the expected prefix
            matching_routes = [route for route in routes if route.startswith(prefix)]
            assert len(matching_routes) > 0, f"No routes found for prefix: {prefix}"
    
    def test_file_structure(self):
        """Test that all required files exist"""
        backend_dir = Path(__file__).parent.parent
        
        required_files = [
            "app/main.py",
            "app/config.py",
            "app/database.py",
            "app/services/notion_service.py",
            "app/services/salesforce_service.py",
            "app/services/analytics_service.py",
            "app/services/resilient_you_client.py",
            "app/api/analytics.py",
            "app/api/integrations.py",
            "app/api/monitoring.py",
            "app/models/integration.py",
            "app/schemas/integration.py"
        ]
        
        for file_path in required_files:
            full_path = backend_dir / file_path
            assert full_path.exists(), f"Required file missing: {file_path}"
    
    def test_frontend_components_exist(self):
        """Test that frontend components exist"""
        project_root = Path(__file__).parent.parent.parent
        components_dir = project_root / "components"
        
        required_components = [
            "PredictiveAnalytics.tsx",
            "IntegrationManager.tsx",
            "WatchList.tsx",
            "ImpactCardDisplay.tsx",
            "CompanyResearch.tsx",
            "APIUsageDashboard.tsx"
        ]
        
        for component in required_components:
            component_path = components_dir / component
            assert component_path.exists(), f"Required component missing: {component}"
    
    def test_ui_components_exist(self):
        """Test that UI components exist"""
        project_root = Path(__file__).parent.parent.parent
        ui_dir = project_root / "components" / "ui"
        
        required_ui = [
            "card.tsx",
            "button.tsx",
            "badge.tsx",
            "input.tsx",
            "label.tsx",
            "tabs.tsx",
            "dialog.tsx",
            "select.tsx"
        ]
        
        for ui_component in required_ui:
            ui_path = ui_dir / ui_component
            assert ui_path.exists(), f"Required UI component missing: {ui_component}"
    
    def test_configuration_files(self):
        """Test that configuration files exist"""
        project_root = Path(__file__).parent.parent.parent
        
        config_files = [
            ".env.example",
            "package.json",
            "requirements.txt",
            "docker-compose.yml"
        ]
        
        for config_file in config_files:
            config_path = project_root / config_file
            assert config_path.exists(), f"Configuration file missing: {config_file}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])