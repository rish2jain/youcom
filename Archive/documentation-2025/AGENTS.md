# Repository Guidelines

This guide orients contributors working on the MVP-focused You.com intelligence
platform.

## Project Structure & Module Organization

- `app/` hosts Next.js routes; shared components live in `components/`, while
  hooks and API clients live in `lib/`.
- `app/globals.css` keeps Tailwind baseline styles; prefer component-scoped
  utility classes for new styling.
- `backend/app/` contains FastAPI code with routers in `api/`, models in
  `models/`, orchestration logic in `services/`, schemas in `schemas/`, and
  persistence helpers in `database.py`.
- Utility scripts and data seeds live under `scripts/`; historical docs are in
  `Archive/`.
- Tests mirror runtime code: React specs in `components/__tests__/`, backend
  suites in `backend/tests/`.

## Build, Test, and Development Commands

- `npm run dev` launches the frontend at `http://localhost:3456`; `npm run build`
  compiles the production bundle; `npm run start` serves it locally.
- `pip install -r requirements.txt` installs API dependencies; from `backend/`
  run `uvicorn app.main:app --reload` to start the FastAPI server.
- `npm run lint` executes ESLint; `npm run test` runs Jest; `pytest
  backend/tests -v` covers the backend suites.
- `./run_tests.sh` orchestrates full-stack checks and writes coverage output to
  `htmlcov/index.html`.

## Coding Style & Naming Conventions

- TypeScript stays strongly typed with `camelCase` functions/hooks and
  `PascalCase` components.
- Python follows PEP 8: `snake_case` functions, `PascalCase` SQLAlchemy models
  and Pydantic schemas.
- Keep Tailwind utilities close to their JSX; avoid expanding global CSS beyond
  `app/globals.css`.
- Run `npm run lint -- --fix` before review and commit formatted code only.

## Testing Guidelines

- Name React tests `components/__tests__/ComponentName.test.tsx` and rely on
  Testing Library patterns, mocking sockets when required.
- Backend tests should mirror routers or services and mark async cases with
  `pytest.mark.asyncio`.
- Maintain ≥90% coverage via `./run_tests.sh`; inspect gaps through
  `htmlcov/index.html`.

## Commit & Pull Request Guidelines

- Use short, imperative commit subjects (e.g., `feat: add watchlist badges`)
  with optional scopes for clarity.
- PR descriptions should outline scope, link issues, note API/env impacts, and
  include UI screenshots or CLI logs where behavior changes.
- List validation steps run locally (`npm run test`, `pytest`) and flag any
  manual setup requirements.

## Security & Configuration Tips

- Copy `.env.example`, populate `YOU_API_KEY`, Postgres, and Redis secrets, and
  rotate credentials before demos.
- Use the `docker-compose.yml` networks to isolate Postgres and Redis, and
  never commit secrets or generated credentials.
