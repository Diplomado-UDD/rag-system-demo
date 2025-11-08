# Sistema RAG en Español

Sistema de Recuperación y Generación Aumentada (RAG) para documentos PDF en español chileno con interfaz web interactiva.

## Características

### ✅ Sistema Completamente Funcional
- Interfaz web moderna con React y Tailwind CSS
- Upload de documentos con drag-and-drop
- Chat interactivo para consultas RAG
- Procesamiento de documentos PDF en español
- Extracción de texto y chunking
- Generación de embeddings con OpenAI
- **Búsqueda semántica vectorial con pgvector** ✅ FUNCIONANDO
- **Respuestas RAG con GPT-4** ✅ FUNCIONANDO
- Almacenamiento vectorial en PostgreSQL + pgvector
- Despliegue con Docker
- 103 tests unitarios + integración

> 💡 **Solución técnica**: La búsqueda vectorial usa psycopg2 síncrono con `register_vector()` para compatibilidad óptima con pgvector.

## Tecnologías

- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI + Python 3.12
- **Base de datos**: PostgreSQL + pgvector
- **IA**: OpenAI (embeddings + GPT-4)
- **Gestión de dependencias**: uv (backend) + npm (frontend)
- **Contenedores**: Docker + docker-compose

## Requisitos

- Docker Desktop
- Python 3.12+ (para desarrollo local)
- OpenAI API key

## Inicio Rapido con Docker

1. **Clonar repositorio**
```bash
git clone <repo-url>
cd rag-system-demo
```

2. **Configurar variables de entorno**
```bash
cp .env.production .env
# Editar .env con tu OpenAI API key
```

3. **Iniciar servicios**
```bash
docker-compose up -d
```

4. **Iniciar frontend**
```bash
cd frontend
npm install
npm run dev
```

5. **Acceder a la aplicacion**
- **Interfaz web**: http://localhost:5173
- **API docs**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

## Desarrollo Local

1. **Instalar uv**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Instalar dependencias**
```bash
uv sync
```

3. **Iniciar PostgreSQL**
```bash
docker-compose up -d postgres
```

4. **Configurar .env**
```bash
cp .env.example .env
# Editar DATABASE_URL y OPENAI_API_KEY
```

5. **Ejecutar migraciones**
```bash
uv run alembic upgrade head
```

6. **Iniciar servidor**
```bash
uv run uvicorn src.main:app --reload
```

## Ejecutar Tests

```bash
# Todos los tests
uv run pytest

# Solo unit tests
uv run pytest tests/unit/

# Con coverage
uv run pytest --cov=src --cov-report=html
```

## Uso de la API

### 1. Subir documento PDF

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@documento.pdf"
```

### 2. Verificar estado del documento

```bash
curl "http://localhost:8000/documents/{document_id}/status"
```

### 3. Hacer pregunta

```bash
curl -X POST "http://localhost:8000/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Cuál es el objetivo principal del documento?",
    "document_id": "uuid-del-documento"
  }'
```

### 4. Listar documentos

```bash
curl "http://localhost:8000/documents/"
```

## Estructura del Proyecto

```
.
├── frontend/          # React + Vite application
│   ├── src/
│   │   ├── components/    # React components (Upload, List, Chat)
│   │   ├── services/      # API client (Axios)
│   │   └── App.jsx        # Main application
│   ├── package.json
│   └── vite.config.js
├── src/               # Backend Python code
│   ├── api/           # Endpoints FastAPI
│   ├── core/          # Configuración y prompts
│   ├── models/        # Modelos SQLAlchemy
│   ├── repositories/  # Capa de datos
│   ├── services/      # Lógica de negocio
│   └── utils/         # Utilidades
├── tests/
│   ├── unit/          # Tests unitarios (103 tests)
│   └── integration/   # Tests de integración
├── alembic/           # Migraciones DB
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Configuración

Variables de entorno clave en `.env`:

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://rag_user:password@localhost:5433/rag_db

# OpenAI
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4-turbo-preview

# Chunking
CHUNK_SIZE=600
CHUNK_OVERLAP=100

# Retrieval
TOP_K_RESULTS=5
MIN_SIMILARITY_THRESHOLD=0.3
```

## Arquitectura

El sistema sigue un flujo RAG clasico:

1. **Ingesta**: PDF -> Extracción -> Chunking -> Embeddings -> Vector DB
2. **Query**: Pregunta -> Embedding -> Busqueda -> Contexto -> LLM -> Respuesta

## Licencia

Libre
