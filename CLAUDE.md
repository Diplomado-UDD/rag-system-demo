# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Educational RAG demo for UDD 2025 Diplomado. Full-stack: React frontend + FastAPI backend + PostgreSQL/pgvector. Responds in Chilean Spanish.

## Stack
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, uv
- **Frontend**: React 18, Vite, Tailwind CSS
- **Database**: PostgreSQL 16 + pgvector (port 5433 local, 5432 in Docker)
- **AI**: OpenRouter proxy → `text-embedding-3-small` + `gpt-4-turbo-preview`
- **Linting**: Ruff (`line-length=100`, `target-version="py312"`)

## Commands

```bash
uv sync                                              # Install deps
uv run uvicorn src.main:app --reload                 # Dev server (port 8000)
docker-compose up -d                                 # Full stack (DB:5433, API:8000, UI:80)
uv run alembic upgrade head                          # Run migrations

uv run pytest                                        # All tests
uv run pytest tests/unit/                            # Unit tests only
uv run pytest tests/unit/test_services/test_rag_service.py -v  # Single test file
uv run pytest --cov=src                              # With coverage

uv run ruff check src/                               # Lint
uv run ruff format src/                              # Format
```

## Environment

Copy `.env.example` to `.env`. Required vars: `DATABASE_URL`, `OPENROUTER_API_KEY`.

## Architecture

```
src/
  main.py               # App entry point, router registration, middleware
  core/
    config.py           # Settings via pydantic-settings (lru_cache)
    prompts.py          # RAG prompt templates
  api/
    routes/             # documents.py, query.py, health.py
    dependencies.py     # FastAPI DI: wires repos + services
    middleware.py       # CORS, logging, error handling
    schemas.py          # API-level Pydantic schemas
  services/             # Business logic (pdf, chunking, embedding, retrieval, llm, rag)
  repositories/         # Async data access: document_repo, vector_repo, query_log_repo
  models/               # SQLAlchemy ORM: Document, Chunk, QueryLog
  schemas/              # Pydantic request/response schemas
  utils/                # exceptions.py, validators.py, text_processing.py
```

### Key design notes

- All DB/API I/O is async except `EmbeddingService` and `LLMService`, which use the synchronous `openai.OpenAI` client (OpenRouter-compatible).
- Both AI services receive `api_key` + `base_url` from `Settings` — the OpenAI SDK is used as an OpenRouter proxy.
- `dependencies.py` is the composition root: repos take `AsyncSession`, services are injected via `Depends`.
- `get_settings()` is `lru_cache`'d — reset in tests with `get_settings.cache_clear()`.
- RAG flow: PDF upload → chunk → embed (batch) → store vectors → query → retrieve top-k → LLM prompt → answer.
