# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Enterprise CIA is a competitive intelligence automation platform built for the You.com Hackathon. It orchestrates **all 4 You.com APIs** (News, Search, Chat with Custom Agents, and ARI) to transform information overload into actionable insights for both individual researchers and enterprise teams.

### Technology Stack

**Backend:**
- Python 3.11+ with FastAPI (async)
- PostgreSQL 15+ with SQLAlchemy (async ORM)
- Redis 7+ for caching and real-time features
- Socket.IO for WebSocket communication
- Alembic for database migrations

**Frontend:**
- Next.js 14 (App Router) with TypeScript
- React 18 with Tailwind CSS
- Zustand + React Query (TanStack Query) for state management
- Recharts for data visualization
- Socket.io-client for real-time updates

### Key Architecture Patterns

**You.com API Orchestration:**
The core of the application is `backend/app/services/you_client.py` (`YouComOrchestrator` class), which coordinates all 4 You.com APIs in a sequential workflow:
1. News API → detects recent competitor activity
2. Search API → enriches context with market data
3. Chat API (Custom Agents) → analyzes competitive impact
4. ARI API → synthesizes 400+ source reports

This orchestration pattern is used throughout the codebase for generating Impact Cards and Company Research.

**Async/Await Everywhere:**
All I/O operations in the backend use async/await patterns. Database queries, API calls, and Redis operations are all asynchronous. FastAPI endpoints use `async def` and dependencies like `AsyncSession = Depends(get_db)`.

**Real-time Progress Updates:**
WebSocket connections (via Socket.IO) provide live progress updates during API orchestration. The backend emits events at each step, and the frontend displays them in real-time.

## Essential Commands

### Development Setup

```bash
# Environment setup
cp .env.example .env
# Edit .env and add YOUR YOU_API_KEY (required)

# Start infrastructure services
docker-compose up postgres redis -d

# Backend setup and start
pip install -r requirements.txt
cd backend
alembic upgrade head
uvicorn app.main:app --reload --port 8765

# Frontend setup and start (in separate terminal)
npm install
npm run dev  # Runs on port 3456
```

### Database Operations

```bash
# Run all migrations
cd backend
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1

# Seed demo data (requires YOU_API_KEY in .env)
python ../scripts/seed_demo_data.py
```

### Testing

```bash
# Backend tests
cd backend
pytest tests/ -v                          # Run all tests
pytest tests/test_you_client.py -v        # Test You.com integration
pytest tests/ --cov=app --cov-report=html # With coverage

# Frontend tests
npm test                    # Run all tests
npm run test:watch         # Watch mode
npm run test:coverage      # With coverage report
```

### Build & Lint

```bash
# Frontend
npm run build              # Production build
npm run lint               # ESLint check
npm start                  # Start production server

# Backend (Python linting not in package.json but recommended)
flake8 backend/app/        # Code style check (if installed)
```

## Architecture & Code Organization

### Backend Structure (`backend/app/`)

**Core Services:**
- `services/you_client.py` - **CRITICAL**: YouComOrchestrator class that coordinates all 4 You.com APIs
- `services/hubspot_sync_service.py` - HubSpot CRM integration
- `services/performance_monitor.py` - Circuit breakers and resilience patterns

**API Endpoints (`api/`):**
- `impact.py` - Impact Card generation (uses all 4 You.com APIs)
- `research.py` - Company research endpoint
- `watch.py` - Competitor watchlist management
- `integrations.py` - Third-party integrations (Notion, Salesforce, Slack)
- `analytics.py` - Predictive analytics and trends
- All routers are registered in `main.py`

**Database (`models/` and `schemas/`):**
- `models/` - SQLAlchemy ORM models (async)
- `schemas/` - Pydantic validation schemas for API requests/responses
- Database migrations in `alembic/versions/`

**Configuration:**
- `config.py` - Settings loaded from environment variables
- `database.py` - Async database session management
- `resilience_config.py` - Circuit breaker and retry configurations

### Frontend Structure

**Pages (`app/`):**
- `page.tsx` - Main application dashboard
- `layout.tsx` - Root layout with providers
- Uses Next.js 14 App Router (not Pages Router)

**Components (`components/`):**
- `WatchList.tsx` - Competitor monitoring interface
- `CompanyResearch.tsx` - Individual company research
- `ImpactCardDisplay.tsx` - 4-tab interface for Impact Cards
- `APIUsageDashboard.tsx` - API metrics and usage tracking
- Components use React Query for data fetching and Zustand for local state

**API Client (`lib/`):**
- `api.ts` - Axios instance with interceptors, configured for http://localhost:8765
- `socket.ts` - Socket.IO client for real-time updates

## Important Development Patterns

### Python Backend Conventions

**Async Everywhere:**
```python
# All endpoints are async
@router.post("/generate", response_model=ImpactCardResponse)
async def generate_impact_card(
    data: ImpactCardRequest,
    db: AsyncSession = Depends(get_db),
    you_client: YouComOrchestrator = Depends(get_you_client)
):
    result = await you_client.generate_impact_card(data.competitor)
    return result
```

**Type Hints Required:**
All function signatures must include type hints. Use Pydantic models for request/response schemas.

**Error Handling:**
- Raise `HTTPException` for API errors
- Use custom `YouComAPIError` for You.com API failures
- Circuit breakers automatically handle retries (see `resilience_config.py`)

### TypeScript Frontend Conventions

**Client Components:**
All components using hooks must have `"use client"` directive at the top.

**React Query Pattern:**
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['impact-cards'],
  queryFn: () => api.get('/api/v1/impact/').then(res => res.data),
});
```

**Real-time Updates:**
Components subscribe to Socket.IO events for progress updates during API orchestration.

## Environment Configuration

**Required Environment Variables:**
- `YOU_API_KEY` - **REQUIRED** - Get from https://api.you.com
- `DATABASE_URL` - Postgres connection string (matches docker-compose ports)
- `REDIS_URL` - Redis connection string

**Optional but Recommended:**
- `DEMO_MODE=false` - Set to `true` to use mock data instead of real API calls
- SMTP settings for email sharing functionality
- Integration API keys for Notion, Salesforce, Slack (optional features)

See `.env.example` for complete configuration reference.

## Database Schema Notes

The database uses **async SQLAlchemy** with 7 migration files tracking the evolution:
- `001_initial_migration.py` - Core tables (users, workspaces, watch items, impact cards)
- `002_enterprise_features.py` - Enterprise features (teams, integrations, compliance)
- `003_advanced_features.py` - Advanced intelligence features
- `004_add_enhancement_features.py` - Enhancements and optimizations
- `005_add_ml_training_models.py` - ML training infrastructure
- `006_add_model_registry.py` - Model versioning and registry
- `007_add_industry_templates.py` - Industry-specific templates

Always run migrations before starting development: `alembic upgrade head`

## You.com API Integration Details

**API Endpoints Used:**
- News API: `/news` endpoint for real-time competitor monitoring
- Search API: `/search` endpoint for context enrichment
- Chat API: `/chat` endpoint with custom agent for strategic analysis
- ARI API: `/research` endpoint for deep 400+ source synthesis

**Rate Limiting & Caching:**
- Redis caching: 15min (news), 1hr (search), 7days (ARI)
- Circuit breakers prevent API overload
- Exponential backoff on failures

**Demo Mode:**
Set `DEMO_MODE=true` in `.env` to use mock responses instead of live API calls (useful for development without API key).

## Port Configuration

- **Frontend**: http://localhost:3456
- **Backend API**: http://localhost:8765
- **API Docs**: http://localhost:8765/docs (FastAPI auto-generated)
- **PostgreSQL**: localhost:5433 (mapped from container's 5432)
- **Redis**: localhost:6380 (mapped from container's 6379)

Note: Docker services use internal ports (5432, 6379) while host machine uses 5433 and 6380 to avoid conflicts.

## Testing Before Commits

Before committing changes:
1. Run tests: `pytest tests/` (backend) or `npm test` (frontend)
2. Check linting: `npm run lint` (frontend)
3. Verify API contracts haven't broken (if backend changes)
4. Test manually in browser if UI changes
5. Ensure migrations are created for model changes: `alembic revision --autogenerate`

## Key Files to Understand

For new developers, start by reading these files to understand the system:

1. `backend/app/services/you_client.py` - Core You.com API orchestration logic
2. `backend/app/main.py` - FastAPI app setup and router registration
3. `backend/app/api/impact.py` - Impact Card generation endpoint
4. `components/ImpactCardDisplay.tsx` - Main UI for displaying results
5. `lib/api.ts` - Frontend API client configuration
6. `.env.example` - All configuration options

## Common Development Tasks

**Adding a new API endpoint:**
1. Create route in `backend/app/api/your_feature.py`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Add database models in `backend/app/models/` (if needed)
4. Register router in `backend/app/main.py`
5. Create migration: `alembic revision --autogenerate -m "add your feature"`
6. Add frontend API call in relevant component using React Query

**Modifying You.com API usage:**
All changes should go through `backend/app/services/you_client.py` to maintain the orchestration pattern.

**Adding a frontend component:**
1. Create component in `components/YourComponent.tsx`
2. Use `"use client"` directive if using hooks
3. Follow existing patterns for React Query and Zustand
4. Use Tailwind CSS for styling (matches existing design system)

## Deployment Notes

The project is containerized with Docker Compose for local development. For production deployment:
- Frontend can be deployed to Vercel (Next.js optimized)
- Backend requires a Python environment with Postgres and Redis
- Ensure all environment variables are properly configured
- Database migrations must run before starting the backend: `alembic upgrade head`
