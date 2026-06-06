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
- **Respuestas RAG con LLM vía OpenRouter** ✅ FUNCIONANDO
- Almacenamiento vectorial en PostgreSQL + pgvector
- Despliegue con Docker
- 103 tests unitarios + integración

> 💡 **Solución técnica**: La búsqueda vectorial usa psycopg2 síncrono con `register_vector()` para compatibilidad óptima con pgvector.

## Tecnologías

- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI + Python 3.12
- **Base de datos**: PostgreSQL + pgvector
- **IA**: OpenRouter (OpenAI-compatible para embeddings + LLM)
- **Gestión de dependencias**: uv (backend) + npm (frontend)
- **Contenedores**: Docker + docker-compose

## Requisitos

- Docker Desktop
- Python 3.12+ (para desarrollo local)
- OpenRouter API key

## Puertos del Sistema

El sistema utiliza los siguientes puertos:

| Servicio | Puerto Host | Puerto Contenedor | Descripción |
|----------|-------------|-------------------|-------------|
| **Frontend (Dev)** | `5173` | - | Servidor de desarrollo Vite (npm run dev) |
| **Frontend (Prod)** | `80` | `80` | Nginx sirviendo build de producción |
| **Backend API** | `8000` | `8000` | FastAPI application |
| **PostgreSQL** | `5433` | `5432` | Base de datos con pgvector |

### URLs de Acceso

- **Interfaz web (desarrollo)**: http://localhost:5173
- **Interfaz web (producción)**: http://localhost
- **API docs (Swagger)**: http://localhost:8000/docs
- **API docs (ReDoc)**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health
- **Database**: `postgresql://rag_user:rag_password@localhost:5433/rag_db`

> **Nota**: El puerto 5433 se usa en el host para evitar conflictos con instalaciones locales de PostgreSQL que típicamente usan el puerto 5432.

## Inicio Rapido con Docker

1. **Clonar repositorio**
```bash
git clone <repo-url>
cd rag-system-demo
```

2. **Configurar variables de entorno**
```bash
cp .env.production .env
# Editar .env con tu OpenRouter API key
```

3. **Iniciar servicios**
```bash
docker-compose up -d
```

4. **Acceder a la aplicacion**
- **Interfaz web**: http://localhost
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
# Editar DATABASE_URL y OPENROUTER_API_KEY
```

5. **Ejecutar migraciones**
```bash
uv run alembic upgrade head
```

6. **Iniciar servidor**
```bash
uv run uvicorn src.main:app --reload
```

7. **Iniciar frontend (desarrollo)**
```bash
cd frontend
npm install
npm run dev
```

8. **Acceder a la aplicación**
- **Frontend dev**: http://localhost:5173
- **API docs**: http://localhost:8000/docs

> **Importante**: `uv run uvicorn src.main:app --reload` solo inicia el backend (API). Para que `http://localhost` (puerto 80) responda, debes iniciar el frontend en Docker (`docker-compose up -d frontend`) o usar el frontend dev en `http://localhost:5173`.

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

## 🔧 Gestión y Monitoreo de la Base de Datos

### Consultas Básicas

#### Ver historial de queries

```bash
# Ver últimas 10 queries con detalles
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
SELECT
    query_text,
    LEFT(answer_text, 80) as respuesta_preview,
    is_answerable,
    response_time_ms,
    JSONB_ARRAY_LENGTH(retrieved_chunks::jsonb) as chunks_usados,
    created_at
FROM query_logs
ORDER BY created_at DESC
LIMIT 10;
"
```

#### Ver una query específica completa

```bash
# Mostrar respuesta completa con todos los detalles
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
SELECT
    query_text,
    answer_text,
    is_answerable,
    response_time_ms,
    jsonb_pretty(retrieved_chunks::jsonb) AS chunks_ids
FROM query_logs
WHERE is_answerable = true
ORDER BY created_at DESC
LIMIT 1;
" -x
```

### Estadísticas y Métricas

#### Resumen general del sistema

```bash
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
SELECT
    (SELECT COUNT(*) FROM query_logs) as total_queries,
    (SELECT COUNT(*) FROM query_logs WHERE is_answerable = true) as queries_respondibles,
    (SELECT COUNT(*) FROM documents) as total_documentos,
    (SELECT COUNT(*) FROM chunks) as total_chunks;
"
```

#### Estadísticas de rendimiento

```bash
# Estadísticas por tipo de query
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
SELECT
    is_answerable AS respondible,
    COUNT(*) as total_queries,
    ROUND(AVG(response_time_ms)::numeric, 2) as tiempo_promedio_ms,
    MIN(response_time_ms) as tiempo_min_ms,
    MAX(response_time_ms) as tiempo_max_ms
FROM query_logs
GROUP BY is_answerable;
"
```

#### Queries más lentas

```bash
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
SELECT
    query_text,
    response_time_ms,
    is_answerable,
    created_at
FROM query_logs
ORDER BY response_time_ms DESC
LIMIT 10;
"
```

#### Queries más frecuentes

```bash
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
SELECT
    query_text,
    COUNT(*) as veces_consultada,
    ROUND(AVG(response_time_ms)::numeric, 2) as tiempo_promedio_ms
FROM query_logs
GROUP BY query_text
HAVING COUNT(*) > 1
ORDER BY veces_consultada DESC;
"
```

### Gestión de Documentos

#### Listar todos los documentos

```bash
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
SELECT
    id,
    filename,
    status,
    total_pages,
    total_chunks,
    upload_date
FROM documents
ORDER BY upload_date DESC;
"
```

#### Ver chunks de un documento específico

```bash
# Reemplazar <document_id> con el UUID del documento
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
SELECT
    chunk_index,
    LEFT(content, 100) as content_preview,
    page_number
FROM chunks
WHERE document_id = '<document_id>'
ORDER BY chunk_index;
"
```

### Análisis de Uso

#### Actividad por día

```bash
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
SELECT
    DATE(created_at) as fecha,
    COUNT(*) as total_queries,
    COUNT(*) FILTER (WHERE is_answerable = true) as respondibles,
    ROUND(AVG(response_time_ms)::numeric, 2) as tiempo_promedio_ms
FROM query_logs
GROUP BY DATE(created_at)
ORDER BY fecha DESC;
"
```

#### Búsqueda por palabra clave en queries

```bash
# Buscar queries que contengan una palabra específica
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
SELECT
    query_text,
    is_answerable,
    response_time_ms,
    created_at
FROM query_logs
WHERE query_text ILIKE '%ciberseguridad%'
ORDER BY created_at DESC;
"
```

### Mantenimiento

#### Limpiar queries antiguas

```bash
# Eliminar queries más antiguas de 30 días
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
DELETE FROM query_logs
WHERE created_at < NOW() - INTERVAL '30 days';
"
```

#### Eliminar un documento y sus chunks

```bash
# PRECAUCIÓN: Esto eliminará el documento y todos sus chunks
docker-compose exec -T postgres psql -U rag_user -d rag_db -c "
DELETE FROM documents WHERE id = '<document_id>';
"
```

### Consola Interactiva

```bash
# Entrar al psql interactivo
docker-compose exec postgres psql -U rag_user -d rag_db

# Comandos útiles dentro de psql:
# \dt                       - listar todas las tablas
# \d query_logs             - describir estructura de query_logs
# \d documents              - describir estructura de documents
# \d chunks                 - describir estructura de chunks
# \x                        - toggle formato expandido (mejor para ver respuestas largas)
# \q                        - salir
```

### Backup y Restore

#### Crear backup

```bash
docker-compose exec -T postgres pg_dump -U rag_user rag_db > backup_$(date +%Y%m%d).sql
```

#### Restaurar backup

```bash
docker-compose exec -T postgres psql -U rag_user -d rag_db < backup_20250111.sql
```

### Persistencia de Datos

Los datos persisten después de `docker-compose down` gracias al volumen nombrado `postgres_data`.

Para eliminar completamente los datos (incluyendo documentos y queries):

```bash
docker-compose down -v  # La flag -v elimina los volúmenes
```

> ⚠️ **Advertencia**: El comando anterior eliminará permanentemente todos los datos almacenados.

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

# OpenRouter
OPENROUTER_API_KEY=sk-or-...
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=~openai/gpt-latest

# Chunking
CHUNK_SIZE=600
CHUNK_OVERLAP=100

# Retrieval
TOP_K_RESULTS=5
MIN_SIMILARITY_THRESHOLD=0.3

# Puertos (opcional, para desarrollo)
BACKEND_PORT=8000          # Puerto del servidor FastAPI
FRONTEND_PORT=5173         # Puerto del servidor Vite dev
DB_PORT=5433              # Puerto del host para PostgreSQL
```

### Configuración de Puertos en Docker

Los puertos se configuran en `docker-compose.yml`:

- **PostgreSQL**: Mapeo `5433:5432` (host:contenedor)
- **Backend**: Mapeo `8000:8000`
- **Frontend**: Mapeo `80:80` (producción)

Para cambiar los puertos del host, edita el archivo `docker-compose.yml` en la sección `ports` de cada servicio.

## Arquitectura

El sistema sigue un flujo RAG clasico:

1. **Ingesta**: PDF -> Extracción -> Chunking -> Embeddings -> Vector DB
2. **Query**: Pregunta -> Embedding -> Busqueda -> Contexto -> LLM -> Respuesta

## Licencia

Libre
