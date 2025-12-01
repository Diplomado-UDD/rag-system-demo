# RAG System Demo - Architecture

## Overview

A RAG (Retrieval-Augmented Generation) system designed to process Spanish PDF documents and answer questions in Chilean Spanish. The system extracts, vectorizes, and stores document content, then uses semantic search to provide accurate, citation-backed answers while preventing hallucinations on out-of-scope queries.

## Architecture Diagrams

> **Note**: Estos diagramas están diseñados para ser legibles en papel tamaño carta (8.5" x 11"). Los diagramas Mermaid se renderizan automáticamente en la mayoría de visores (GitHub, GitLab, VS Code, mermaid.live). Para impresión, exporta a PDF desde un visor compatible con Mermaid para obtener el mejor resultado.

### 1. System Architecture Overview

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React UI<br/>Port 5173]
        COMP1[DocumentUpload]
        COMP2[DocumentList]
        COMP3[ChatInterface]
        UI --> COMP1
        UI --> COMP2
        UI --> COMP3
    end
    
    subgraph "API Layer"
        API[FastAPI<br/>Port 8000]
        R1[Documents Route]
        R2[Query Route]
        R3[Health Route]
        API --> R1
        API --> R2
        API --> R3
    end
    
    subgraph "Service Layer"
        RAG[RAG Service]
        PDF[PDF Service]
        CHUNK[Chunking Service]
        EMBED[Embedding Service]
        RET[Retrieval Service]
        LLM[LLM Service]
        RAG --> RET
        RAG --> LLM
        RET --> EMBED
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL<br/>+ pgvector<br/>Port 5433)]
        DOC_REPO[Document Repo]
        VEC_REPO[Vector Repo]
        DOC_REPO --> DB
        VEC_REPO --> DB
    end
    
    subgraph "External Services"
        OPENAI[OpenAI API<br/>GPT-4 + Embeddings]
    end
    
    COMP1 -->|HTTP/REST| R1
    COMP2 -->|HTTP/REST| R1
    COMP3 -->|HTTP/REST| R2
    
    R1 --> PDF
    R1 --> CHUNK
    R1 --> EMBED
    R1 --> DOC_REPO
    R1 --> VEC_REPO
    
    R2 --> RAG
    
    EMBED --> OPENAI
    LLM --> OPENAI
    RET --> VEC_REPO
    
    style UI fill:#e1f5ff
    style API fill:#fff4e1
    style RAG fill:#ffe1f5
    style DB fill:#e1ffe1
    style OPENAI fill:#f5e1ff
```

### 2. Document Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant PDFService
    participant ChunkingService
    participant EmbeddingService
    participant DocumentRepo
    participant VectorRepo
    participant OpenAI
    participant Database

    User->>Frontend: Upload PDF
    Frontend->>API: POST /documents/upload
    API->>PDFService: Validate file
    API->>DocumentRepo: Create document (status: processing)
    DocumentRepo->>Database: INSERT document
    
    API->>PDFService: Extract text with pages
    PDFService-->>API: Pages with text
    
    API->>ChunkingService: Chunk text
    ChunkingService-->>API: Chunks with metadata
    
    API->>EmbeddingService: Generate embeddings
    EmbeddingService->>OpenAI: Batch embed request
    OpenAI-->>EmbeddingService: Embeddings (1536 dim)
    EmbeddingService-->>API: Embeddings list
    
    loop For each chunk
        API->>VectorRepo: Create chunk with embedding
        VectorRepo->>Database: INSERT chunk
    end
    
    API->>DocumentRepo: Update status to ready
    DocumentRepo->>Database: UPDATE document
    
    API-->>Frontend: Document response (ready)
    Frontend->>User: Show success notification
```

### 3. RAG Query Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant RAGService
    participant RetrievalService
    participant EmbeddingService
    participant VectorRepo
    participant LLMService
    participant OpenAI
    participant Database

    User->>Frontend: Type question (Spanish)
    Frontend->>API: POST /query/ {question, document_id}
    
    API->>RAGService: answer_question()
    
    RAGService->>RetrievalService: retrieve_relevant_chunks()
    RetrievalService->>EmbeddingService: embed_text(query)
    EmbeddingService->>OpenAI: Generate query embedding
    OpenAI-->>EmbeddingService: Query embedding
    EmbeddingService-->>RetrievalService: Embedding vector
    
    RetrievalService->>VectorRepo: similarity_search()
    VectorRepo->>Database: SELECT chunks WHERE<br/>embedding <=> query_embedding<br/>ORDER BY similarity<br/>LIMIT top_k
    Database-->>VectorRepo: Relevant chunks with scores
    VectorRepo-->>RetrievalService: Chunks with scores
    RetrievalService-->>RAGService: Chunks with scores
    
    alt Relevant chunks found
        RAGService->>RAGService: Format context from chunks
        RAGService->>LLMService: generate_answer(prompt)
        LLMService->>OpenAI: GPT-4 API call<br/>(context + question + system prompt)
        OpenAI-->>LLMService: Answer text
        LLMService-->>RAGService: Answer + tokens
        RAGService->>RAGService: Extract citations
        RAGService-->>API: RAGResponse (answer, citations, is_answerable)
    else No relevant chunks
        RAGService-->>API: RAGResponse (polite refusal, is_answerable=false)
    end
    
    API-->>Frontend: QueryResponse
    Frontend->>User: Display answer with citations
```

### 4. Database Schema

```mermaid
erDiagram
    DOCUMENTS ||--o{ CHUNKS : contains
    DOCUMENTS ||--o{ QUERY_LOGS : references
    
    DOCUMENTS {
        uuid id PK
        string filename
        integer file_size
        timestamp upload_date
        enum status
        text error_message
        integer total_pages
        integer total_chunks
        jsonb doc_metadata
    }
    
    CHUNKS {
        uuid id PK
        uuid document_id FK
        text content
        vector embedding "1536 dimensions"
        integer page_number
        integer chunk_index
        integer word_count
        timestamp created_at
    }
    
    QUERY_LOGS {
        uuid id PK
        uuid document_id FK
        text query_text
        text answer_text
        jsonb retrieved_chunks
        boolean is_answerable
        integer response_time_ms
        timestamp created_at
    }
```

### 5. Docker Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Network: rag_network"
        subgraph "Frontend Container"
            FE[Frontend<br/>Nginx<br/>Port 80]
        end
        
        subgraph "Backend Container"
            BE[FastAPI App<br/>Port 8000]
            PYTHON[Python 3.12<br/>uv + dependencies]
        end
        
        subgraph "Database Container"
            PG[PostgreSQL 16<br/>Port 5432]
            PGVEC[pgvector extension]
            DATA[(PostgreSQL Data<br/>Volume)]
        end
    end
    
    subgraph "External Services"
        OPENAI_API[OpenAI API<br/>HTTPS]
    end
    
    USER[User Browser] -->|HTTP| FE
    FE -->|HTTP/REST| BE
    BE -->|SQL/asyncpg| PG
    BE -->|HTTPS| OPENAI_API
    PG --> PGVEC
    PG --> DATA
    
    style FE fill:#e1f5ff
    style BE fill:#fff4e1
    style PG fill:#e1ffe1
    style OPENAI_API fill:#f5e1ff
```

### 6. Component Interaction Diagram

```mermaid
graph LR
    subgraph "Upload Pipeline"
        A[PDF Upload] --> B[PDF Service]
        B --> C[Chunking Service]
        C --> D[Embedding Service]
        D --> E[Vector Repository]
        E --> F[PostgreSQL]
    end
    
    subgraph "Query Pipeline"
        G[User Question] --> H[Embedding Service]
        H --> I[Vector Repository]
        I --> J[Similarity Search]
        J --> K[RAG Service]
        K --> L[LLM Service]
        L --> M[OpenAI GPT-4]
        M --> N[Answer with Citations]
    end
    
    F -.->|Vector Storage| I
    E -.->|Store Embeddings| F
    
    style A fill:#e1f5ff
    style G fill:#ffe1f5
    style F fill:#e1ffe1
    style M fill:#f5e1ff
```

## Technology Stack

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Package Manager**: npm

### Backend
- **Language**: Python 3.12+
- **API Framework**: FastAPI
- **Database**: PostgreSQL 16+ with pgvector extension
- **Environment Management**: uv
- **Containerization**: Docker & Docker Compose
- **LLM Provider**: OpenAI (with Spanish language support)
- **Embeddings**: Multilingual embeddings (`text-embedding-3-small`)
- **PDF Processing**: PyPDF2, pdfplumber
- **Vector Search**: pgvector (cosine similarity)

---

## Network Ports and Access

### Port Configuration

| Service | Host Port | Container Port | Protocol | Description |
|---------|-----------|----------------|----------|-------------|
| **Frontend (Dev)** | 5173 | - | HTTP | Vite development server |
| **Frontend (Prod)** | 80 | 80 | HTTP | Nginx serving production build |
| **Backend API** | 8000 | 8000 | HTTP | FastAPI application |
| **PostgreSQL** | 5433 | 5432 | TCP | PostgreSQL with pgvector |

### Access URLs

#### Development Environment
- **Web Interface**: http://localhost:5173
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Database Connection**: `postgresql://rag_user:rag_password@localhost:5433/rag_db`

#### Production Environment (Docker)
- **Web Interface**: http://localhost
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database Connection** (from containers): `postgresql://rag_user:rag_password@postgres:5432/rag_db`

### Port Notes

> **PostgreSQL Port 5433**: The host uses port 5433 instead of the default 5432 to avoid conflicts with local PostgreSQL installations. Inside the Docker network, containers communicate using the standard port 5432.

> **Frontend Ports**: Development uses Vite's default port 5173, while production uses port 80 (standard HTTP) via Nginx.

> **API Port**: FastAPI runs on port 8000 in both development and production environments.

---

## Project Structure

```
rag-system-demo/
├── .git/
├── .gitignore
├── .python-version              # 3.12
├── README.md
├── architecture.md              # This file
├── user-stories.md
├── tasks.md
├── pyproject.toml               # Backend uv configuration
├── uv.lock
│
├── docker-compose.yml           # Multi-container orchestration
├── Dockerfile                   # Backend API container
├── .env.example
├── .env                         # Gitignored
│
├── frontend/                    # React web application
│   ├── src/
│   │   ├── components/
│   │   │   ├── DocumentUpload.jsx
│   │   │   ├── DocumentList.jsx
│   │   │   └── ChatInterface.jsx
│   │   ├── services/
│   │   │   └── api.js           # Axios API client
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vite.config.js
│   └── .env
│
├── alembic/                     # DB migrations
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
│
├── src/                         # Backend Python code
│   ├── __init__.py
│   │
│   ├── api/                     # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py              # App entry point
│   │   ├── dependencies.py      # DI container
│   │   ├── middleware.py        # CORS, error handling
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py        # Health checks
│   │       ├── documents.py     # Upload & processing status
│   │       └── queries.py       # RAG Q&A endpoint
│   │
│   ├── core/                    # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py            # Settings (env vars)
│   │   ├── logging.py           # Logging setup
│   │   └── prompts.py           # LLM prompt templates (Spanish)
│   │
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   ├── pdf_service.py       # PDF text extraction
│   │   ├── chunking_service.py  # Text splitting
│   │   ├── embedding_service.py # Vector generation
│   │   ├── retrieval_service.py # Similarity search
│   │   ├── llm_service.py       # LLM calls (OpenAI/Anthropic)
│   │   └── rag_service.py       # Orchestrates RAG pipeline
│   │
│   ├── models/                  # SQLAlchemy ORM
│   │   ├── __init__.py
│   │   ├── document.py          # Document metadata
│   │   ├── chunk.py             # Text chunks + embeddings
│   │   └── query_log.py         # Query history
│   │
│   ├── schemas/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── document.py          # Upload/status DTOs
│   │   ├── query.py             # Query request/response
│   │   └── common.py            # Shared schemas
│   │
│   ├── repositories/            # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py              # Base repository
│   │   ├── document_repo.py     # Document CRUD
│   │   └── vector_repo.py       # Vector search queries
│   │
│   └── utils/                   # Helpers
│       ├── __init__.py
│       ├── text_processing.py   # Cleaning, normalization
│       ├── validators.py        # File validation
│       └── exceptions.py        # Custom exceptions
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/
│   │   ├── test_services/
│   │   └── test_utils/
│   ├── integration/
│   │   ├── test_api/
│   │   └── test_rag_flow.py
│   └── fixtures/
│       └── sample.pdf           # Test PDF
│
└── scripts/
    ├── init_db.sh               # Initialize pgvector
    └── seed_sample.py           # Load test document
```

---

## Component Descriptions

### 0. Frontend Layer (`frontend/`)

**Purpose**: User-facing web interface for document management and chat interaction

#### **Components** (`src/components/`)

**DocumentUpload.jsx**
- Drag-and-drop file upload interface
- Client-side PDF validation (type, size)
- Upload progress indicator
- Error display with user-friendly messages
- Features: File preview, remove file, upload button states

**DocumentList.jsx**
- Display all uploaded documents with metadata
- Real-time status badges (ready/processing/failed)
- Document selection for filtered queries
- Delete document functionality
- Auto-refresh on new uploads
- Visual indicators: page count, chunk count, processing state

**ChatInterface.jsx**
- Real-time chat UI with message history
- User/assistant message bubbles
- Loading indicators (typing animation)
- Display query metadata (chunks retrieved, tokens used, answerability)
- Scroll-to-bottom on new messages
- Support for document-filtered or global queries

#### **Services** (`src/services/`)

**api.js**
- Axios HTTP client configuration
- API base URL from environment variable
- Service modules:
  - `documentService`: upload, getStatus, list, delete
  - `queryService`: ask (submit questions)
  - `healthService`: check backend health
- Centralized error handling
- Request/response interceptors for CORS

#### **Main App** (`src/App.jsx`)
- Root component orchestrating all features
- State management for:
  - Selected document ID (for filtered queries)
  - Refresh trigger (document list updates)
- Responsive layout (desktop: 3-column, mobile: stacked)
- Header with connection status
- Footer with attribution

#### **Styling**
- Tailwind CSS for utility-first styling
- Responsive breakpoints (sm, md, lg)
- Custom animations (pulse, bounce, spin)
- Color palette: Blue primary, gray neutrals, status colors
- Dark mode support (future enhancement)

---

### 1. API Layer (`src/api/`)

**Purpose**: HTTP interface for document uploads and queries

#### `main.py`
- FastAPI app initialization
- CORS middleware (allow frontend origin)
- Global exception handlers
- Startup/shutdown events (DB connection pool)

#### `routes/documents.py`
- `POST /documents/upload`: Accept PDF file
- `GET /documents/{id}/status`: Check processing status
- `GET /documents/{id}`: Get document metadata
- `DELETE /documents/{id}`: Remove document

#### `routes/queries.py`
- `POST /queries`: Submit question, get answer with citations
- Response includes: answer text, confidence, source chunks, page numbers

#### `routes/health.py`
- `GET /health`: System health check
- `GET /health/ready`: Readiness probe (DB + LLM API connectivity)

---

### 2. Services Layer (`src/services/`)

**Purpose**: Core business logic implementing user stories

#### **pdf_service.py** (Story 1.1 - 1.4)
- Extract text from uploaded PDF
- Handle errors: invalid format, corrupted files, oversized
- Return structured text with page numbers
- Libraries: `pdfplumber` (primary), fallback to `PyPDF2`

#### **chunking_service.py** (Story 2.3)
- Split document into semantic chunks (500-800 tokens)
- Preserve context with overlap (100 tokens)
- Maintain page number references for citations
- Strategy: Sentence-aware splitting

#### **embedding_service.py** (Story 2.3)
- Generate multilingual embeddings
- Model: OpenAI `text-embedding-3-small` (supports Spanish)
- Batch processing for efficiency
- Normalize vectors for cosine similarity

#### **retrieval_service.py** (Story 2.5)
- Perform vector similarity search (top-k=5)
- Return chunks with scores and page numbers
- Filter by minimum similarity threshold (>0.7)
- Re-ranking based on page proximity (optional)

#### **llm_service.py** (Stories 2.2, 2.4, 3.1, 3.2)
- Interface with LLM API (GPT-4 or Claude 3.5 Sonnet)
- System prompt in Spanish enforcing:
  - Answer ONLY from provided context
  - Respond in clear Spanish
  - Include page citations
  - Refuse out-of-scope questions politely
- Token counting and cost tracking

#### **rag_service.py** (Orchestrator)
- End-to-end pipeline:
  1. Embed user query
  2. Retrieve relevant chunks
  3. Check if context is sufficient
  4. Construct Spanish prompt with context
  5. Generate answer via LLM
  6. Extract citations
  7. Log query/response

---

### 3. Data Layer

#### **Database Models** (`src/models/`)

**documents table**:
```python
id              UUID (PK)
filename        VARCHAR(255)
file_size       INTEGER
upload_date     TIMESTAMP
status          ENUM('uploading', 'processing', 'ready', 'failed')
error_message   TEXT (nullable)
total_pages     INTEGER
total_chunks    INTEGER
metadata        JSONB (language, encoding, etc.)
```

**chunks table**:
```python
id              UUID (PK)
document_id     UUID (FK -> documents)
content         TEXT
embedding       VECTOR(1536)  # pgvector
page_number     INTEGER
chunk_index     INTEGER
word_count      INTEGER
created_at      TIMESTAMP

INDEX: GIN index on embedding (cosine similarity)
INDEX: document_id + chunk_index
```

**query_logs table**:
```python
id                  UUID (PK)
document_id         UUID (FK -> documents)
query_text          TEXT
answer_text         TEXT
retrieved_chunks    JSONB (array of chunk IDs + scores)
is_answerable       BOOLEAN
response_time_ms    INTEGER
created_at          TIMESTAMP
```

#### **Repositories** (`src/repositories/`)

- **document_repo.py**: CRUD operations for documents
- **vector_repo.py**:
  - `similarity_search(embedding, top_k, min_score)`
  - Raw SQL with pgvector operators (`<=>`)
  - Returns chunks ordered by relevance

---

### 4. Configuration (`src/core/`)

#### **config.py**
```python
DATABASE_URL: str
OPENAI_API_KEY: str  # or ANTHROPIC_API_KEY
EMBEDDING_MODEL: str = "text-embedding-3-small"
LLM_MODEL: str = "gpt-4-turbo-preview"
CHUNK_SIZE: int = 600
CHUNK_OVERLAP: int = 100
TOP_K_RESULTS: int = 5
MIN_SIMILARITY_THRESHOLD: float = 0.7
MAX_FILE_SIZE_MB: int = 50
ALLOWED_FILE_TYPES: list = [".pdf"]
```

#### **prompts.py**
System prompt in Spanish:
```
Eres un asistente útil que responde preguntas basándose EXCLUSIVAMENTE
en el contexto proporcionado de un documento PDF.

REGLAS ESTRICTAS:
1. Si la respuesta NO está en el contexto, responde: "Lo siento, esa
   información no se encuentra en el documento. ¿Podrías reformular
   tu pregunta o hacer otra relacionada con el contenido?"
2. SIEMPRE incluye las páginas de referencia: [Página X]
3. Responde en español claro y natural, adaptado al español chileno
4. NO inventes información
5. Si el contexto es insuficiente, pide más detalles

CONTEXTO:
{context}

PREGUNTA: {question}
```

---

## State Management

### Application State
- **Configuration**: Loaded once at startup from `.env`
- **DB Connection Pool**: SQLAlchemy async engine (singleton)
- **LLM Client**: Cached OpenAI/Anthropic client instance

### Document Processing State
- **Status Tracking**: `documents.status` field
  - `uploading` → `processing` → `ready` / `failed`
- **Progress Indicator**: Frontend polls `GET /documents/{id}/status`

### Data State
- **Document Metadata**: PostgreSQL `documents` table
- **Vector Embeddings**: PostgreSQL `chunks` table (pgvector)
- **Query History**: PostgreSQL `query_logs` table

### No Session State
- Stateless API (each request independent)
- No user authentication required (demo scope)

---

## Service Connection Flow

The system follows a layered architecture connecting frontend, API, services, and external dependencies. See the [System Architecture Overview](#1-system-architecture-overview) diagram above for a visual representation of component relationships.

**Key Connections:**
- **Frontend → API**: HTTP/REST requests via Axios (CORS enabled)
- **API → Services**: Dependency injection for business logic
- **Services → Database**: SQLAlchemy async queries to PostgreSQL with pgvector
- **Services → OpenAI**: HTTPS API calls for embeddings and LLM generation

### Flow Details

For detailed flow diagrams, see:
- [Document Processing Flow](#2-document-processing-flow) - Complete upload pipeline
- [RAG Query Flow](#3-rag-query-flow) - Question answering pipeline

#### **Document Upload Flow Summary** (User Story 1)

1. User uploads PDF via frontend
2. Frontend sends `POST /documents/upload` to API
3. API validates file and creates document record (status: 'processing')
4. Processing pipeline:
   - Extract text from PDF (PDF Service)
   - Split into semantic chunks (Chunking Service)
   - Generate embeddings (Embedding Service → OpenAI)
   - Store chunks with embeddings in database (Vector Repository)
   - Update document status to 'ready'
5. Frontend polls status endpoint and shows success notification

#### **Query Flow Summary** (User Story 2 & 3)

1. User types question in Spanish
2. Frontend sends `POST /query/` with question and optional document_id
3. RAG Service orchestrates:
   - Generate query embedding (Embedding Service)
   - Search similar chunks (Retrieval Service → Vector Repository)
   - Check relevance threshold
4. If relevant chunks found:
   - Format context from chunks
   - Build prompt with Spanish system instructions
   - Generate answer via LLM (LLM Service → OpenAI GPT-4)
   - Extract citations and metadata
5. If no relevant chunks: Return polite refusal message
6. Log query and return response to frontend

---

## Docker Architecture

### **docker-compose.yml**

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: rag_postgres
    environment:
      POSTGRES_DB: rag_db
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sh:/docker-entrypoint-initdb.d/init.sh
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rag_user -d rag_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    container_name: rag_api
    command: uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
      - /app/.venv  # Prevent volume mount of venv
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://rag_user:${DB_PASSWORD}@postgres:5432/rag_db
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      EMBEDDING_MODEL: text-embedding-3-small
      LLM_MODEL: gpt-4-turbo-preview
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
```

### **Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies in a virtual environment
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start app
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000"]
```

### **scripts/init_db.sh**

```bash
#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOSQL
```

---

## Key Design Decisions

### 1. **Chilean Spanish Support**
- Use multilingual embedding models
- Spanish-specific LLM prompts
- Test with Chilean Spanish phrases

### 2. **Citation System** (User Story 2.5)
- Chunks store page numbers
- LLM instructed to include `[Página X]` in answers
- Frontend can highlight source pages

### 3. **Hallucination Prevention** (User Story 3.1)
- Strict system prompt: "Answer ONLY from context"
- Similarity threshold filtering (>0.7)
- Out-of-scope detection: if no relevant chunks → polite refusal

### 4. **Processing Feedback** (User Story 1.2)
- Status enum: `uploading`, `processing`, `ready`, `failed`
- Frontend polls `/documents/{id}/status` every 2s
- Estimated time: ~30s for 50-page PDF

### 5. **Error Handling** (User Story 1.4)
```python
- Invalid format → 400: "Solo se aceptan archivos PDF"
- Corrupted PDF → 422: "El archivo está corrupto"
- Oversized → 413: "Tamaño máximo: 50MB"
- Processing failure → 500: "Error interno, intenta nuevamente"
```

### 6. **pgvector vs Dedicated Vector DB**
- Simpler deployment (single DB)
- Sufficient for demo (<10k documents)
- ACID guarantees for metadata + vectors

---

## API Endpoints

### Document Management

**Upload Document**
```http
POST /documents/upload
Content-Type: multipart/form-data

file: <pdf_file>

Response 202:
{
  "id": "uuid",
  "filename": "documento.pdf",
  "status": "processing",
  "message": "Procesando documento..."
}
```

**Check Status**
```http
GET /documents/{id}/status

Response 200:
{
  "id": "uuid",
  "status": "ready",  # or "processing", "failed"
  "progress": 100,
  "total_pages": 45,
  "error": null
}
```

### Querying

**Ask Question**
```http
POST /queries
Content-Type: application/json

{
  "document_id": "uuid",
  "question": "¿Cuál es el objetivo del proyecto?"
}

Response 200:
{
  "answer": "El objetivo del proyecto es...",
  "citations": [
    {"page": 3, "chunk_id": "uuid", "relevance": 0.89},
    {"page": 7, "chunk_id": "uuid", "relevance": 0.82}
  ],
  "is_answerable": true,
  "response_time_ms": 1450
}

Response 200 (out-of-scope):
{
  "answer": "Lo siento, esa información no se encuentra en el documento. ¿Podrías reformular tu pregunta?",
  "citations": [],
  "is_answerable": false,
  "response_time_ms": 650
}
```

---

## Development Workflow

### Setup

```bash
# Navigate to project
cd rag-system-demo

# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Setup environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and DB_PASSWORD

# Start Docker services
docker-compose up -d

# Wait for DB to be ready, then run migrations
uv run alembic upgrade head

# (Optional) Seed sample document
uv run python scripts/seed_sample.py
```

### Running

```bash
# Development (hot reload)
uv run uvicorn src.api.main:app --reload --port 8000

# Or via Docker
docker-compose up --build

# Access API docs
open http://localhost:8000/docs
```

### Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=html

# Test specific flow
uv run pytest tests/integration/test_rag_flow.py -v

# Manual testing
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@sample.pdf"
```

---

## Performance Considerations

### Optimization Strategies

1. **Embeddings**: Batch process during upload (5-10 chunks/request)
2. **Vector Search**: GIN index on pgvector column
3. **Caching**: Cache embeddings for common queries (Redis - future)
4. **Async I/O**: All DB and API calls use `async/await`
5. **Connection Pooling**: SQLAlchemy pool (min=5, max=20)

### Expected Performance
- Upload processing: ~30s for 50-page PDF
- Query response: 1-2s (including LLM call)
- Concurrent users: ~50 (single instance)

---

## Security Notes

- API keys in `.env` (never committed)
- File size validation (max 50MB)
- File type validation (PDF only)
- Input sanitization on queries
- SQL injection prevention (ORM)
- Rate limiting (future: 10 req/min per IP)

---

## Future Enhancements

1. ~~**Frontend**: React UI with drag-drop upload~~ ✅ **COMPLETED**
2. **Multi-document Search**: Query across multiple PDFs simultaneously
3. **User Authentication**: Multi-tenant support with JWT tokens
4. **Streaming Responses**: Server-sent events for real-time LLM output
5. **Analytics Dashboard**: Query patterns, popular pages, usage metrics
6. **Export Functionality**: Download Q&A sessions as PDF/Markdown
7. **Language Detection**: Auto-detect document language
8. **Dark Mode**: Frontend theme switching
9. **Document Preview**: PDF viewer with highlighted relevant pages
10. **Advanced Filters**: Filter by date, tags, document type
11. **Batch Upload**: Multiple document upload at once
12. **Docker Compose for Frontend**: Add frontend to containerized stack

---

## Testing Strategy

### Unit Tests
- `test_pdf_service`: Extraction accuracy
- `test_chunking_service`: Boundary preservation
- `test_embedding_service`: Dimension validation
- `test_prompts`: Spanish template correctness

### Integration Tests
- `test_upload_flow`: End-to-end document processing
- `test_query_flow`: RAG pipeline with mock LLM
- `test_out_of_scope`: Hallucination prevention

### E2E Tests
- Upload real Spanish PDF
- Ask relevant question → verify citations
- Ask irrelevant question → verify refusal message
- Test Chilean Spanish phrases

---

## Monitoring

### Logging
- Request/response logs (FastAPI middleware)
- Service-level logs (document processing stages)
- Error tracking (Sentry - future)

### Metrics (Future)
- Average query response time
- Document processing success rate
- Top queried pages
- Out-of-scope query ratio

---

## User Story Mapping to Architecture

| User Story | Component | Implementation |
|------------|-----------|----------------|
| 1.1 - Upload PDF | `routes/documents.py` | `POST /documents/upload` |
| 1.2 - Processing indicator | `routes/documents.py` | `GET /documents/{id}/status` with polling |
| 1.3 - Success notification | Frontend logic | Status transition to `ready` |
| 1.4 - Error alerts | `pdf_service.py` | Exception handling + error messages |
| 2.1 - Text input | `routes/queries.py` | `POST /queries` |
| 2.2 - Chilean Spanish | `prompts.py` | Spanish system prompt + multilingual embeddings |
| 2.3 - Answer from PDF | `rag_service.py` | Context-only answering enforced |
| 2.4 - Clear Spanish | `llm_service.py` | LLM model selection (GPT-4/Claude) |
| 2.5 - Citations | `rag_service.py` | Page extraction from chunks |
| 3.1 - No hallucinations | `retrieval_service.py` | Similarity threshold + prompt constraints |
| 3.2 - Rephrase prompt | `prompts.py` | System prompt with refusal message |

---

## Conclusion

This architecture provides a robust foundation for a Spanish-language RAG system with strong guardrails against hallucinations and clear user feedback. The modular design allows for easy testing, scaling, and future enhancements while meeting all user story requirements.
