#!/bin/bash

# Backend Server Startup Script
# Kills any existing process on port 8765 before starting

PORT=8765

echo "🔍 Checking for existing processes on port $PORT..."

# Kill any process using port 8765 (works on macOS and Linux)
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "⚠️  Found existing process(es) on port $PORT"
    PIDS=$(lsof -ti:$PORT)
    echo "🛑 Killing process(es): $PIDS"
    kill -9 $PIDS 2>/dev/null
    sleep 1
    echo "✅ Port $PORT is now free"
else
    echo "✅ Port $PORT is available"
fi

# Change to backend directory
cd "$(dirname "$0")/../backend" || exit 1

# Check if .env file exists (in parent directory)
if [ ! -f ../.env ]; then
    echo "⚠️  Warning: .env file not found in project root"
    echo "   Backend will use default configuration"
fi

# Start backend server
echo "🚀 Starting FastAPI backend server on port $PORT..."
echo "   API will be available at http://localhost:$PORT"
echo "   API docs at http://localhost:$PORT/docs"
echo ""

# Load environment variables from parent .env if it exists
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
    uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload --env-file ../.env
else
    uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload
fi

