# Enterprise CIA - Quick Start Guide

**Last Updated**: October 31, 2025  
**Duration**: 5 minutes to running system

## 🚀 5-Minute Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- You.com API Key

### 1. Clone & Configure

```bash
# Clone repository
git clone <repository-url>
cd <repository-folder>  # Change to your cloned repository directory

# Copy environment file
cp .env.example .env
```

**Edit `.env` with your You.com API key:**

```bash
# Required - You.com API (all 4 APIs)
YOU_API_KEY=your_you_api_key_here

# Optional - Database (uses SQLite if not set)
DATABASE_URL=postgresql://user:password@localhost:5432/cia_db

# Optional - Redis (uses in-memory cache if not set)
REDIS_URL=redis://localhost:6379
```

### 2. Install Dependencies

```bash
# Node.js dependencies (run from project root)
npm install

# Python dependencies (run from backend directory)
cd backend
pip install -r requirements.txt
cd ..  # Return to project root
```

### 3. Start Services

```bash
# Terminal 1: Backend API
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8765

# Terminal 2: Frontend
npm run dev
```

### 4. Verify Setup

- **Frontend**: http://localhost:3000 (port shown by npm run dev)
- **Backend API**: http://localhost:8765/docs
- **Health Check**: http://localhost:8765/health

## ✅ Quick Verification

### Test You.com API Connection

```bash
curl -H "X-API-Key: $YOU_API_KEY" http://localhost:8765/api/v1/health/you-apis
```

**Expected Response**:

```json
{
  "overall_status": "healthy",
  "apis": {
    "news": { "status": "healthy" },
    "search": { "status": "healthy" },
    "chat": { "status": "healthy" },
    "ari": { "status": "healthy" }
  }
}
```

### Test Frontend

1. Open http://localhost:3456
2. Navigate to "Individual Research" tab
3. Search for "OpenAI"
4. Verify results appear

## 🎬 Demo Mode

If you don't have a You.com API key yet:

```bash
# Set demo mode in .env
DEMO_MODE=true
YOU_API_KEY=demo_key
```

Demo mode provides:

- Pre-loaded sample data
- Simulated API responses
- Full UI functionality
- No external API calls

## 🔧 Optional: Full Database Setup

For complete functionality with persistence:

```bash
# Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Run database migrations
cd backend
alembic upgrade head

# Seed demo data (requires valid YOU_API_KEY)
cd ..
python scripts/seed_demo_data.py
```

## 🚨 Troubleshooting

### Common Issues

**Backend won't start**:

```bash
# Check Python version
python --version  # Should be 3.11+

# Install dependencies
pip install -r requirements.txt
```

**Frontend won't start**:

```bash
# Check Node version
node --version  # Should be 18+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**API calls failing**:

```bash
# Verify API key is set
echo $YOU_API_KEY

# Test API key directly
curl -H "X-API-Key: $YOU_API_KEY" https://api.ydc-index.io/livenews?q=test&count=1
```

### Quick Fixes

**Port conflicts**:

```bash
# Use different ports
uvicorn app.main:app --port 8766  # Backend
npm run dev -- -p 3457          # Frontend
```

**Database issues**:

```bash
# Use SQLite (no setup required)
# Remove DATABASE_URL from .env
```

**Redis issues**:

```bash
# Use in-memory cache
# Remove REDIS_URL from .env
```

## 🎯 Next Steps

Once running:

1. **[User Guide](../user/USER_GUIDE.md)** - Learn all features
2. **[Demo Guide](../user/DEMO_GUIDE.md)** - Prepare presentations
3. **[Implementation Guide](IMPLEMENTATION_GUIDE.md)** - Full setup details

## 📞 Need Help?

- **Setup Issues**: Check [Troubleshooting Guide](../development/TROUBLESHOOTING.md)
- **API Problems**: See [API Integration Guide](../development/API_INTEGRATION.md)
- **Feature Questions**: Read [User Guide](../user/USER_GUIDE.md)

---

**Ready in 5 minutes!** 🚀
