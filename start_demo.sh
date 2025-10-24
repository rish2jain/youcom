#!/bin/bash

# Enterprise CIA - Hackathon Demo Startup Script
# This script sets up and starts the complete demo environment

echo "🚀 Starting Enterprise CIA Hackathon Demo..."
echo "Showcasing all 4 You.com APIs in perfect orchestration!"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your YOU_API_KEY before continuing"
    echo "   YOU_API_KEY=your_you_api_key_here"
    exit 1
fi

# Check if YOU_API_KEY is set
if ! grep -q "YOU_API_KEY=.*[^=]" .env; then
    echo "❌ YOU_API_KEY not set in .env file"
    echo "📝 Please edit .env file and add your You.com API key:"
    echo "   YOU_API_KEY=your_you_api_key_here"
    exit 1
fi

echo "✅ Environment configuration found"

# Start database and Redis
echo "🐘 Starting PostgreSQL and Redis..."
docker-compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
cd backend
python -c "
import asyncio
from app.database import engine, Base

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ Database tables created')

asyncio.run(create_tables())
"

# Seed demo data
echo "🌱 Seeding demo data..."
python ../scripts/seed_demo_data.py

# Start backend server in background
echo "🚀 Starting FastAPI backend server..."
uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload --env-file ../.env &
BACKEND_PID=$!
cd ..

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Start frontend server in background
echo "🌐 Starting Next.js frontend server..."
npm run dev -- --port 3456 &
FRONTEND_PID=$!

# Wait a moment for servers to start
sleep 3

echo ""
echo "🎉 Enterprise CIA Demo is now running!"
echo ""
echo "🌐 Frontend: http://localhost:3456"
echo "🔧 Backend API: http://localhost:8765"
echo "📚 API Docs: http://localhost:8765/docs"
echo ""
echo "🎯 Demo Features:"
echo "   • Enterprise Mode: Competitive monitoring with Impact Cards"
echo "   • Individual Mode: Instant company research"
echo "   • All 4 You.com APIs: News, Search, Chat, ARI"
echo "   • Real-time processing with WebSocket updates"
echo "   • Pre-seeded demo data ready for presentation"
echo ""
echo "🏆 Hackathon Demo Script:"
echo "   1. Enterprise: Add 'OpenAI' competitor → Generate Impact Card"
echo "   2. Individual: Research 'Perplexity AI' → View comprehensive report"
echo "   3. Show API usage dashboard with all 4 You.com APIs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    docker-compose down
    echo "✅ Demo stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Keep script running
wait
