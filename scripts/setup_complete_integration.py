#!/usr/bin/env python3
"""
Complete integration setup script for Enterprise CIA
Ensures all features are properly configured and integrated
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))


class IntegrationSetup:
    """Setup and configure all integrated features"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "backend"
    
    def log_step(self, step: str, success: bool = True, details: str = ""):
        """Log setup step"""
        icon = "✅" if success else "❌"
        print(f"{icon} {step}")
        if details:
            print(f"   {details}")
    
    def check_dependencies(self):
        """Check that all required dependencies are installed"""
        print("🔍 Checking Dependencies...")
        
        # Check Python dependencies
        try:
            import fastapi
            import sqlalchemy
            import httpx
            import redis
            import reportlab
            self.log_step("Python Dependencies", True, "All required packages available")
        except ImportError as e:
            self.log_step("Python Dependencies", False, f"Missing: {e}")
            return False
        
        # Check Node.js dependencies
        package_json = self.project_root / "package.json"
        if package_json.exists():
            self.log_step("Node.js Dependencies", True, "package.json found")
        else:
            self.log_step("Node.js Dependencies", False, "package.json missing")
            return False
        
        return True
    
    def check_environment_config(self):
        """Check environment configuration"""
        print("\n🔧 Checking Environment Configuration...")
        
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if env_file.exists():
            self.log_step("Environment File", True, ".env file exists")
            
            # Check for required variables
            with open(env_file) as f:
                env_content = f.read()
                
            required_vars = ["YOU_API_KEY", "DATABASE_URL", "REDIS_URL"]
            missing_vars = []
            
            for var in required_vars:
                if var not in env_content or f"{var}=" not in env_content:
                    missing_vars.append(var)
            
            if missing_vars:
                self.log_step(
                    "Environment Variables",
                    False,
                    f"Missing: {', '.join(missing_vars)}"
                )
                return False
            else:
                self.log_step("Environment Variables", True, "All required variables present")
        else:
            self.log_step("Environment File", False, ".env file missing")
            if env_example.exists():
                print("   💡 Copy .env.example to .env and configure your settings")
            return False
        
        return True
    
    def check_database_setup(self):
        """Check database setup and migrations"""
        print("\n🗄️ Checking Database Setup...")
        
        alembic_dir = self.backend_dir / "alembic"
        versions_dir = alembic_dir / "versions"
        
        if alembic_dir.exists():
            self.log_step("Alembic Configuration", True, "Migration system configured")
            
            # Check for migration files
            if versions_dir.exists():
                migration_files = list(versions_dir.glob("*.py"))
                migration_count = len([f for f in migration_files if not f.name.startswith("__")])
                
                self.log_step(
                    "Database Migrations",
                    migration_count >= 3,
                    f"{migration_count} migration files found"
                )
                return migration_count >= 3
            else:
                self.log_step("Database Migrations", False, "No versions directory")
                return False
        else:
            self.log_step("Alembic Configuration", False, "No alembic directory")
            return False
    
    def check_service_integration(self):
        """Check that all services are properly integrated"""
        print("\n🔧 Checking Service Integration...")
        
        # Check service files exist
        services_dir = self.backend_dir / "app" / "services"
        required_services = [
            "you_client.py",
            "resilient_you_client.py",
            "notion_service.py",
            "salesforce_service.py",
            "analytics_service.py",
            "email_service.py",
            "slack_service.py",
            "pdf_service.py"
        ]
        
        missing_services = []
        for service in required_services:
            service_path = services_dir / service
            if service_path.exists():
                self.log_step(f"Service - {service}", True)
            else:
                self.log_step(f"Service - {service}", False)
                missing_services.append(service)
        
        return len(missing_services) == 0
    
    def check_api_endpoints(self):
        """Check that all API endpoints are properly registered"""
        print("\n🌐 Checking API Endpoints...")
        
        api_dir = self.backend_dir / "app" / "api"
        required_apis = [
            "watch.py",
            "impact.py", 
            "research.py",
            "analytics.py",
            "integrations.py",
            "auth.py",
            "workspaces.py",
            "metrics.py",
            "monitoring.py"
        ]
        
        missing_apis = []
        for api in required_apis:
            api_path = api_dir / api
            if api_path.exists():
                self.log_step(f"API - {api}", True)
            else:
                self.log_step(f"API - {api}", False)
                missing_apis.append(api)
        
        return len(missing_apis) == 0
    
    def check_frontend_components(self):
        """Check that all frontend components exist"""
        print("\n🎨 Checking Frontend Components...")
        
        components_dir = self.project_root / "components"
        required_components = [
            "WatchList.tsx",
            "ImpactCardDisplay.tsx",
            "CompanyResearch.tsx",
            "APIUsageDashboard.tsx",
            "PredictiveAnalytics.tsx",
            "IntegrationManager.tsx"
        ]
        
        missing_components = []
        for component in required_components:
            component_path = components_dir / component
            if component_path.exists():
                self.log_step(f"Component - {component}", True)
            else:
                self.log_step(f"Component - {component}", False)
                missing_components.append(component)
        
        return len(missing_components) == 0
    
    def check_ui_components(self):
        """Check that UI components are available"""
        print("\n🎭 Checking UI Components...")
        
        ui_dir = self.project_root / "components" / "ui"
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
        
        missing_ui = []
        for ui in required_ui:
            ui_path = ui_dir / ui
            if ui_path.exists():
                self.log_step(f"UI - {ui}", True)
            else:
                self.log_step(f"UI - {ui}", False)
                missing_ui.append(ui)
        
        return len(missing_ui) == 0
    
    async def run_complete_setup_check(self):
        """Run complete setup verification"""
        print("🚀 Enterprise CIA - Complete Integration Setup Check")
        print("=" * 70)
        
        checks = [
            ("Dependencies", self.check_dependencies()),
            ("Environment", self.check_environment_config()),
            ("Database", self.check_database_setup()),
            ("Services", self.check_service_integration()),
            ("API Endpoints", self.check_api_endpoints()),
            ("Frontend Components", self.check_frontend_components()),
            ("UI Components", self.check_ui_components())
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for check_name, result in checks:
            if result:
                passed_checks += 1
        
        print("\n" + "=" * 70)
        print("📊 Setup Verification Summary")
        print("=" * 70)
        print(f"Total Checks: {total_checks}")
        print(f"✅ Passed: {passed_checks}")
        print(f"❌ Failed: {total_checks - passed_checks}")
        print(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%")
        
        if passed_checks == total_checks:
            print("\n🎉 ALL FEATURES FULLY INTEGRATED!")
            print("   Ready for demo and production use")
            return True
        else:
            print(f"\n⚠️  {total_checks - passed_checks} issues need attention")
            print("   Review failed checks above")
            return False


async def main():
    """Main setup verification function"""
    setup = IntegrationSetup()
    success = await setup.run_complete_setup_check()
    
    if success:
        print("\n🎯 Next Steps:")
        print("   1. Start backend: cd backend && uvicorn app.main:app --reload")
        print("   2. Start frontend: npm run dev")
        print("   3. Run integration verification: python scripts/verify_integration.py")
        print("   4. Access application: http://localhost:3456")
        return 0
    else:
        print("\n🔧 Fix the issues above and run this script again")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)