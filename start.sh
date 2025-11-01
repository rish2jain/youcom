#!/bin/bash

# Enterprise CIA - Unified Service Startup Script
# Starts all services: Docker (PostgreSQL, Redis), Backend, and Frontend
# Run from project root: ./start.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Ports
BACKEND_PORT=8765
FRONTEND_PORT=3456
POSTGRES_PORT=5433
REDIS_PORT=6380

# PID files for tracking processes
BACKEND_PID_FILE="/tmp/cia_backend.pid"
FRONTEND_PID_FILE="/tmp/cia_frontend.pid"

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down all services...${NC}"
    
    # Kill backend if running
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}   Stopping backend (PID: $BACKEND_PID)${NC}"
            kill "$BACKEND_PID" 2>/dev/null || kill -9 "$BACKEND_PID" 2>/dev/null || true
        fi
        rm -f "$BACKEND_PID_FILE"
    fi
    
    # Kill frontend if running
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}   Stopping frontend (PID: $FRONTEND_PID)${NC}"
            kill "$FRONTEND_PID" 2>/dev/null || kill -9 "$FRONTEND_PID" 2>/dev/null || true
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi
    
    # Kill any processes on ports
    if lsof -ti:$BACKEND_PORT > /dev/null 2>&1; then
        echo -e "${YELLOW}   Cleaning up port $BACKEND_PORT${NC}"
        lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
    fi
    
    if lsof -ti:$FRONTEND_PORT > /dev/null 2>&1; then
        echo -e "${YELLOW}   Cleaning up port $FRONTEND_PORT${NC}"
        lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
    fi
    
    # Optionally stop Docker services (commented out to preserve data)
    # echo -e "${YELLOW}   Stopping Docker services...${NC}"
    # docker-compose down > /dev/null 2>&1 || true
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM EXIT

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo -e "${YELLOW}   Creating from .env.example if it exists...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}   Please edit .env and add your YOU_API_KEY${NC}"
    fi
fi

echo -e "${BLUE}🚀 Starting Enterprise CIA Services${NC}"
echo ""

# Step 1: Start Docker services (PostgreSQL and Redis)
echo -e "${BLUE}📦 Step 1: Starting Docker services (PostgreSQL, Redis)...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed or not in PATH${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo -e "${YELLOW}   Please start Docker Desktop and try again${NC}"
    exit 1
fi

# Start only postgres and redis services
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo -e "${BLUE}   Waiting for PostgreSQL to be ready...${NC}"
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ PostgreSQL is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}   ❌ PostgreSQL failed to start within 30 seconds${NC}"
        exit 1
    fi
    sleep 1
done

# Wait for Redis to be ready
echo -e "${BLUE}   Waiting for Redis to be ready...${NC}"
for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Redis is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}   ⚠️  Redis may not be ready, but continuing...${NC}"
        break
    fi
    sleep 1
done

echo ""

# Step 2: Check and free ports
echo -e "${BLUE}🔍 Step 2: Checking ports...${NC}"

# Check backend port
if lsof -ti:$BACKEND_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}   ⚠️  Port $BACKEND_PORT is in use${NC}"
    OLD_PIDS=$(lsof -ti:$BACKEND_PORT)
    echo -e "${YELLOW}   🛑 Killing existing process(es): $OLD_PIDS${NC}"
    echo "$OLD_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Check frontend port
if lsof -ti:$FRONTEND_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}   ⚠️  Port $FRONTEND_PORT is in use${NC}"
    OLD_PIDS=$(lsof -ti:$FRONTEND_PORT)
    echo -e "${YELLOW}   🛑 Killing existing process(es): $OLD_PIDS${NC}"
    echo "$OLD_PIDS" | xargs kill -9 2>/dev/null || true
    sleep 1
fi

echo -e "${GREEN}   ✅ Ports are available${NC}"
echo ""

# Step 3: Start Backend
echo -e "${BLUE}🔧 Step 3: Starting FastAPI Backend...${NC}"

cd "$PROJECT_ROOT/backend"

# Check if Python dependencies are installed
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}   ⚠️  Python virtual environment not found${NC}"
    echo -e "${YELLOW}   💡 Tip: Create a venv and install requirements${NC}"
fi

# Start backend server
echo -e "${BLUE}   Starting backend server on port $BACKEND_PORT...${NC}"

# Export environment variables if .env exists
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | grep -v '^$' | xargs)
fi

# Start backend in background
if [ -f ../.env ]; then
    uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload --env-file ../.env > /tmp/cia_backend.log 2>&1 &
else
    uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > /tmp/cia_backend.log 2>&1 &
fi

BACKEND_PID=$!
echo "$BACKEND_PID" > "$BACKEND_PID_FILE"

# Wait for backend to be ready
echo -e "${BLUE}   Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -f http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Backend is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}   ⚠️  Backend may not be fully ready, but continuing...${NC}"
        break
    fi
    sleep 1
done

cd "$PROJECT_ROOT"
echo ""

# Step 4: Start Frontend
echo -e "${BLUE}🌐 Step 4: Starting Next.js Frontend...${NC}"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}   ⚠️  Node modules not found, installing dependencies...${NC}"
    npm install
fi

# Start frontend server
echo -e "${BLUE}   Starting frontend server on port $FRONTEND_PORT...${NC}"

# Start frontend in background, redirect output to log file
# Note: npm run dev already sets port 3456, so we just run it
npm run dev > /tmp/cia_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"

# Wait for frontend to be ready
echo -e "${BLUE}   Waiting for frontend to be ready...${NC}"
for i in {1..60}; do
    if curl -f http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Frontend is ready${NC}"
        break
    fi
    if [ $i -eq 60 ]; then
        echo -e "${YELLOW}   ⚠️  Frontend may not be fully ready, but continuing...${NC}"
        break
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Enterprise CIA is now running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
echo -e "   ${GREEN}✅${NC} PostgreSQL:  localhost:$POSTGRES_PORT"
echo -e "   ${GREEN}✅${NC} Redis:       localhost:$REDIS_PORT"
echo -e "   ${GREEN}✅${NC} Backend API: http://localhost:$BACKEND_PORT"
echo -e "   ${GREEN}✅${NC} Frontend:    http://localhost:$FRONTEND_PORT"
echo ""
echo -e "${BLUE}📚 Quick Links:${NC}"
echo -e "   ${BLUE}•${NC} Frontend:        http://localhost:$FRONTEND_PORT"
echo -e "   ${BLUE}•${NC} API Docs:        http://localhost:$BACKEND_PORT/docs"
echo -e "   ${BLUE}•${NC} Health Check:    http://localhost:$BACKEND_PORT/health"
echo ""
echo -e "${BLUE}📝 Logs:${NC}"
echo -e "   ${BLUE}•${NC} Backend log:     tail -f /tmp/cia_backend.log"
echo -e "   ${BLUE}•${NC} Frontend log:    tail -f /tmp/cia_frontend.log"
echo ""
echo -e "${YELLOW}💡 Press Ctrl+C to stop all services${NC}"
echo ""

# Function to check service health periodically
check_health() {
    while true; do
        sleep 30
        
        # Check backend by port and health endpoint instead of PID
        if ! lsof -ti:$BACKEND_PORT > /dev/null 2>&1; then
            echo -e "${RED}⚠️  Backend process died!${NC}"
            echo -e "${RED}   Check logs: tail -f /tmp/cia_backend.log${NC}"
        elif ! curl -f http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Backend health check failed${NC}"
            echo -e "${YELLOW}   Check logs: tail -f /tmp/cia_backend.log${NC}"
        fi
        
        # Check frontend by port instead of PID (npm spawns child processes)
        if ! lsof -ti:$FRONTEND_PORT > /dev/null 2>&1; then
            echo -e "${RED}⚠️  Frontend process died!${NC}"
            echo -e "${RED}   Check logs: tail -f /tmp/cia_frontend.log${NC}"
        elif ! curl -f http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Frontend health check failed${NC}"
            echo -e "${YELLOW}   Check logs: tail -f /tmp/cia_frontend.log${NC}"
        fi
    done
}

# Start health check in background
check_health &
HEALTH_CHECK_PID=$!

# Wait for processes
wait

