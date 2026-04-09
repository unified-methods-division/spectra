Read and follow these files before starting work:

1. `AGENTS.md` — learned preferences, workspace facts, build notes format
2. `colearn/tutor-prompt.txt` — tutor/grader behavior when working on curriculum
3. `colearn/grading-criteria.md` — grading rules (treat as law)

## Running the project

### Prerequisites
- Python 3.12 (managed by `uv`)
- Node/Bun (frontend)
- Redis (Celery broker + result backend)
- PostgreSQL via Neon (remote) — no local Postgres needed

### Backend (`backend/`)
- Environment: `backend/.env` must contain `DATABASE_URL` (Neon connection string). Settings auto-load it via `python-dotenv`.
- Start server: `uv run python manage.py runserver`
- Start Celery worker: `uv run celery -A config worker -l info`
- Redis must be running (`sudo service redis-server start`) before Celery or uploads will fail.
- Tests use SQLite by default (`DJANGO_TEST_USE_SQLITE=1`), no Neon/Redis needed: `uv run python manage.py test`

### Frontend (`frontend/`)
- `frontend/.env.local` must contain `VITE_TENANT_ID` (UUID of a tenant in the DB).
- Vite dev proxy forwards `/api` → `localhost:8000` — no CORS issues in dev.
- Auth: log in at `http://localhost:8000/admin/` first to get a session cookie.
- Start dev server: `cd frontend && bun dev`
- Typecheck: `bun run typecheck`
