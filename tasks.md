# RAG System MVP - Implementation Tasks

**Guidelines**: Complete one task at a time. Write tests first (TDD). Test after each task before proceeding.

---

## Phase 0: Project Setup & Infrastructure

### 0.1 Configure Python Environment
- [ ] Update `pyproject.toml` with project dependencies: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic-settings`, `python-dotenv`
- [ ] Update Python version requirement to `>=3.12` in `pyproject.toml`
- [ ] Run `uv sync` to install dependencies
- **Test**: Verify `uv run python --version` shows 3.12+

### 0.2 Create Project Directory Structure
- [ ] Create `src/` directory with `__init__.py`
- [ ] Create subdirectories: `src/api/`, `src/core/`, `src/models/`, `src/schemas/`, `src/services/`, `src/repositories/`, `src/utils/`
- [ ] Add `__init__.py` to each subdirectory
- **Test**: Run `find src -name "__init__.py"` and verify all exist

### 0.3 Configure Testing Framework
- [ ] Add test dependencies to `pyproject.toml`: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`
- [ ] Create `tests/` directory with `__init__.py`
- [ ] Create `tests/conftest.py` with basic pytest configuration
- [ ] Create subdirectories: `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- **Test**: Run `uv run pytest --collect-only` (should show 0 tests collected)

### 0.4 Setup Environment Configuration
- [ ] Create `.env.example` with placeholder values: `DATABASE_URL`, `OPENAI_API_KEY`, `EMBEDDING_MODEL`, `LLM_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K_RESULTS`, `MIN_SIMILARITY_THRESHOLD`, `MAX_FILE_SIZE_MB`
- [ ] Add `.env` to `.gitignore`
- [ ] Create `src/core/config.py` with `Settings` class using `pydantic-settings`
- **Test**: Write `tests/unit/test_config.py` to verify Settings loads from env vars

### 0.5 Setup Docker for PostgreSQL
- [ ] Create `docker-compose.yml` with `postgres` service using `pgvector/pgvector:pg16` image
- [ ] Configure environment variables, volumes, healthcheck, and port mapping
- [ ] Create `scripts/init_db.sh` to enable `vector` and `uuid-ossp` extensions
- **Test**: Run `docker-compose up -d` and `docker-compose ps` to verify postgres is healthy

### 0.6 Initialize Alembic for Database Migrations
- [ ] Run `uv run alembic init alembic` to create migration structure
- [ ] Configure `alembic/env.py` to use async SQLAlchemy and load config from `src/core/config.py`
- [ ] Update `alembic.ini` with `sqlalchemy.url` placeholder
- **Test**: Run `uv run alembic current` (should show no revisions yet)

---

## Phase 1: Database Layer (Models & Repositories)

### 1.1 Define Custom Exceptions
- [ ] Create `src/utils/exceptions.py`
- [ ] Define custom exceptions: `DocumentNotFoundError`, `InvalidFileTypeError`, `FileSizeExceededError`, `PDFProcessingError`, `EmbeddingServiceError`, `LLMServiceError`
- **Test**: Write `tests/unit/test_exceptions.py` to verify exceptions can be raised and caught

### 1.2 Create Document Model
- [ ] Add dependency: `sqlalchemy` with asyncpg driver
- [ ] Create `src/models/document.py` with `Document` SQLAlchemy model
- [ ] Fields: `id` (UUID PK), `filename`, `file_size`, `upload_date`, `status` (Enum), `error_message`, `total_pages`, `total_chunks`, `metadata` (JSON)
- [ ] Define `DocumentStatus` enum: `uploading`, `processing`, `ready`, `failed`
- **Test**: Write `tests/unit/test_models/test_document.py` to verify model instantiation

### 1.3 Create Chunk Model with pgvector
- [ ] Add dependency: `pgvector`
- [ ] Create `src/models/chunk.py` with `Chunk` SQLAlchemy model
- [ ] Fields: `id` (UUID PK), `document_id` (FK), `content`, `embedding` (Vector(1536)), `page_number`, `chunk_index`, `word_count`, `created_at`
- [ ] Define indexes: on `document_id`, on `embedding` (vector ops)
- **Test**: Write `tests/unit/test_models/test_chunk.py` to verify model instantiation

### 1.4 Create QueryLog Model
- [ ] Create `src/models/query_log.py` with `QueryLog` SQLAlchemy model
- [ ] Fields: `id` (UUID PK), `document_id` (FK), `query_text`, `answer_text`, `retrieved_chunks` (JSON), `is_answerable`, `response_time_ms`, `created_at`
- **Test**: Write `tests/unit/test_models/test_query_log.py` to verify model instantiation

### 1.5 Create Initial Database Migration
- [ ] Import all models in `src/models/__init__.py`
- [ ] Create migration: `uv run alembic revision --autogenerate -m "Initial schema with documents, chunks, query_logs"`
- [ ] Review generated migration file for correctness
- **Test**: Run `uv run alembic upgrade head` and verify tables exist using `psql`

### 1.6 Create Base Repository Pattern
- [ ] Create `src/repositories/base.py` with `BaseRepository` class
- [ ] Implement generic async methods: `get_by_id()`, `create()`, `update()`, `delete()`, `list_all()`
- [ ] Use SQLAlchemy async session
- **Test**: Write `tests/unit/test_repositories/test_base.py` with mock session

### 1.7 Create Document Repository
- [ ] Create `src/repositories/document_repo.py` extending `BaseRepository`
- [ ] Implement: `get_by_id()`, `create()`, `update_status()`, `delete()`
- [ ] Add method: `get_by_filename()` for duplicate checking
- **Test**: Write `tests/integration/test_repositories/test_document_repo.py` with test database

### 1.8 Create Vector Repository
- [ ] Create `src/repositories/vector_repo.py` extending `BaseRepository`
- [ ] Implement: `create_chunk()`, `get_chunks_by_document_id()`, `delete_chunks_by_document_id()`
- [ ] Implement: `similarity_search(embedding, top_k, min_score, document_id)` using pgvector `<=>` operator
- **Test**: Write `tests/integration/test_repositories/test_vector_repo.py` with sample embeddings

---

## Phase 2: Core Services (Utilities & Business Logic)

### 2.1 Create File Validation Utilities
- [ ] Create `src/utils/validators.py`
- [ ] Implement `validate_file_type(filename)` - check for `.pdf` extension
- [ ] Implement `validate_file_size(file_size, max_size_mb)` - check size limit
- [ ] Raise custom exceptions on validation failure
- **Test**: Write `tests/unit/test_utils/test_validators.py` with valid/invalid cases

### 2.2 Create Text Processing Utilities
- [ ] Add dependency: `tiktoken` for token counting
- [ ] Create `src/utils/text_processing.py`
- [ ] Implement `clean_text(text)` - remove extra whitespace, normalize unicode
- [ ] Implement `count_tokens(text, model)` - use tiktoken to count tokens
- **Test**: Write `tests/unit/test_utils/test_text_processing.py` with sample Spanish text

### 2.3 Create PDF Extraction Service
- [ ] Add dependencies: `pdfplumber`, `pypdf2`
- [ ] Create `src/services/pdf_service.py` with `PDFService` class
- [ ] Implement `extract_text_with_pages(file_path)` - return dict mapping page_number → text
- [ ] Use `pdfplumber` as primary, fallback to `pypdf2` on failure
- [ ] Handle errors: corrupted files, encrypted PDFs, empty PDFs
- **Test**: Write `tests/unit/test_services/test_pdf_service.py` with fixture PDF

### 2.4 Create Chunking Service
- [ ] Add dependency: `langchain-text-splitters`
- [ ] Create `src/services/chunking_service.py` with `ChunkingService` class
- [ ] Implement `chunk_text(pages_dict, chunk_size, overlap)` - split text preserving page numbers
- [ ] Return list of dicts: `{"content": str, "page_number": int, "chunk_index": int, "word_count": int}`
- [ ] Use `RecursiveCharacterTextSplitter` with token-based splitting
- **Test**: Write `tests/unit/test_services/test_chunking_service.py` verifying overlap and page tracking

### 2.5 Create Spanish Prompt Templates
- [ ] Create `src/core/prompts.py`
- [ ] Define `SYSTEM_PROMPT_TEMPLATE` with Spanish instructions for context-only answering
- [ ] Include rules: citations, no hallucination, Chilean Spanish adaptation, polite refusals
- [ ] Define `format_prompt(context, question)` function to inject context and question
- **Test**: Write `tests/unit/test_core/test_prompts.py` verifying template rendering

### 2.6 Create Embedding Service
- [ ] Add dependency: `openai`
- [ ] Create `src/services/embedding_service.py` with `EmbeddingService` class
- [ ] Implement `embed_text(text)` - call OpenAI API, return vector as list[float]
- [ ] Implement `embed_batch(texts)` - batch embed multiple texts (max 100)
- [ ] Handle API errors, rate limits, retry logic
- **Test**: Write `tests/unit/test_services/test_embedding_service.py` with mocked OpenAI client

### 2.7 Create LLM Service
- [ ] Create `src/services/llm_service.py` with `LLMService` class
- [ ] Implement `generate_answer(prompt)` - call OpenAI API with system + user prompt
- [ ] Configure model, temperature, max_tokens from settings
- [ ] Return response text and token usage
- [ ] Handle API errors, timeouts, content filtering
- **Test**: Write `tests/unit/test_services/test_llm_service.py` with mocked OpenAI client

### 2.8 Create Retrieval Service
- [ ] Create `src/services/retrieval_service.py` with `RetrievalService` class
- [ ] Inject `EmbeddingService` and `VectorRepository` dependencies
- [ ] Implement `retrieve_relevant_chunks(question, document_id, top_k, min_threshold)`
- [ ] Embed question, perform similarity search, filter by threshold
- [ ] Return list of chunks with scores and page numbers
- **Test**: Write `tests/integration/test_services/test_retrieval_service.py` with test DB

### 2.9 Create RAG Orchestration Service
- [ ] Create `src/services/rag_service.py` with `RAGService` class
- [ ] Inject: `RetrievalService`, `LLMService`, `QueryLogRepository`
- [ ] Implement `answer_question(document_id, question)`
- [ ] Pipeline: retrieve chunks → check if answerable → format prompt → generate answer → extract citations → log query
- [ ] Return structured response with answer, citations, is_answerable flag
- **Test**: Write `tests/integration/test_services/test_rag_service.py` with mocked LLM

---

## Phase 3: API Layer (Routes & Dependencies)

### 3.1 Create Pydantic Schemas for Documents
- [ ] Create `src/schemas/common.py` with `UUIDModel` base schema
- [ ] Create `src/schemas/document.py`
- [ ] Define schemas: `DocumentUploadResponse`, `DocumentStatusResponse`, `DocumentMetadata`
- [ ] Include validation for document status enum
- **Test**: Write `tests/unit/test_schemas/test_document.py` verifying serialization

### 3.2 Create Pydantic Schemas for Queries
- [ ] Create `src/schemas/query.py`
- [ ] Define schemas: `QueryRequest`, `Citation`, `QueryResponse`
- [ ] Include field validators for non-empty question strings
- **Test**: Write `tests/unit/test_schemas/test_query.py` verifying validation rules

### 3.3 Setup Database Dependency Injection
- [ ] Create `src/api/dependencies.py`
- [ ] Implement `get_async_session()` - FastAPI dependency yielding SQLAlchemy async session
- [ ] Implement factory functions for repositories and services
- [ ] Use `Depends()` for dependency injection
- **Test**: Write `tests/unit/test_api/test_dependencies.py` verifying dependency creation

### 3.4 Create Logging Configuration
- [ ] Create `src/core/logging.py`
- [ ] Configure structured logging with `logging` module
- [ ] Set log level from environment variable
- [ ] Format logs with timestamp, level, message, context
- **Test**: Write `tests/unit/test_core/test_logging.py` verifying log output

### 3.5 Create Health Check Routes
- [ ] Create `src/api/routes/health.py`
- [ ] Implement `GET /health` - return 200 with status message
- [ ] Implement `GET /health/ready` - check DB connection and return readiness
- [ ] Use async database ping
- **Test**: Write `tests/integration/test_api/test_health.py` using TestClient

### 3.6 Initialize FastAPI Application
- [ ] Create `src/api/main.py`
- [ ] Initialize FastAPI app with metadata (title, version, description)
- [ ] Add CORS middleware
- [ ] Include health check router
- [ ] Add startup/shutdown event handlers for DB connection
- **Test**: Run `uv run uvicorn src.api.main:app` and access `/health`

### 3.7 Create Document Upload Endpoint
- [ ] Create `src/api/routes/documents.py`
- [ ] Implement `POST /documents/upload` accepting multipart file upload
- [ ] Validate file using validators, save to temporary location
- [ ] Create document record with status `processing`
- [ ] Return `DocumentUploadResponse` with document ID
- **Test**: Write `tests/integration/test_api/test_documents.py` with file upload

### 3.8 Create Background Task for Document Processing
- [ ] In upload endpoint, trigger background task using FastAPI `BackgroundTasks`
- [ ] Task: extract text → chunk → embed → store in DB → update status to `ready`
- [ ] Handle errors and update status to `failed` with error message
- **Test**: Write test verifying status transitions after upload

### 3.9 Create Document Status Endpoint
- [ ] In `src/api/routes/documents.py`
- [ ] Implement `GET /documents/{document_id}/status`
- [ ] Query document by ID, return `DocumentStatusResponse` with status, progress, error
- [ ] Return 404 if document not found
- **Test**: Write test verifying status polling after upload

### 3.10 Create Document Metadata Endpoint
- [ ] In `src/api/routes/documents.py`
- [ ] Implement `GET /documents/{document_id}`
- [ ] Return full `DocumentMetadata` with all fields
- [ ] Return 404 if document not found
- **Test**: Write test verifying metadata retrieval

### 3.11 Create Document Deletion Endpoint
- [ ] In `src/api/routes/documents.py`
- [ ] Implement `DELETE /documents/{document_id}`
- [ ] Delete document and all associated chunks
- [ ] Return 204 on success, 404 if not found
- **Test**: Write test verifying document and chunks are deleted

### 3.12 Create Query Endpoint
- [ ] Create `src/api/routes/queries.py`
- [ ] Implement `POST /queries` accepting `QueryRequest` body
- [ ] Validate document exists and status is `ready`
- [ ] Call `RAGService.answer_question()`
- [ ] Return `QueryResponse` with answer, citations, is_answerable flag
- **Test**: Write `tests/integration/test_api/test_queries.py` with end-to-end flow

### 3.13 Add Global Exception Handlers
- [ ] In `src/api/main.py`
- [ ] Add exception handlers for custom exceptions (DocumentNotFoundError → 404, etc.)
- [ ] Add handler for validation errors → 422
- [ ] Add handler for unexpected errors → 500 with logging
- **Test**: Write tests verifying correct HTTP status codes for each error type

### 3.14 Add Request/Response Logging Middleware
- [ ] Create `src/api/middleware.py`
- [ ] Implement middleware logging request method, path, status code, duration
- [ ] Add correlation ID to requests
- [ ] Include in FastAPI app
- **Test**: Manually verify logs appear for requests

---

## Phase 4: Docker & Deployment

### 4.1 Create Dockerfile for API
- [ ] Create `Dockerfile` in project root
- [ ] Base: `python:3.12-slim`
- [ ] Install system dependencies: `gcc`, `postgresql-client`
- [ ] Copy `uv` binary from official image
- [ ] Install Python dependencies with `uv sync --frozen`
- [ ] Copy source code
- [ ] Expose port 8000
- **Test**: Run `docker build -t rag-api .` and verify build succeeds

### 4.2 Update docker-compose with API Service
- [ ] Add `api` service to `docker-compose.yml`
- [ ] Configure build context, command, volumes, ports, environment variables
- [ ] Set dependency on postgres service with healthcheck condition
- [ ] Configure restart policy
- **Test**: Run `docker-compose up --build` and verify both services start

### 4.3 Add Database Initialization to Startup
- [ ] Update Dockerfile CMD to run migrations before starting server
- [ ] Command: `uv run alembic upgrade head && uv run uvicorn ...`
- **Test**: Run `docker-compose up` and verify migrations run automatically

### 4.4 Create .dockerignore
- [ ] Create `.dockerignore` file
- [ ] Exclude: `.git`, `.env`, `__pycache__`, `*.pyc`, `.venv`, `tests/`, `.pytest_cache/`
- **Test**: Rebuild Docker image and verify build context is smaller

---

## Phase 5: Testing & Quality Assurance

### 5.1 Create Test Fixture for Sample Spanish PDF
- [ ] Add a sample Spanish PDF to `tests/fixtures/sample.pdf`
- [ ] Content should include multiple pages with Chilean Spanish text
- **Test**: Verify PDF can be opened and read

### 5.2 Write Unit Tests for PDF Service with Spanish Text
- [ ] Write `tests/unit/test_services/test_pdf_service.py`
- [ ] Test extraction from sample Spanish PDF
- [ ] Verify page numbers are correctly tracked
- [ ] Test error handling for corrupted files
- **Test**: Run `uv run pytest tests/unit/test_services/test_pdf_service.py -v`

### 5.3 Write Integration Test for Document Upload Flow
- [ ] Write `tests/integration/test_document_upload_flow.py`
- [ ] Test: upload PDF → poll status → verify status changes to `ready`
- [ ] Verify chunks and embeddings are created in DB
- **Test**: Run integration test with test database

### 5.4 Write Integration Test for RAG Query Flow
- [ ] Write `tests/integration/test_rag_flow.py`
- [ ] Test: upload PDF → wait for processing → ask question in Spanish → verify answer
- [ ] Test relevant question → verify citations included
- [ ] Test irrelevant question → verify polite refusal
- **Test**: Run integration test with test database and mocked LLM

### 5.5 Write Test for Chilean Spanish Understanding
- [ ] Add Chilean Spanish phrases to test queries (e.g., "¿Cuál es el cacho?", "¿De qué se trata la weá?")
- [ ] Verify system handles colloquialisms gracefully
- **Test**: Run query tests with Chilean Spanish phrases

### 5.6 Write Test for Hallucination Prevention
- [ ] Upload document about Topic A
- [ ] Ask question about completely unrelated Topic B
- [ ] Verify response includes refusal message and is_answerable = False
- [ ] Verify no citations are returned
- **Test**: Run test verifying out-of-scope handling

### 5.7 Write Test for Citation Accuracy
- [ ] Upload multi-page PDF
- [ ] Ask question answerable from specific pages
- [ ] Verify citations include correct page numbers
- [ ] Verify cited pages actually contain relevant content
- **Test**: Run test verifying citation page numbers match source

### 5.8 Add Code Coverage Configuration
- [ ] Configure `pytest-cov` in `pyproject.toml`
- [ ] Set minimum coverage threshold (e.g., 80%)
- [ ] Generate HTML coverage report
- **Test**: Run `uv run pytest --cov=src --cov-report=html` and review report

### 5.9 Add Code Formatting and Linting
- [ ] Add dependencies: `ruff` for linting and formatting
- [ ] Create `pyproject.toml` configuration for ruff
- [ ] Configure rules: line length, import sorting, code style
- **Test**: Run `uv run ruff check src/` and `uv run ruff format src/`

### 5.10 Create Pre-commit Hook Configuration
- [ ] Add dependency: `pre-commit`
- [ ] Create `.pre-commit-config.yaml`
- [ ] Configure hooks: ruff linting, ruff formatting, pytest
- [ ] Install hooks: `uv run pre-commit install`
- **Test**: Make a code change and commit to verify hooks run

---

## Phase 6: Documentation & Scripts

### 6.1 Create Sample Data Seeding Script
- [ ] Create `scripts/seed_sample.py`
- [ ] Script uploads a sample Spanish PDF and processes it
- [ ] Prints document ID for testing queries
- **Test**: Run script and verify document appears in database

### 6.2 Create Development Setup Script
- [ ] Create `scripts/setup_dev.sh`
- [ ] Script automates: `uv sync`, `docker-compose up -d`, `alembic upgrade head`, `seed_sample.py`
- [ ] Add error handling and status messages
- **Test**: Run script on fresh checkout and verify environment is ready

### 6.3 Update README with Setup Instructions
- [ ] Update `README.md` with project description
- [ ] Add prerequisites: Python 3.12, uv, Docker
- [ ] Add setup steps, running instructions, API documentation link
- [ ] Add example curl commands for API usage
- **Test**: Follow README instructions on fresh machine

### 6.4 Create API Usage Examples
- [ ] Create `docs/usage.md`
- [ ] Document upload flow with curl examples
- [ ] Document query flow with Spanish example questions
- [ ] Include expected responses for success and error cases
- **Test**: Execute all curl examples and verify they work

### 6.5 Document Testing Strategy
- [ ] Create `docs/testing.md`
- [ ] Explain test structure: unit, integration, E2E
- [ ] Document how to run tests, coverage, and fixtures
- [ ] Include examples of adding new tests
- **Test**: Follow testing documentation to run all test suites

---

## Phase 7: MVP Validation

### 7.1 Perform End-to-End Manual Test
- [ ] Start full system with `docker-compose up`
- [ ] Upload a real Spanish PDF document
- [ ] Monitor logs to verify processing pipeline
- [ ] Ask 5+ questions in Chilean Spanish via API
- [ ] Verify all responses have correct citations
- **Test**: Document results of manual test

### 7.2 Test Error Scenarios
- [ ] Upload non-PDF file → verify error response
- [ ] Upload file exceeding size limit → verify error response
- [ ] Upload corrupted PDF → verify error response
- [ ] Query non-existent document → verify 404 response
- [ ] Query document still processing → verify appropriate error
- **Test**: Verify all error messages are in Spanish and user-friendly

### 7.3 Performance Testing
- [ ] Upload a 50-page Spanish PDF
- [ ] Measure processing time
- [ ] Measure query response time (including LLM call)
- [ ] Verify times are within acceptable ranges (<60s upload, <3s query)
- **Test**: Document performance metrics

### 7.4 Security Review
- [ ] Verify `.env` is in `.gitignore` and not committed
- [ ] Verify API keys are loaded from environment only
- [ ] Test file upload size limits are enforced
- [ ] Test file type validation works
- [ ] Check for SQL injection vulnerabilities (ORM usage)
- **Test**: Document security checklist completion

### 7.5 Create MVP Demo Script
- [ ] Create script demonstrating all user stories
- [ ] Include: upload, status check, successful question, out-of-scope question, citations
- [ ] Record output/screenshots
- **Test**: Execute demo script and verify all user stories are satisfied

---

## Success Criteria for MVP

✅ All user stories from `user-stories.md` are implemented and tested
✅ System can process Spanish PDF documents and extract text
✅ System can answer questions in Chilean Spanish with citations
✅ System refuses to answer out-of-scope questions politely
✅ All API endpoints return appropriate status codes and errors
✅ Docker setup allows one-command deployment
✅ Test coverage >= 80%
✅ Code passes linting and formatting checks
✅ Documentation is complete and accurate

---

## Notes

- **Test-Driven Development**: Write tests BEFORE implementation for each task
- **One Task at a Time**: Complete and test each task before moving to the next
- **SOLID Principles**: Follow Single Responsibility, Dependency Injection, Interface Segregation
- **Error Handling**: Every service method should handle errors gracefully
- **Logging**: Add informative logs at key points in the pipeline
- **Spanish Language**: All user-facing messages must be in Spanish
- **Citations**: Always track page numbers through the entire pipeline
