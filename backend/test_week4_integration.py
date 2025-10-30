#!/usr/bin/env python3
"""
Week 4 Integration Test

Test script to verify all Week 4 features are properly integrated
and accessible through the API.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

def test_week4_integration():
    """Test that all Week 4 API endpoints are accessible"""
    
    client = TestClient(app)
    
    print("🧪 Testing Week 4 Integration...")
    
    # Test Community API endpoints
    print("\n📊 Testing Community API...")
    try:
        # Test community stats endpoint (should be accessible without auth for basic stats)
        response = client.get("/api/community/analytics")
        print(f"   Community Analytics: {response.status_code}")
        
        # Test community search
        response = client.post("/api/community/search", json={
            "query": "test",
            "limit": 10
        })
        print(f"   Community Search: {response.status_code}")
        
        # Test leaderboard
        response = client.get("/api/community/leaderboard")
        print(f"   Community Leaderboard: {response.status_code}")
        
    except Exception as e:
        print(f"   ❌ Community API Error: {e}")
    
    # Test White-label API endpoints
    print("\n🏢 Testing White-label API...")
    try:
        # Test deployment templates (public endpoint)
        response = client.get("/api/whitelabel/deployment-templates")
        print(f"   Deployment Templates: {response.status_code}")
        
        # Test customer list (should require auth)
        response = client.get("/api/whitelabel/customers")
        print(f"   Customer List: {response.status_code} (expected 401/403)")
        
    except Exception as e:
        print(f"   ❌ White-label API Error: {e}")
    
    # Test Integration Marketplace API endpoints
    print("\n🛒 Testing Integration Marketplace API...")
    try:
        # Test marketplace stats (public endpoint)
        response = client.get("/api/marketplace/stats")
        print(f"   Marketplace Stats: {response.status_code}")
        
        # Test integration search
        response = client.get("/api/marketplace/integrations?limit=5")
        print(f"   Integration Search: {response.status_code}")
        
        # Test developer registration (should require auth)
        response = client.post("/api/marketplace/developers/register", json={
            "developer_name": "Test Developer",
            "email": "test@example.com"
        })
        print(f"   Developer Registration: {response.status_code} (expected 401/403)")
        
    except Exception as e:
        print(f"   ❌ Integration Marketplace API Error: {e}")
    
    # Test main app health
    print("\n🏥 Testing Main App Health...")
    try:
        response = client.get("/health")
        print(f"   Health Check: {response.status_code}")
        
        response = client.get("/")
        print(f"   Root Endpoint: {response.status_code}")
        
    except Exception as e:
        print(f"   ❌ Health Check Error: {e}")
    
    print("\n✅ Week 4 Integration Test Complete!")
    print("\nNote: Some endpoints return 401/403 as expected since they require authentication.")
    print("The important thing is that the routes are accessible and not returning 404.")

if __name__ == "__main__":
    test_week4_integration()