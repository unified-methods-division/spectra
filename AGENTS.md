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
- M1 is complete (Steps 1.1-1.5). Deferred items: Source.config overloaded, no mid-task progress, serializer leaks config, temp file local-only, no Postgres RLS, no upload traceability (`UploadBatch` model — see `scope.md`).
- M2.5 built: tenant-wide theme discovery (`themes/discovery.py`: sklearn HDBSCAN + LLM summarize + cosine merge; writes `Theme.slug` onto `FeedbackItem.themes` for `?theme=` filtering); `process_source` chains classify → embed → `discover_themes_for_source`; `GET/POST api/themes/` + Themes UI; Explorer theme filter + URL-driven filters; `python manage.py reset_app_data` keeps tenants only. Theme list live `item_count` aligns to explorer by scanning `FeedbackItem.themes` per slug (not a `themes__contains=[OuterRef]` subquery—SQLite limits + psycopg3 JSON bind issues on Postgres). 35 backend tests total.
- M3.1 built: Correction apply (`POST /api/analysis/corrections/` writes `human_value` to `FeedbackItem` atomically via `transaction.atomic()` + `.update()`); shape validation per `field_corrected`; `trends/engine.py` rewritten to read AI originals from `Correction.ai_value` for corrected fields (earliest correction = true AI prediction); `trends/tasks.py` with `compute_daily_snapshots()` beat task (runs 4am daily); `GET /api/trends/snapshots/?start=&end=` API endpoint with tenant-scoped date filtering. 49 backend tests total.
- M3 curriculum restructured: 3.1 accuracy -> 3.2 improvement loop -> 3.3 Weekly Outlook foundation + shared synthesis model -> 3.4 decision workflow + alerts + drilldown -> 3.5 eval harness. Old steps 3.5/3.6/3.7 merged or moved to optional extension.
- M3.5 (3.6) built: `GoldSetItem` model (unique tenant+item, stores gold labels independently from FeedbackItem); `analysis/eval.py` with `run_gold_eval()` (field accuracy + theme P/R via Correction.ai_value); regression gate in `assess_corrections()` blocks promotion if gold eval < previous accuracy, falls back to float comparison when no gold set; `CorrectionDisagreement` model with auto-detect on correction create; `analysis/disagreement.py` (detect, resolve via select_for_update, rate); `analysis/outcomes.py` (measure_recommendation_outcome baseline vs 14-day, compute_drift_delta via ISO week bucketing); API: `eval/drift/`, `disagreements/`, `disagreements/rate/`, `disagreements/{id}/resolve/`, `recommendations/{id}/outcome/`, `gold-set/`, `eval/gold/`; frontend eval components + dashboard panels + interactive disagreement resolution + `/eval` page for gold set management. 81 backend tests, 57 frontend tests total.
- M3.5 review fixes: `run_gold_eval` dead `prompt_version_id` param removed; `RecommendationOutcome` has `UniqueConstraint(fields=[recommendation, metric_name, measured_at])` and `measure_recommendation_outcome` uses `transaction.atomic` + `select_for_update`; naive datetime warnings fixed in improvement.py; `useResolveDisagreement` invalidates both disagreements and disagreement-rate queries; gold-set CRUD API + serializer with cross-tenant FK validation added.
- `scikit-learn>=1.6.0` is a backend dependency (provides `sklearn.cluster.HDBSCAN` for theme clustering).
- Git repo was moved from `backend/` (where `uv init` created it) to the project root `feedback-intelligence/`.
- `frontend/` uses Bun (not pnpm): add packages with the Bun CLI instead of hand-editing `package.json` dependency entries; keep Tailwind usage aligned with Tailwind CSS v4 syntax in components.

## Build Notes Format (Persistent)

- For milestone workbook build logs, use this exact heading pattern:
  - `### <step> Build Notes — What was built + what to study`
- Always include these sections in order:
  - `**What the build did:**` (numbered list, concrete implementation artifacts)
  - `**Design decisions to know for interviews:**` (short bullets, tradeoff-focused)
  - `**Files to study:**` (markdown table with `File:Lines` and `What to know`)
- `Files to study` must use precise `path:line-line` references where possible (not generic file names only).
- Prefer clickable markdown links with line anchors for navigation: `` [`path:line-line`](../../rel/path#Lline-Lline) ``. The link path is **relative from the workbook file** (in `colearn/workbooks/`) to the target — use `../../` prefix. The anchor uses GitHub-style `#Lline-Lline` format on the bare path (no `../../` in the anchor href, just the relative path portion). Example: `` [`analysis/eval.py:17-79`](../../backend/analysis/eval.py#L17-L79) ``.
- Keep build notes concrete and code-referential; avoid generic or high-level process commentary.
- Do not add/modify grading content unless explicitly requested; default to appending build notes only.
