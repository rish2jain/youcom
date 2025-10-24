#!/bin/bash

# Enterprise CIA - Test Suite Runner
# Comprehensive testing for You.com API integration and all components

echo "🧪 Running Enterprise CIA Test Suite..."
echo "Testing You.com API integration and all components"

# Set environment variables for testing
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
export YOU_API_KEY="test_api_key_for_testing"
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export REDIS_URL="redis://localhost:6379"

# Reuse local virtual environment for speed
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "✨ Creating virtual environment in $VENV_DIR"
  python -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

if [ ! -f "$VENV_DIR/.tests-installed" ]; then
  echo "📦 Installing project + test dependencies..."
  pip install -r requirements.txt -r requirements-test.txt
  touch "$VENV_DIR/.tests-installed"
else
  echo "📦 Reusing cached dependencies"
fi

# Change to backend directory
cd backend

echo ""
echo "🔬 Running Unit Tests..."
echo "=========================="
pytest tests/test_schemas.py -v

echo ""
echo "🔧 Running You.com API Client Tests..."
echo "======================================"
pytest tests/test_you_client.py -v

echo ""
echo "🗄️  Running Database Model Tests..."
echo "==================================="
pytest tests/test_models.py -v

echo ""
echo "🌐 Running API Endpoint Tests..."
echo "==============================="
pytest tests/test_api_endpoints.py -v

echo ""
echo "🔄 Running Integration Tests..."
echo "==============================="
pytest tests/test_integration.py -v

echo ""
echo "📊 Running All Tests with Coverage..."
echo "===================================="
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing -v

echo ""
echo "✅ Test Suite Complete!"
echo ""
echo "📈 Coverage Report: htmlcov/index.html"
echo "🎯 Key Test Areas Covered:"
echo "   • You.com API Integration (News, Search, Chat, ARI)"
echo "   • Database Models and Relationships"
echo "   • API Endpoints and Error Handling"
echo "   • Complete Workflow Integration"
echo "   • Schema Validation and Edge Cases"
echo ""
echo "🏆 Ready for Hackathon Demo!"
