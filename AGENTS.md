## Learned User Preferences

- Prefer terse, concrete rewrites and explanations over high-level guidance.
- Prefer direct execution over discussion: make the file change first, keep chat minimal.
- When editing authored docs or curriculum files, preserve existing content and append new build notes instead of replacing prior text.
- Commit messages: conventional `type(scope):` subject is fine; keep subject and optional body terse—avoid long, chatty, bot-like changelog bullets. Prefer concrete verbs (add/fix/wire/guard/validate/…); avoid filler like _enhance_, _introduce_, _leverage_, _streamline_—say what actually changed.
- Prefer output that drives actionable product decisions, not infrastructure-heavy info dumps.
- Prefer grading that rewards architectural intent, tradeoff reasoning, and flow clarity over exact file-tree recitation unless strict scaffold fidelity is explicitly requested.
- Prefer minimal repetitive chat; consolidate guidance into updated files to avoid repeated token-heavy explanations.
- No trailing summaries of what you just did — the user can read the diff.
- Apply your own standards to your own output: if you dock the student for something, don't do it in your tightened/ideal version. The student catches inconsistency immediately.
- When grading hypothetical scenarios (e.g., "explain to a client"), don't dock for referencing future product surfaces — that's natural in a pitch context.
- Prefers TDD workflow for backend builds ("TDD mindset" — RED/GREEN/REFACTOR cycles).
- Prefers TanStack Query v5 patterns that keep UI lean: e.g. drive invalidation from the query path (`queryFn` after a terminal successful read) instead of extra React `useEffect` wired to query data when avoiding effect churn.

## Runtime Requirements

- Redis required for Celery (uploads, classification, embedding). Without it, file uploads 500.
- Backend `.env` must have `DATABASE_URL` — settings.py loads it via `python-dotenv`. Without it, Django falls back to local Postgres creds and fails.
- Frontend `.env.local` must have `VITE_TENANT_ID` — the API client sends it as `X-Tenant-ID` header. Must be a valid UUID of an existing tenant.
- Session auth: user must log in at `/admin/` to get a session cookie before the frontend can POST (CSRF + auth).
- Vite proxy handles `/api` → `localhost:8000` in dev, so frontend and backend don't need CORS negotiation locally.

## Learned Workspace Facts

- In `/colearn/milestone-*.md`, new build notes should follow the existing pattern by appending beneath the original section content.
- `scope.md` defines the scope of whats being built.
- the user is learning while building using the `/colearn` subfolder
- `colearn/grading-criteria.md` should remain generic (milestone-agnostic) while still defining scaffold-question grading behavior.
- `colearn/tutor-prompt.txt` is the full tutor/grader system prompt for new Claude instances picking up this project.
- Grading results and build notes are expected to be written in the current milestone workbook file, not only in chat.
- Backend Postgres is Neon-first via `DATABASE_URL` and `dj-database-url`; local Docker Compose usually runs Redis (and the app) without a bundled Postgres container.
- Neon-style `DATABASE_URL` examples should include `sslmode=require` and `channel_binding=require` in the query string when the stack expects them.
- M1 is complete (Steps 1.1-1.5). Deferred items: Source.config overloaded, no mid-task progress, serializer leaks config, temp file local-only, no Postgres RLS.
- M2.5 built: tenant-wide theme discovery (`themes/discovery.py`: sklearn HDBSCAN + LLM summarize + cosine merge; writes `Theme.slug` onto `FeedbackItem.themes` for `?theme=` filtering); `process_source` chains classify → embed → `discover_themes_for_source`; `GET/POST api/themes/` + Themes UI; Explorer theme filter + URL-driven filters; `python manage.py reset_app_data` keeps tenants only. Theme list live `item_count` aligns to explorer by scanning `FeedbackItem.themes` per slug (not a `themes__contains=[OuterRef]` subquery—SQLite limits + psycopg3 JSON bind issues on Postgres). 35 backend tests total.
- M3.1 built: Correction apply (`POST /api/analysis/corrections/` writes `human_value` to `FeedbackItem` atomically via `transaction.atomic()` + `.update()`); shape validation per `field_corrected`; `trends/engine.py` rewritten to read AI originals from `Correction.ai_value` for corrected fields (earliest correction = true AI prediction); `trends/tasks.py` with `compute_daily_snapshots()` beat task (runs 4am daily); `GET /api/trends/snapshots/?start=&end=` API endpoint with tenant-scoped date filtering. 49 backend tests total.
- `scikit-learn>=1.6.0` is a backend dependency (provides `sklearn.cluster.HDBSCAN` for theme clustering).
- Git repo was moved from `backend/` (where `uv init` created it) to the project root `feedback-intelligence/`.

## Build Notes Format (Persistent)

- For milestone workbook build logs, use this exact heading pattern:
  - `### <step> Build Notes — What was built + what to study`
- Always include these sections in order:
  - `**What the build did:**` (numbered list, concrete implementation artifacts)
  - `**Design decisions to know for interviews:**` (short bullets, tradeoff-focused)
  - `**Files to study:**` (markdown table with `File:Lines` and `What to know`)
- `Files to study` must use precise `path:line-line` references where possible (not generic file names only).
- Prefer clickable markdown links with line anchors for navigation (e.g. ``[`path:1-10`](path#L1-L10)``).
- Keep build notes concrete and code-referential; avoid generic or high-level process commentary.
- Do not add/modify grading content unless explicitly requested; default to appending build notes only.
