#!/bin/bash

# Enterprise CIA - Stop All Services Script
# Stops all running services: Backend, Frontend, and optionally Docker services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ports
BACKEND_PORT=8765
FRONTEND_PORT=3456

# PID files
BACKEND_PID_FILE="/tmp/cia_backend.pid"
FRONTEND_PID_FILE="/tmp/cia_frontend.pid"

echo -e "${BLUE}🛑 Stopping Enterprise CIA Services...${NC}"
echo ""

# Stop backend if running
if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat "$BACKEND_PID_FILE")
    if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}   Stopping backend (PID: $BACKEND_PID)${NC}"
        kill "$BACKEND_PID" 2>/dev/null || kill -9 "$BACKEND_PID" 2>/dev/null || true
        rm -f "$BACKEND_PID_FILE"
        echo -e "${GREEN}   ✅ Backend stopped${NC}"
    else
        rm -f "$BACKEND_PID_FILE"
    fi
fi

# Stop frontend if running
if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}   Stopping frontend (PID: $FRONTEND_PID)${NC}"
        kill "$FRONTEND_PID" 2>/dev/null || kill -9 "$FRONTEND_PID" 2>/dev/null || true
        rm -f "$FRONTEND_PID_FILE"
        echo -e "${GREEN}   ✅ Frontend stopped${NC}"
    else
        rm -f "$FRONTEND_PID_FILE"
    fi
fi

# Kill any processes on backend port
if lsof -ti:$BACKEND_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}   Cleaning up port $BACKEND_PORT${NC}"
    lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
fi

# Kill any processes on frontend port
if lsof -ti:$FRONTEND_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}   Cleaning up port $FRONTEND_PORT${NC}"
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
fi

# Optionally stop Docker services
if [ "$1" == "--docker" ] || [ "$1" == "-d" ]; then
    echo -e "${YELLOW}   Stopping Docker services (PostgreSQL, Redis)...${NC}"
    docker-compose down
    echo -e "${GREEN}   ✅ Docker services stopped${NC}"
else
    echo -e "${BLUE}   💡 Docker services are still running${NC}"
    echo -e "${BLUE}   💡 To stop them, run: ./stop.sh --docker${NC}"
fi

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"


