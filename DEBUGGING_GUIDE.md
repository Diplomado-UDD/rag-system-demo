# Guía de Debugging: Vector Search Issue

## ✅ ISSUE RESOLVED - 2025-11-08

**Solución**: Migrado a psycopg2 síncrono con `register_vector()`
**Archivo modificado**: `src/repositories/vector_repo.py`
**Estado**: Sistema funcionando correctamente

---

## Proceso de Debugging (Histórico)

Este documento contiene los pasos que se siguieron para investigar el problema de búsqueda vectorial.

## Verificaciones Rápidas

### 1. Verificar que hay chunks en la base de datos
```bash
docker-compose exec postgres psql -U rag_user -d rag_db -c "SELECT document_id, COUNT(*), MIN(chunk_index), MAX(chunk_index) FROM chunks GROUP BY document_id;"
```

### 2. Verificar que los embeddings existen
```bash
docker-compose exec postgres psql -U rag_user -d rag_db -c "SELECT id, embedding IS NOT NULL as has_embedding, vector_dims(embedding) as dims FROM chunks LIMIT 5;"
```

### 3. Probar búsqueda vectorial directa en PostgreSQL
```bash
docker-compose exec postgres psql -U rag_user -d rag_db
```

```sql
-- Obtener un embedding de ejemplo
\x
SELECT embedding FROM chunks LIMIT 1 \gset

-- Buscar chunks similares
SELECT id, content, 1 - (embedding <=> :'embedding') AS similarity
FROM chunks
WHERE embedding IS NOT NULL
ORDER BY similarity DESC
LIMIT 5;
```

### 4. Verificar versiones de dependencias
```bash
docker-compose exec app uv pip list | grep -E "pgvector|sqlalchemy|asyncpg"
```

## Tests de Integración

### Test 1: Crear endpoint de prueba síncrono

Agregar a `src/api/routes/query.py`:

```python
from sqlalchemy import create_engine, text

@router.get("/test-vector-sync")
async def test_vector_sync():
    """Test vector search with synchronous connection."""
    import os
    db_url = os.getenv("DATABASE_URL").replace("asyncpg", "psycopg2")

    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Get a sample embedding
        result = conn.execute(text("SELECT embedding FROM chunks LIMIT 1"))
        embedding = result.scalar()

        # Search similar
        query = text("""
            SELECT id, content, 1 - (embedding <=> :emb) AS similarity
            FROM chunks
            WHERE embedding IS NOT NULL
            ORDER BY similarity DESC
            LIMIT 3
        """)

        results = conn.execute(query, {"emb": str(embedding)})
        rows = [{"id": str(r[0]), "similarity": float(r[2])} for r in results]

    return {"results": rows, "count": len(rows)}
```

Probar:
```bash
curl http://localhost:8000/query/test-vector-sync
```

### Test 2: Verificar compilación de query ORM

Agregar logging al query compilado:

```python
from sqlalchemy.dialects import postgresql

# En similarity_search()
compiled = query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
logger.info(f"Compiled SQL: {compiled}")
```

### Test 3: Usar raw asyncpg directamente

```python
import asyncpg

@router.get("/test-asyncpg")
async def test_asyncpg():
    """Test with raw asyncpg."""
    conn = await asyncpg.connect("postgresql://rag_user:rag_password@postgres:5432/rag_db")

    await conn.execute("SELECT register_vector()")  # May be needed

    # Get sample embedding
    row = await conn.fetchrow("SELECT embedding FROM chunks LIMIT 1")
    embedding = row['embedding']

    # Search
    results = await conn.fetch("""
        SELECT id, 1 - (embedding <=> $1::vector) AS similarity
        FROM chunks
        ORDER BY similarity DESC
        LIMIT 3
    """, embedding)

    await conn.close()

    return {"count": len(results)}
```

## Investigar Logs

### Habilitar SQL echo en SQLAlchemy

En `src/config/database.py`:

```python
engine = create_async_engine(
    settings.database_url,
    echo=True,  # <-- Add this
    pool_pre_ping=True,
)
```

Esto imprimirá todas las queries SQL ejecutadas.

### Agregar logging a nivel DEBUG

En `src/main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
```

### Capturar stdout sin buffering

En `Dockerfile`:

```dockerfile
ENV PYTHONUNBUFFERED=1
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Alternativas a Probar

### Opción 1: Usar pgvector con psycopg2 (sync)

Modificar dependencies en `pyproject.toml`:
```toml
dependencies = [
    ...
    "psycopg2-binary>=2.9.11",
]
```

Crear un servicio síncrono solo para vector search.

### Opción 2: Usar pgvector 0.2.x

```bash
uv add "pgvector==0.2.5"
```

Versiones antiguas pueden tener mejor compatibilidad con SQLAlchemy async.

### Opción 3: Usar ORM mapping con custom type

```python
from pgvector.sqlalchemy import Vector as PgVector

class Chunk(Base):
    # ...
    embedding = mapped_column(PgVector(1536))
```

### Opción 4: Implementar con raw SQL + manual mapping

Abandonar el ORM para esta operación específica:

```python
async def similarity_search(self, embedding: List[float], ...):
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    query = f"""
    SELECT
        id, document_id, content, page_number, chunk_index, word_count, created_at,
        1 - (embedding <=> '{embedding_str}'::vector) AS similarity
    FROM chunks
    WHERE embedding IS NOT NULL
      AND 1 - (embedding <=> '{embedding_str}'::vector) >= :min_score
    ORDER BY embedding <=> '{embedding_str}'::vector
    LIMIT :top_k
    """

    result = await self.session.execute(
        text(query),
        {"min_score": min_score, "top_k": top_k}
    )

    chunks = []
    for row in result:
        chunk = Chunk()
        chunk.id = row.id
        chunk.document_id = row.document_id
        # ... map all fields manually
        chunks.append((chunk, row.similarity))

    return chunks
```

## Herramientas de Debugging

### pgvector debug info

```sql
-- Check pgvector version
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check index
\d+ chunks

-- Analyze index usage
EXPLAIN ANALYZE
SELECT id, 1 - (embedding <=> '[0.1,0.2,...]'::vector) AS similarity
FROM chunks
ORDER BY embedding <=> '[0.1,0.2,...]'::vector
LIMIT 5;
```

### Monitor async tasks

```python
import asyncio

# In route handler
pending = len(asyncio.all_tasks())
logger.info(f"Pending async tasks: {pending}")
```

## Recursos

- pgvector GitHub: https://github.com/pgvector/pgvector
- pgvector-python: https://github.com/pgvector/pgvector-python
- SQLAlchemy async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- asyncpg: https://magicstack.github.io/asyncpg/

## Notas del Debugging Anterior

- Direct SQL in PostgreSQL works ✓
- SQLAlchemy query never throws errors ✓
- Always returns empty list []
- Logs with logger.info() don't appear (buffering issue)
- Logs with print(flush=True) don't appear either
- Tried: raw SQL text(), ORM select(), custom op('<=>')
- All approaches return 0 results

**Hypothesis**: AsyncPG may not be properly handling the pgvector custom type in parameter binding, even when cast explicitly.

**Next to try**: Use sync psycopg2 connection for vector queries only.
