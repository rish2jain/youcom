#!/bin/bash

# Enterprise CIA - One-Click Demo Setup
# Sets up everything needed for the perfect hackathon demo

set -e  # Exit on error

echo "🚀 Enterprise CIA - One-Click Demo Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8765
FRONTEND_PORT=3000

# Step 1: Check dependencies
echo -e "${BLUE}📋 Step 1: Checking dependencies...${NC}"
echo ""

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "  ${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "  ${YELLOW}⚠️  $1 not found${NC}"
        return 1
    fi
}

check_command "python3" || { echo "Install Python 3.8+"; exit 1; }
check_command "node" || { echo "Install Node.js 18+"; exit 1; }
check_command "npm" || { echo "Install npm"; exit 1; }
check_command "psql" || echo "  (PostgreSQL CLI - optional)"
check_command "redis-cli" || echo "  (Redis CLI - optional)"

echo ""

# Step 2: Environment setup
echo -e "${BLUE}📝 Step 2: Setting up environment...${NC}"
echo ""

if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# You.com API Configuration
YOU_API_KEY=your-api-key-here

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cia_hackathon

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=$(openssl rand -hex 32)

# Email (Optional - for demo you can skip)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=noreply@enterprisecia.com

# Environment
ENVIRONMENT=development
EOF
    echo -e "${GREEN}✅ .env created${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: Add your YOU_API_KEY to .env${NC}"
    echo ""
    read -p "Press ENTER when you've added your API key..."
else
    echo -e "${GREEN}✅ .env already exists${NC}"
fi

echo ""

# Step 3: Install dependencies
echo -e "${BLUE}📦 Step 3: Installing dependencies...${NC}"
echo ""

# Backend
cd backend
echo "Installing Python dependencies..."
pip install -r requirements.txt
cd ..

# Frontend
echo "Installing Node dependencies..."
npm install

# Additional packages for demo
npm install canvas-confetti

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 4: Database setup
echo -e "${BLUE}💾 Step 4: Setting up database...${NC}"
echo ""

# Check if PostgreSQL is running
if pg_isready &> /dev/null; then
    echo "PostgreSQL is running ✅"

    # Create database if it doesn't exist
    psql -U postgres -lqt | cut -d \| -f 1 | grep -qw cia_hackathon || {
        echo "Creating database..."
        createdb -U postgres cia_hackathon
    }

    # Run migrations
    cd backend
    echo "Running database migrations..."
    alembic upgrade head
    cd ..

    echo -e "${GREEN}✅ Database ready${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL not detected${NC}"
    echo "Start PostgreSQL or use Docker:"
    echo "  docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres"
    read -p "Press ENTER when PostgreSQL is running..."
fi

echo ""

# Step 5: Seed demo data
echo -e "${BLUE}🌱 Step 5: Seeding demo data...${NC}"
echo ""

echo "This will create:"
echo "  • Demo user: demo@enterprisecia.com / demo2024"
echo "  • 6 competitors with impact cards"
echo "  • 3 company research records"
echo "  • 1000+ API call logs"
echo ""

read -p "Seed demo data? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd backend
    python scripts/seed_demo_data.py
    cd ..
    echo -e "${GREEN}✅ Demo data seeded${NC}"
else
    echo "Skipped demo data seeding"
fi

echo ""

# Step 6: Build frontend
echo -e "${BLUE}🏗️  Step 6: Building frontend...${NC}"
echo ""

npm run build

echo -e "${GREEN}✅ Frontend built${NC}"
echo ""

# Create start scripts
echo -e "${BLUE}📜 Step 7: Creating start scripts...${NC}"
echo ""

# Backend start script
cat > start-backend.sh << 'EOF'
#!/bin/bash
cd backend
echo "🚀 Starting backend on port 8765..."
uvicorn app.main:socket_app --reload --port 8765
EOF
chmod +x start-backend.sh

# Frontend start script
cat > start-frontend.sh << 'EOF'
#!/bin/bash
echo "🎨 Starting frontend on port 3000..."
npm run dev
EOF
chmod +x start-frontend.sh

# Combined start script
cat > start-demo.sh << 'EOF'
#!/bin/bash

# Start backend in background
echo "🚀 Starting Enterprise CIA..."
echo ""

# Start backend
echo "Starting backend on port 8765..."
cd backend && uvicorn app.main:socket_app --reload --port 8765 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend on port 3456..."
PORT=3456 npm run dev &
FRONTEND_PID=$!

echo ""
echo "✨ Enterprise CIA is running!"
echo ""
echo "  Backend:  http://localhost:8765"
echo "  Frontend: http://localhost:3456"
echo "  API Docs: http://localhost:8765/docs"
echo ""
echo "  Demo Login:"
echo "    Email: demo@enterprisecia.com"
echo "    Password: demo2024"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
EOF
chmod +x start-demo.sh

echo -e "${GREEN}✅ Start scripts created${NC}"
echo ""

# Final instructions
echo ""
echo "═══════════════════════════════════════════════"
echo -e "${GREEN}✨ Demo setup complete!${NC}"
echo "═══════════════════════════════════════════════"
echo ""
echo "🎯 Quick Start:"
echo ""
echo "  1. Start everything:"
echo "     ./start-demo.sh"
echo ""
echo "  2. Open browser:"
echo "     http://localhost:3000"
echo ""
echo "  3. Login with:"
echo "     demo@enterprisecia.com / demo2024"
echo ""
echo "  4. Record demo:"
echo "     python scripts/record_demo.py"
echo ""
echo "📚 Additional Commands:"
echo ""
echo "  Backend only:   ./start-backend.sh"
echo "  Frontend only:  ./start-frontend.sh"
echo "  Deploy:         ./scripts/deploy.sh"
echo ""
echo "📹 Recording Tips:"
echo "  • Run demo seed first (creates impressive data)"
echo "  • Use demo credentials to login"
echo "  • Follow VIDEO_TIMESTAMPS.md guide"
echo "  • Practice a few times before recording"
echo ""
echo "🏆 You're ready to win the hackathon!"
echo ""
