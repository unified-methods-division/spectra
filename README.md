# Spectra

Turn user feedback into product decisions. Ingest from CSV/JSONL or webhooks, classify with AI (sentiment, themes, urgency), embed for semantic search, and surface trends and recommendations.

## Stack

- **Backend:** Django 6, DRF, Celery, pydantic_ai
- **Frontend:** React 19, TypeScript, Vite, TanStack Query, Tailwind 4, shadcn
- **Database:** PostgreSQL (Neon) + pgvector
- **Queue:** Redis (Celery broker + result backend)
- **AI:** OpenAI (GPT-4.1 Nano for classification, text-embedding-3-small for embeddings)

## Setup

### Prerequisites

- Python 3.12+ ([uv](https://docs.astral.sh/uv/) for dependency management)
- [Bun](https://bun.sh/) (frontend package manager)
- Redis
- A PostgreSQL database (we use [Neon](https://neon.tech/))

### Git hooks (Conventional Commits)

Once per clone, point Git at this repo's hooks (validates subject line + a small banned-word list; see [`.githooks/commit-msg`](.githooks/commit-msg) and [`.cursor/rules/conventional-commits.mdc`](.cursor/rules/conventional-commits.mdc)):

```bash
git config core.hooksPath .githooks
```

To skip checks intentionally (e.g. emergency hotfix): `git commit --no-verify`.

### Backend

```bash
cd backend
uv sync

# Create .env with your database connection
cat > .env << 'EOF'
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname?sslmode=require
EOF

# Run migrations
uv run python manage.py migrate

# Create a superuser (needed for auth)
uv run python manage.py createsuperuser

# Create a tenant
uv run python manage.py shell -c "from core.models import Tenant; t = Tenant.objects.create(name='Dev'); print(f'Tenant ID: {t.id}')"

# Start the server
uv run python manage.py runserver
```

### Redis

```bash
# Ubuntu/WSL
sudo apt install -y redis-server
sudo service redis-server start

# Or Docker
docker run -d -p 6379:6379 redis:alpine
```

### Celery worker

```bash
cd backend
uv run celery -A config worker -l info
```

Required for file uploads, classification, and embedding tasks to actually run.

### Celery Beat

```bash
cd backend
uv run celery -A config beat -l info
```

Required for scheduled background jobs in `CELERY_BEAT_SCHEDULE` to enqueue automatically.
Current scheduled jobs:

- `themes.discover_themes_for_all_tenants` at `03:00`
- `trends.compute_daily_snapshots` at `04:00`

You do not need to keep your machine running until 3 or 4 AM to test these locally. Beat is for production-like scheduling; in development, trigger the tasks manually.

### Manually trigger scheduled tasks

Run them directly from Django shell:

```bash
cd backend
uv run python manage.py shell -c "from themes.tasks import discover_themes_for_all_tenants; discover_themes_for_all_tenants()"
uv run python manage.py shell -c "from trends.tasks import compute_daily_snapshots; compute_daily_snapshots()"
```

Or enqueue them through Celery to exercise Redis + worker too:

```bash
cd backend
uv run python manage.py shell -c "from themes.tasks import discover_themes_for_all_tenants; discover_themes_for_all_tenants.delay()"
uv run python manage.py shell -c "from trends.tasks import compute_daily_snapshots; compute_daily_snapshots.delay()"
```

### Run the full dev stack with tmuxp

If you want the whole app up in one shot without a homemade launcher, this repo includes a checked-in `.tmuxp.yaml` workspace.

Prereqs:

- `tmux`
- `tmuxp`

Example install:

```bash
# Ubuntu/WSL
sudo apt install -y tmux

# install tmuxp once
uv tool install tmuxp
```

Then from the project root:

```bash
tmuxp load ./
```

That opens separate tmux windows for:

- Redis status check
- Django backend
- Celery worker
- Celery beat
- Vite frontend

The Redis window only checks whether Redis is already running on `localhost:6379`; it does not start Redis for you. If Redis is down, start it with the commands above and reload the workspace.

### Frontend

```bash
cd frontend
bun install

# Create .env.local with your tenant ID (from the shell command above)
echo "VITE_TENANT_ID=your-tenant-uuid-here" > .env.local

bun dev
```

### Seed real Slack reviews

```bash
cd backend
uv run python manage.py seed_real_data --reset
```

Scrapes Google Play reviews for Slack, runs the full pipeline (classify, embed, discover themes, corrections, gold set, improvement loop, snapshots, report + alerts, recommendations + outcomes). Defaults to 200 reviews. Use `--fixture scripts/fixtures/slack_reviews.json` to skip scraping, `--dry-run` to preview, or `--app-id com.Discord` to target a different app.

### First run

1. `tmuxp load ./` (or start Redis, backend, worker, frontend manually)
2. `cd backend && uv run python manage.py seed_real_data --reset`
3. Log in at http://localhost:8000/admin/ (creates session cookie)
4. Open http://localhost:5173/sources

## Project structure

```
backend/
  config/          # Django settings, URLs, WSGI/ASGI
  core/            # Tenant model, middleware, base models
  ingestion/       # Sources, feedback items, CSV/webhook ingestion
  analysis/        # AI classification, embedding, processing pipeline
  themes/          # Theme taxonomy
  trends/          # Trend computation

frontend/
  src/
    components/    # UI components (sources table, dialogs, status badges)
    hooks/         # TanStack Query hooks
    lib/           # API client, query client, utilities
    pages/         # Page components
    types/         # TypeScript types matching backend API

colearn/           # Learning curriculum and workbooks (not part of the app)
```