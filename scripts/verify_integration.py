#!/usr/bin/env python3
"""
Comprehensive integration verification script for Enterprise CIA
Tests all implemented features and their integration
"""

import asyncio
import sys
import os
import httpx
from typing import Dict, Any, List
import json

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.notion_service import NotionService
from app.services.salesforce_service import SalesforceService
from app.services.analytics_service import PredictiveAnalyticsService


class IntegrationVerifier:
    """Comprehensive integration verification"""
    
    def __init__(self, base_url: str = "http://localhost:8765"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
    
    def log_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        }
        self.results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        
        if details and not success:
            print(f"   Details: {details}")
    
    async def test_backend_health(self):
        """Test backend health and API availability"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        "Backend Health",
                        True,
                        f"Backend is healthy - {data.get('service', 'Unknown')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Backend Health",
                        False,
                        f"Backend unhealthy - HTTP {response.status_code}"
                    )
                    return False
        except Exception as e:
            self.log_result(
                "Backend Health",
                False,
                f"Backend connection failed: {str(e)}"
            )
            return False
    
    async def test_you_api_integration(self):
        """Test You.com API integration"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/health/you-apis")
                
                if response.status_code == 200:
                    data = response.json()
                    overall_status = data.get("overall_status", "unknown")
                    apis = data.get("apis", {})
                    
                    self.log_result(
                        "You.com API Integration",
                        overall_status in ["healthy", "degraded"],
                        f"Overall status: {overall_status}, APIs: {len(apis)}",
                        {"apis": list(apis.keys())}
                    )
                    return True
                else:
                    self.log_result(
                        "You.com API Integration",
                        False,
                        f"API health check failed - HTTP {response.status_code}"
                    )
                    return False
        except Exception as e:
            self.log_result(
                "You.com API Integration",
                False,
                f"API health check error: {str(e)}"
            )
            return False
    
    async def test_resilience_system(self):
        """Test resilience and circuit breaker system"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/health/resilience")
                
                if response.status_code == 200:
                    data = response.json()
                    summary = data.get("summary", {})
                    total_circuits = summary.get("total_circuits", 0)
                    
                    self.log_result(
                        "Resilience System",
                        True,
                        f"Circuit breakers active: {total_circuits}",
                        summary
                    )
                    return True
                else:
                    self.log_result(
                        "Resilience System",
                        False,
                        f"Resilience check failed - HTTP {response.status_code}"
                    )
                    return False
        except Exception as e:
            self.log_result(
                "Resilience System",
                False,
                f"Resilience check error: {str(e)}"
            )
            return False
    
    async def test_analytics_endpoints(self):
        """Test predictive analytics endpoints"""
        endpoints = [
            ("/api/v1/analytics/market-landscape", "Market Landscape"),
            ("/api/v1/analytics/executive-summary", "Executive Summary"),
            ("/api/v1/analytics/api-usage-predictions", "API Usage Predictions")
        ]
        
        success_count = 0
        
        for endpoint, name in endpoints:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    
                    if response.status_code == 200:
                        self.log_result(
                            f"Analytics - {name}",
                            True,
                            "Endpoint accessible and responding"
                        )
                        success_count += 1
                    else:
                        self.log_result(
                            f"Analytics - {name}",
                            False,
                            f"HTTP {response.status_code}"
                        )
            except Exception as e:
                self.log_result(
                    f"Analytics - {name}",
                    False,
                    f"Error: {str(e)}"
                )
        
        return success_count == len(endpoints)
    
    async def test_integration_endpoints(self):
        """Test integration management endpoints"""
        endpoints = [
            ("/api/v1/integrations/?workspace_id=1", "List Integrations"),
        ]
        
        success_count = 0
        
        for endpoint, name in endpoints:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    
                    # 401 is acceptable for auth-required endpoints
                    if response.status_code in [200, 401]:
                        self.log_result(
                            f"Integration - {name}",
                            True,
                            f"Endpoint accessible (HTTP {response.status_code})"
                        )
                        success_count += 1
                    else:
                        self.log_result(
                            f"Integration - {name}",
                            False,
                            f"HTTP {response.status_code}"
                        )
            except Exception as e:
                self.log_result(
                    f"Integration - {name}",
                    False,
                    f"Error: {str(e)}"
                )
        
        return success_count == len(endpoints)
    
    async def test_core_endpoints(self):
        """Test core CIA endpoints"""
        endpoints = [
            ("/api/v1/demo/you-apis", "Demo Showcase"),
            ("/api/v1/metrics/api-usage", "API Metrics"),
        ]
        
        success_count = 0
        
        for endpoint, name in endpoints:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    
                    if response.status_code in [200, 401]:
                        self.log_result(
                            f"Core - {name}",
                            True,
                            f"Endpoint accessible (HTTP {response.status_code})"
                        )
                        success_count += 1
                    else:
                        self.log_result(
                            f"Core - {name}",
                            False,
                            f"HTTP {response.status_code}"
                        )
            except Exception as e:
                self.log_result(
                    f"Core - {name}",
                    False,
                    f"Error: {str(e)}"
                )
        
        return success_count == len(endpoints)
    
    def test_service_imports(self):
        """Test that all services can be imported"""
        services = [
            ("NotionService", NotionService),
            ("SalesforceService", SalesforceService),
            ("PredictiveAnalyticsService", PredictiveAnalyticsService),
        ]
        
        success_count = 0
        
        for name, service_class in services:
            try:
                # Try to instantiate the service
                if name == "NotionService":
                    service = service_class("test_token")
                elif name == "SalesforceService":
                    service = service_class("https://test.salesforce.com", "test_token")
                else:
                    service = service_class()
                
                self.log_result(
                    f"Service Import - {name}",
                    True,
                    "Service can be imported and instantiated"
                )
                success_count += 1
            except Exception as e:
                self.log_result(
                    f"Service Import - {name}",
                    False,
                    f"Import/instantiation error: {str(e)}"
                )
        
        return success_count == len(services)
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Enterprise CIA Integration Verification")
        print("=" * 60)
        
        # Test service imports first (doesn't require running backend)
        self.test_service_imports()
        
        # Test backend connectivity
        backend_healthy = await self.test_backend_health()
        
        if backend_healthy:
            # Run API tests
            await self.test_you_api_integration()
            await self.test_resilience_system()
            await self.test_analytics_endpoints()
            await self.test_integration_endpoints()
            await self.test_core_endpoints()
        else:
            print("\n⚠️  Backend not running - skipping API tests")
            print("   Start backend with: cd backend && uvicorn app.main:app --reload")
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 Integration Verification Summary")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
        
        print("\n🎯 Integration Status:")
        if passed_tests == total_tests:
            print("   ✅ ALL FEATURES FULLY INTEGRATED")
        elif passed_tests >= total_tests * 0.8:
            print("   🟡 MOSTLY INTEGRATED (some issues)")
        else:
            print("   ❌ INTEGRATION INCOMPLETE")
        
        # Feature-specific status
        print("\n📋 Feature Status:")
        feature_status = {
            "Backend Health": any(r["test"] == "Backend Health" and r["success"] for r in self.results),
            "You.com APIs": any("You.com API" in r["test"] and r["success"] for r in self.results),
            "Resilience System": any("Resilience" in r["test"] and r["success"] for r in self.results),
            "Analytics Engine": any("Analytics" in r["test"] and r["success"] for r in self.results),
            "Integration Management": any("Integration" in r["test"] and r["success"] for r in self.results),
            "Service Architecture": any("Service Import" in r["test"] and r["success"] for r in self.results),
        }
        
        for feature, status in feature_status.items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {feature}")


async def main():
    """Main verification function"""
    verifier = IntegrationVerifier()
    await verifier.run_all_tests()
    
    # Return exit code based on results
    failed_tests = sum(1 for r in verifier.results if not r["success"])
    return 0 if failed_tests == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)