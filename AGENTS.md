# Repository Guidelines

## MVP vs Enterprise Feature Roadmap

### MVP (Current Version) - Individual User Focus

The MVP targets **individual users** (job seekers, investors, entrepreneurs, researchers, consultants) with core competitive intelligence features:

- ✅ **Core You.com API Integration**: All 4 APIs (News, Search, Chat, ARI) working together
- ✅ **Individual Company Research**: Quick company profiles and market analysis
- ✅ **Basic Competitive Monitoring**: Simple watchlists and impact analysis
- ✅ **Export & Sharing**: PDF reports and shareable insights
- ✅ **Real-time Processing**: WebSocket updates during analysis
- ✅ **API Usage Dashboard**: Transparent You.com API metrics
- ✅ **Action Planning**: Ranked next steps with owners, OKR linkage, and evidence capture
- ✅ **Credibility Controls**: Source tiering, review flags, and comparison analytics

### Enterprise Features (Next Version)

Enterprise-specific features are planned for post-MVP development:

- 🔄 **Team Collaboration**: Multi-user workspaces and shared watchlists
- 🔄 **Advanced Compliance**: SOC 2, GDPR, audit trails, immutable logs
- 🔄 **RBAC & Security**: Role-based access control (viewer/analyst/admin)
- 🔄 **Enterprise Integrations**: Slack, Notion, Salesforce connectors
- 🔄 **Advanced Analytics**: Custom dashboards and reporting
- 🔄 **White-label Solutions**: Branded deployments for enterprise clients

## Project Structure & Module Organization

- **Frontend**: Next.js app lives in `app/`, shared UI in `components/`, utility hooks and API clients in `lib/`. Static styles stay in `app/globals.css`.
- **Backend**: FastAPI service under `backend/app/` with routers in `api/`, persistence in `models/` + `database.py`, services orchestrating You.com calls, and `schemas/` for Pydantic shapes.
- **Common Assets**: `scripts/` hosts demo/setup helpers (e.g., `seed_demo_data.py`), `Research/` and `claudedocs/` capture supporting docs, and `docker-compose.yml` manages local Postgres/Redis.
- **Tests**: Backend coverage in `backend/tests/`; UI behavior specs in `components/__tests__/`.
- **Telemetry**: API call analytics persist via `backend/app/models/api_call_log.py` and power the `/api/v1/metrics/api-usage` endpoint.

## Build, Test, and Development Commands

- `npm run dev`: Start the Next.js frontend on `http://localhost:3456`.
- `npm run build` / `npm run start`: Production build and serve.
- `npm run lint` / `npm run test`: ESLint and Jest suites for UI.
- `pip install -r requirements.txt`: FastAPI dependencies.
- `uvicorn app.main:app --reload`: Launch backend locally (run inside `backend/`).
- `pytest backend/tests -v`: Backend unit + integration tests. Use `./run_tests.sh` for the full coverage workflow and HTML report.
- `python scripts/seed_demo_data.py`: Hydrates the database with real You.com data (requires `YOU_API_KEY`).

## MVP Development Guidelines

**Important**: This project follows an MVP-first approach targeting individual users. See [MVP_ROADMAP.md](MVP_ROADMAP.md) for complete feature separation between MVP and enterprise versions.

### MVP Feature Development

- Focus on individual user workflows (company research, basic competitive monitoring)
- Prioritize You.com API integration and core functionality
- Avoid enterprise-specific features (team collaboration, advanced compliance, RBAC)
- Keep UI simple and focused on individual productivity

## Coding Style & Naming Conventions

- **TypeScript**: Keep modules typed; prefer `camelCase` for variables/hooks, `PascalCase` for components, and colocate UI logic with Tailwind utility classes. Run `npm run lint -- --fix` before committing.
- **Python**: Follow PEP 8; use `snake_case` for functions and `PascalCase` for SQLAlchemy models/Pydantic schemas. Organize endpoints under `api/` by feature and isolate service logic in `services/`.
- **Config**: Store secrets in `.env`; never commit keys referenced in README examples.

## Testing Guidelines

- Align backend tests with feature folders (e.g., `test_api_endpoints.py` mirrors `api/` routes) and mark async cases with `pytest.mark.asyncio`.
- Place React tests in `components/__tests__/ComponentName.test.tsx` using Testing Library patterns and socket mocks.
- Target ≥90% coverage when running `./run_tests.sh`; triage gaps using `htmlcov/index.html`.

## Commit & Pull Request Guidelines

- Git history is unavailable here; use short, imperative subjects (e.g., `feat: add impact card gauges`) and add scopes where helpful.
- Reference related issues, list API/env impacts, and attach UI screenshots or CLI logs for behavior changes.
- Summarize validation steps (`npm run test`, `pytest`) and call out manual setup required for reviewers.

## Security & Configuration Tips

- Copy `.env.example` to configure `YOU_API_KEY`, Postgres, and Redis URLs before running services.
- Rotate credentials prior to public demos and keep Postgres/Redis containers within the networks defined in `docker-compose.yml`.
