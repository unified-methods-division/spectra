# Feedback Intelligence Platform

Open-source tool for turning user feedback from multiple channels into prioritized product decisions. Ingests feedback via CSV/JSONL upload or webhook, classifies it with AI (sentiment, themes, urgency), generates embeddings for semantic search, and surfaces trends and recommendations.

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

### Frontend

```bash
cd frontend
bun install

# Create .env.local with your tenant ID (from the shell command above)
echo "VITE_TENANT_ID=your-tenant-uuid-here" > .env.local

bun dev
```

### First run

1. Start Redis, backend, Celery worker, and frontend
2. Log in at http://localhost:8000/admin/ (creates session cookie)
3. Open http://localhost:5173/sources
4. Add a source, upload a CSV, watch it process

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
