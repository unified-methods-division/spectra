-- Ensures pgvector extension is available before Django migrations run.
-- Idempotent: CREATE EXTENSION ... IF NOT EXISTS is safe to re-run.
CREATE EXTENSION IF NOT EXISTS vector;