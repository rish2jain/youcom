# Enterprise CIA - Complete Project Documentation Index

> **Competitive Intelligence Automation powered by You.com APIs**
> Last Updated: October 31, 2025

## 📚 Table of Contents

1. [Quick Navigation](#quick-navigation)
2. [Project Overview](#project-overview)
3. [Architecture Documentation](#architecture-documentation)
4. [API Reference](#api-reference)
5. [Development Guides](#development-guides)
6. [Component Documentation](#component-documentation)
7. [Testing & Quality](#testing--quality)
8. [Deployment](#deployment)

---

## Quick Navigation

### 🚀 Getting Started
- **New Users**: Start with [README.md](README.md)
- **Developers**: Follow [CLAUDE.md](CLAUDE.md) for development guidelines
- **API Integration**: See [You.com API Integration](#youcom-api-integration)

### 🎯 Common Tasks
| Task | Documentation |
|------|---------------|
| Setup development environment | [README.md](README.md#quick-start) |
| Understand You.com API workflow | [You.com API Integration](#youcom-api-integration) |
| Add new API endpoint | [CLAUDE.md](CLAUDE.md#adding-a-new-api-endpoint) |
| Run tests | [Testing Guide](#testing--quality) |
| Deploy application | [Deployment](#deployment) |

---

## Project Overview

### Core Concept
Enterprise CIA orchestrates **all 4 You.com APIs** in a coordinated workflow to automate competitive intelligence:

```
News API → Search API → Chat API (Custom Agents) → ARI API → Impact Card
```

### Key Features
- **📰 Real-time Monitoring**: <60 second detection time
- **🔍 Context Enrichment**: 400+ source research via ARI
- **🤖 Strategic Analysis**: Custom intelligence agents
- **📊 Enterprise Ready**: Team collaboration, integrations, compliance

### Technology Stack

**Backend** (`backend/`)
- Python 3.11+ with FastAPI (async)
- PostgreSQL 15+ with SQLAlchemy (async ORM)
- Redis 7+ for caching
- Socket.IO for WebSocket communication

**Frontend** (root)
- Next.js 14 with App Router
- React 18 + TypeScript
- Tailwind CSS
- Zustand + React Query (TanStack Query)

---

## Architecture Documentation

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  Next.js 14 + React 18 + TypeScript + Tailwind CSS         │
│  (http://localhost:3456)                                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ REST API + WebSocket
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend                           │
│                  (http://localhost:8765)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          You.com API Orchestrator                    │  │
│  │   (backend/app/services/you_client.py)               │  │
│  │                                                       │  │
│  │  News → Search → Chat → ARI → Impact Card           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   Database   │  │    Redis     │  │  Circuit         │ │
│  │  PostgreSQL  │  │   Caching    │  │  Breakers        │ │
│  │   (5433)     │  │   (6380)     │  │  (Resilience)    │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### You.com API Integration

**Orchestration Flow** (`backend/app/services/you_client.py`):

```python
class YouComOrchestrator:
    """
    Core orchestration class coordinating all 4 You.com APIs
    """

    async def generate_impact_card(competitor: str):
        # 1. NEWS API - Real-time detection
        news = await fetch_news(competitor)

        # 2. SEARCH API - Context enrichment
        context = await search_context(competitor)

        # 3. CHAT API - Strategic analysis (Custom Agents)
        analysis = await analyze_impact(news, context, competitor)

        # 4. ARI API - Deep synthesis (400+ sources)
        synthesis = await generate_research_report(competitor)

        return ImpactCard(...)
```

**API Endpoints**:
- News API: `https://api.ydc-index.io/livenews`
- Search API: `https://api.ydc-index.io/v1/search`
- Chat API: `https://api.you.com/v1/agents/runs`
- ARI API: `https://api.you.com/v1/agents/runs` (Express Agent)

**Caching Strategy**:
- News: 15 minutes (frequent updates)
- Search: 1 hour (moderate freshness)
- ARI: 7 days (stable research)

### Directory Structure

```
enterprise-cia/
├── app/                           # Next.js App Router pages
│   ├── page.tsx                   # Main dashboard
│   ├── layout.tsx                 # Root layout
│   └── providers.tsx              # React Query + context
│
├── components/                    # React components
│   ├── WatchList.tsx              # Competitor monitoring
│   ├── ImpactCardDisplay.tsx     # 4-tab Impact Card UI
│   ├── CompanyResearch.tsx        # Company profiles
│   ├── APIUsageDashboard.tsx     # Metrics dashboard
│   └── ErrorBoundary.tsx          # Error handling
│
├── lib/                           # Frontend utilities
│   ├── api.ts                     # Axios client (→ localhost:8765)
│   └── socket.ts                  # Socket.IO client
│
├── backend/                       # Python FastAPI backend
│   ├── app/
│   │   ├── main.py                # FastAPI application
│   │   ├── config.py              # Environment configuration
│   │   ├── database.py            # Async SQLAlchemy setup
│   │   │
│   │   ├── services/
│   │   │   ├── you_client.py      # ⭐ You.com orchestrator
│   │   │   ├── resilient_you_client.py  # Circuit breakers
│   │   │   ├── scheduler.py       # Automated alerts
│   │   │   └── soc2_service.py    # Security compliance
│   │   │
│   │   ├── api/                   # REST API endpoints
│   │   │   ├── impact.py          # Impact Card generation
│   │   │   ├── research.py        # Company research
│   │   │   ├── watch.py           # Watchlist management
│   │   │   ├── analytics.py       # Predictive analytics
│   │   │   ├── integrations.py    # Third-party integrations
│   │   │   └── ...                # Additional endpoints
│   │   │
│   │   ├── models/                # SQLAlchemy ORM models
│   │   │   ├── impact_card.py
│   │   │   ├── company_research.py
│   │   │   ├── watch_item.py
│   │   │   └── ...
│   │   │
│   │   └── schemas/               # Pydantic validation schemas
│   │       ├── impact.py
│   │       ├── research.py
│   │       └── ...
│   │
│   ├── alembic/                   # Database migrations
│   │   └── versions/              # Migration files (7 total)
│   │
│   └── tests/                     # Backend test suite
│       ├── test_you_client.py     # You.com integration tests
│       ├── test_error_handling_integration.py
│       └── ...
│
├── scripts/
│   └── seed_demo_data.py          # Demo data seeding
│
├── public/                        # Static assets
│
├── docker-compose.yml             # Infrastructure services
├── .env.example                   # Environment variables
├── package.json                   # Frontend dependencies
├── requirements.txt               # Backend dependencies
└── README.md                      # Project overview
```

---

## API Reference

### Core Intelligence Endpoints

#### Impact Card Generation
```
POST /api/v1/impact/generate
```

**Description**: Generate comprehensive Impact Card using all 4 You.com APIs

**Request**:
```json
{
  "competitor": "OpenAI",
  "keywords": ["GPT", "ChatGPT"]
}
```

**Response**:
```json
{
  "competitor_name": "OpenAI",
  "risk_score": 85,
  "risk_level": "HIGH",
  "confidence_score": 0.92,
  "total_sources": 427,
  "impact_areas": [
    {"area": "product", "score": 90, "weight": 0.35},
    {"area": "marketing", "score": 75, "weight": 0.25}
  ],
  "recommended_actions": [...],
  "key_insights": [...],
  "created_at": "2025-10-31T12:00:00Z"
}
```

**API Orchestration**:
1. News API: Fetch recent competitor activity
2. Search API: Enrich context with market data
3. Chat API: Analyze competitive impact (Custom Agent)
4. ARI API: Generate 400+ source research report

**See**: `backend/app/api/impact.py`

#### Company Research
```
POST /api/v1/research/company
```

**Description**: Generate instant company profile with 400+ sources

**Request**:
```json
{
  "company_name": "Perplexity AI"
}
```

**Response**:
```json
{
  "company_name": "Perplexity AI",
  "total_sources": 412,
  "search_results": {
    "count": 8,
    "results": [...]
  },
  "research_report": {
    "summary": "...",
    "key_insights": [...],
    "citations": [...]
  },
  "created_at": "2025-10-31T12:00:00Z"
}
```

**See**: `backend/app/api/research.py`

#### Competitor Watchlist
```
POST /api/v1/watch/
GET  /api/v1/watch/
DELETE /api/v1/watch/{id}
```

**See**: `backend/app/api/watch.py`

### Integration Endpoints

#### Notion Integration
```
POST /api/v1/integrations/notion/test
POST /api/v1/integrations/notion/sync-research
```

#### Salesforce Integration
```
POST /api/v1/integrations/salesforce/test
POST /api/v1/integrations/salesforce/sync-impact
```

**See**: `backend/app/api/integrations.py`

### Analytics Endpoints

```
GET /api/v1/analytics/competitor-trends/{name}
GET /api/v1/analytics/market-landscape
GET /api/v1/analytics/executive-summary
```

**See**: `backend/app/api/analytics.py`

### System Health Endpoints

```
GET /health
GET /api/v1/health/you-apis
GET /api/v1/health/resilience
```

**See**: `backend/app/main.py`

---

## Development Guides

### Environment Setup

**Prerequisites**:
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- You.com API Key ([get key](https://api.you.com))

**Quick Start**:
```bash
# 1. Clone and configure
git clone <repository-url>
cd enterprise-cia
cp .env.example .env
# Edit .env and add YOU_API_KEY

# 2. Start infrastructure
docker-compose up postgres redis -d

# 3. Backend setup
pip install -r requirements.txt
cd backend
alembic upgrade head
uvicorn app.main:app --reload --port 8765

# 4. Frontend setup (new terminal)
npm install
npm run dev  # Runs on port 3456
```

### Development Workflow

**Adding a New API Endpoint**:
1. Create route in `backend/app/api/your_feature.py`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Add database models in `backend/app/models/` (if needed)
4. Register router in `backend/app/main.py`
5. Create migration: `alembic revision --autogenerate -m "add your feature"`
6. Add frontend API call using React Query

**Modifying You.com API Usage**:
- All changes through `backend/app/services/you_client.py`
- Maintain orchestration pattern: News → Search → Chat → ARI
- Use circuit breakers for resilience
- Implement proper caching

**Adding a Frontend Component**:
1. Create in `components/YourComponent.tsx`
2. Use `"use client"` directive for hooks
3. Follow React Query patterns for data fetching
4. Use Tailwind CSS for styling

### Python Backend Conventions

**Async Everywhere**:
```python
@router.post("/generate", response_model=ImpactCardResponse)
async def generate_impact_card(
    data: ImpactCardRequest,
    db: AsyncSession = Depends(get_db),
    you_client: YouComOrchestrator = Depends(get_you_client)
):
    result = await you_client.generate_impact_card(data.competitor)
    return result
```

**Type Hints Required**: All functions must have type annotations

**Error Handling**:
- Raise `HTTPException` for API errors
- Use `YouComAPIError` for You.com API failures (includes `api_type`)
- Circuit breakers handle retries automatically
- Structured error logging with context

### TypeScript Frontend Conventions

**Client Components**:
```typescript
"use client"  // Required for components using hooks

export function Component() {
  const { data, isLoading } = useQuery({
    queryKey: ['impact-cards'],
    queryFn: () => api.get('/api/v1/impact/').then(res => res.data)
  })

  return <div>{/* ... */}</div>
}
```

**Error Boundaries**:
```typescript
import { ErrorBoundary } from '@/components/ErrorBoundary'

<ErrorBoundary context="API Dashboard">
  <APIUsageDashboard />
</ErrorBoundary>
```

---

## Component Documentation

### Backend Services

#### YouComOrchestrator (`backend/app/services/you_client.py`)
**Purpose**: Core service coordinating all 4 You.com APIs

**Key Methods**:
- `fetch_news(query, limit)`: News API integration
- `search_context(query, limit)`: Search API integration
- `analyze_impact(news, context, competitor)`: Chat API (Custom Agents)
- `generate_research_report(query)`: ARI API integration
- `generate_impact_card(competitor)`: Full orchestration workflow

**Error Handling**:
- `YouComAPIError` exception with `api_type` parameter
- Type-safe citation handling (dict vs string formats)
- Runtime validation for data structures
- Comprehensive error logging

#### ResilientYouComOrchestrator (`backend/app/services/resilient_you_client.py`)
**Purpose**: Circuit breakers and resilience patterns

**Features**:
- Per-API circuit breakers
- Exponential backoff
- Rate limiting
- Health status monitoring

### Frontend Components

#### ImpactCardDisplay (`components/ImpactCardDisplay.tsx`)
**Purpose**: 4-tab interface for Impact Cards

**Tabs**:
1. **Overview**: Risk score, impact areas, confidence metrics
2. **Analysis**: Strategic insights and recommendations
3. **Timeline**: Change detection and evidence
4. **Citations**: 400+ source references

#### WatchList (`components/WatchList.tsx`)
**Purpose**: Competitor monitoring interface

**Features**:
- Add/remove competitors
- Keyword monitoring
- Real-time alerts
- Impact Card generation

#### CompanyResearch (`components/CompanyResearch.tsx`)
**Purpose**: Individual company research interface

**Features**:
- Instant company profiles
- 400+ source research
- Export to PDF
- Email sharing

#### APIUsageDashboard (`components/APIUsageDashboard.tsx`)
**Purpose**: API metrics and usage tracking

**Displays**:
- API call counts by type
- Cost estimates
- Response times
- Error rates

#### ErrorBoundary (`components/ErrorBoundary.tsx`)
**Purpose**: React error boundary for graceful error handling

**Features**:
- Catches JavaScript errors in component tree
- User-friendly error UI
- Error recovery actions
- Development stack traces

---

## Testing & Quality

### Backend Testing

**Test Suite** (`backend/tests/`):
```bash
# Run all tests
cd backend
pytest tests/ -v

# Run specific test file
pytest tests/test_you_client.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

**Test Categories**:
- Integration tests: You.com API orchestration
- Error handling: Enhanced error context
- Type safety: Citation format handling
- Resilience: Circuit breaker functionality

**Key Test Files**:
- `test_you_client.py`: You.com integration tests
- `test_error_handling_integration.py`: Error handling tests
- `test_resilience.py`: Circuit breaker tests

### Frontend Testing

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

**Test Location**: `components/__tests__/`

### Code Quality

**Backend**:
```bash
# Linting (recommended)
flake8 backend/app/

# Type checking
mypy backend/app/
```

**Frontend**:
```bash
# Linting
npm run lint

# Build verification
npm run build
```

---

## Deployment

### Environment Configuration

**Required Environment Variables**:
```bash
# You.com API (REQUIRED)
YOU_API_KEY=your_you_api_key_here

# Database (matches docker-compose ports)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/cia_hackathon
REDIS_URL=redis://localhost:6380

# Security
SECRET_KEY=your-secret-key-here  # Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Environment
ENVIRONMENT=production  # or development
```

**Optional Variables**:
```bash
# API Base URLs (defaults work for most users)
YOU_SEARCH_BASE_URL=https://api.ydc-index.io
YOU_AGENT_BASE_URL=https://api.you.com/v1

# Email (for sharing features)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Integrations (optional)
# Notion, Salesforce, Slack credentials...
```

**See**: `.env.example` for complete reference

### Database Migrations

```bash
cd backend

# Run all migrations
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

**Migration Files**: `backend/alembic/versions/` (7 total)

### Production Deployment

**Backend**:
- Python environment with Postgres and Redis
- Run migrations: `alembic upgrade head`
- Start server: `uvicorn app.main:app --host 0.0.0.0 --port 8765`

**Frontend**:
- Deploy to Vercel (Next.js optimized)
- Configure `NEXT_PUBLIC_API_URL` to production backend

**Infrastructure**:
- PostgreSQL 15+
- Redis 7+
- Ensure all environment variables configured

---

## Additional Resources

### External Documentation
- [You.com API Documentation](https://documentation.you.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Next.js Documentation](https://nextjs.org/docs)

### Project Files
- [README.md](README.md): Project overview and quick start
- [CLAUDE.md](CLAUDE.md): Developer guide for Claude Code
- [.env.example](.env.example): Environment configuration reference
- [CLEANUP_COMPLETE.md](CLEANUP_COMPLETE.md): Documentation cleanup summary

### Code Quality Improvements (2025)
- Enhanced error handling with `api_type` context
- Type-safe citation processing
- React Error Boundary implementation
- Environment-configurable API endpoints
- Comprehensive integration test coverage

---

## Quick Reference Card

### Port Configuration
- **Frontend**: http://localhost:3456
- **Backend API**: http://localhost:8765
- **API Docs**: http://localhost:8765/docs (FastAPI auto-generated)
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6380

### Common Commands

```bash
# Backend
cd backend
alembic upgrade head                # Run migrations
uvicorn app.main:app --reload       # Start dev server
pytest tests/ -v                    # Run tests

# Frontend
npm run dev                         # Start dev server
npm test                            # Run tests
npm run lint                        # Lint code
npm run build                       # Production build

# Infrastructure
docker-compose up postgres redis -d # Start services
docker-compose down                 # Stop services
```

### Key Files to Understand

For new developers, read these files first:

1. `backend/app/services/you_client.py` - Core You.com orchestration
2. `backend/app/main.py` - FastAPI app setup
3. `backend/app/api/impact.py` - Impact Card generation
4. `components/ImpactCardDisplay.tsx` - Main UI component
5. `lib/api.ts` - Frontend API client
6. `.env.example` - Configuration options

---

**🎯 Built for You.com Hackathon - Showcasing the power of orchestrated API integration**
