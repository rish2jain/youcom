#!/usr/bin/env python3
"""
Quick setup script for You.com API resilience implementation.
Run this to verify everything is configured correctly.
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        "YOU_API_KEY",
        "DATABASE_URL", 
        "REDIS_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    
    print("✅ Environment variables configured")
    return True

def check_files():
    """Check if all resilience files are in place"""
    print("\n📁 Checking resilience files...")
    
    required_files = [
        "app/services/resilient_you_client.py",
        "app/config/resilience.py",
        "app/api/monitoring.py",
        "test_resilience.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All resilience files present")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        "httpx",
        "redis",
        "tenacity",
        "fastapi",
        "sqlalchemy"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True

def create_env_template():
    """Create .env template with resilience settings"""
    print("\n📝 Creating .env template...")
    
    env_template = """# You.com API Configuration
YOU_API_KEY=your_you_api_key_here

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost/cia_db

# Redis Configuration (for caching and circuit breaker state)
REDIS_URL=redis://localhost:6379

# Resilience Configuration
ENABLE_CIRCUIT_BREAKERS=true
ENABLE_RATE_LIMITING=true
ENABLE_QUERY_OPTIMIZATION=true
ENABLE_FALLBACK_DATA=true
HACKATHON_MODE=true

# Demo Mode (uses fallback data when APIs fail)
DEMO_MODE=false

# Environment
ENVIRONMENT=development
"""
    
    if not Path(".env").exists():
        with open(".env", "w") as f:
            f.write(env_template)
        print("✅ Created .env template")
    else:
        print("ℹ️ .env file already exists")

def print_next_steps():
    """Print next steps for implementation"""
    print("\n🚀 Next Steps:")
    print("1. Update your .env file with actual API keys")
    print("2. Run: python test_resilience.py")
    print("3. Start the FastAPI server: uvicorn app.main:socket_app --reload")
    print("4. Check monitoring dashboard: http://localhost:8000/api/v1/monitoring/dashboard")
    print("5. Check resilience status: http://localhost:8000/api/v1/health/resilience")
    
    print("\n📊 Key Endpoints:")
    print("- Health Check: GET /api/v1/health/you-apis")
    print("- Resilience Status: GET /api/v1/health/resilience") 
    print("- Monitoring Dashboard: GET /api/v1/monitoring/dashboard")
    print("- API Performance: GET /api/v1/monitoring/performance/{api_type}")
    print("- Active Alerts: GET /api/v1/monitoring/alerts")
    print("- Reset Circuit Breaker: POST /api/v1/monitoring/circuit-breaker/{api_type}/reset")
    
    print("\n🎯 Discord Insights Implemented:")
    print("✅ Circuit breakers for API failures")
    print("✅ Aggressive rate limiting (2-10s intervals)")
    print("✅ Query optimization (avoid boolean operators)")
    print("✅ Timeout protection for hanging custom agents")
    print("✅ Fallback data when APIs fail")
    print("✅ Comprehensive monitoring and alerting")

def main():
    """Run setup checks"""
    print("🔧 You.com API Resilience Setup")
    print("=" * 40)
    
    all_good = True
    
    # Run checks
    if not check_environment():
        all_good = False
    
    if not check_files():
        all_good = False
    
    if not check_dependencies():
        all_good = False
    
    # Create template
    create_env_template()
    
    if all_good:
        print("\n✅ Setup complete! Ready for resilient You.com API integration")
    else:
        print("\n❌ Setup incomplete. Please fix the issues above.")
    
    print_next_steps()

if __name__ == "__main__":
    main()