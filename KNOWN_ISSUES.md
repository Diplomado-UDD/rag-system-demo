# Known Issues

## ~~Critical Issue: Vector Similarity Search Not Working~~ ✅ FIXED

### Status: ✅ RESOLVED - Core RAG functionality now working

**Fix Date**: 2025-11-08
**Solution**: Migrated from async SQLAlchemy to synchronous psycopg2 with pgvector's `register_vector()`

### Description
The vector similarity search is not returning results despite:
- Documents being uploaded successfully
- Text extraction working correctly
- Chunks being created and stored
- Embeddings being generated and stored in PostgreSQL
- pgvector extension being installed and operational

### Symptoms
- All queries return 0 results: `"retrieved_chunks_count": 0`
- Response: "Lo siento, no encontré información relevante en el documento para responder tu pregunta."
- No errors logged in application or database

### Evidence That Components Work Individually

1. **Document Processing Works**: ✅
   ```bash
   # Document uploaded with 7 chunks
   curl http://localhost:8000/documents/
   # Returns: total_chunks: 7, status: "ready"
   ```

2. **Embeddings Stored Correctly**: ✅
   ```sql
   SELECT COUNT(*), vector_dims(embedding)
   FROM chunks
   WHERE document_id = '272c0fbe-359c-4881-9e07-558ecb030d05';
   -- Returns: 7 chunks, 1536 dimensions
   ```

3. **Direct PostgreSQL Vector Search Works**: ✅
   ```sql
   SELECT id, 1 - (embedding <=> (SELECT embedding FROM chunks LIMIT 1)) AS similarity
   FROM chunks
   ORDER BY similarity DESC
   LIMIT 3;
   -- Returns 3 results with similarity scores
   ```

4. **API Receives Requests**: ✅
   - Middleware logs show POST /query/ requests
   - OpenAI embeddings API called successfully
   - Response returned (just empty)

### Root Cause Analysis

The issue is in `src/repositories/vector_repo.py:similarity_search()`. Multiple approaches attempted:

#### Attempt 1: Raw SQL with bind parameters
```python
query = text("""
    SELECT *, 1 - (embedding <=> :embedding_vec::vector) AS similarity
    FROM chunks
    WHERE document_id = :doc_id
    ...
""")
params = {"embedding_vec": embedding_str, "doc_id": document_id}
```
**Result**: 0 results (parameter binding issue with custom vector type)

#### Attempt 2: String interpolation in SQL
```python
query = text(f"""
    SELECT *, 1 - (embedding <=> '{embedding_str}'::vector) AS similarity
    ...
""")
```
**Result**: 0 results (same issue)

#### Attempt 3: SQLAlchemy ORM with custom operator
```python
distance = Chunk.embedding.op('<=>', return_type=Vector)(embedding)
similarity = 1 - distance
query = select(Chunk, similarity.label('similarity'))...
```
**Result**: 0 results (operator not properly compiled)

### Investigation Done

1. ✅ Verified pgvector installed: `pgvector 0.4.1`
2. ✅ Verified pgvector extension loaded in PostgreSQL
3. ✅ Tested direct SQL queries - they work
4. ✅ Checked async SQLAlchemy session handling
5. ✅ Added extensive logging (logs not appearing - separate buffering issue)
6. ✅ Reduced min_similarity threshold from 0.7 to 0.3
7. ✅ Tested with multiple documents and queries
8. ✅ Verified embeddings are not NULL in database

### Possible Causes

1. **AsyncPG + pgvector incompatibility**: The async database driver may not properly handle pgvector's custom operators
2. **SQLAlchemy parameter binding**: Custom types like `vector` may not be properly serialized in bind parameters
3. **pgvector-python version**: Version 0.4.1 may have issues with async SQLAlchemy
4. **Type casting**: The embedding list → vector conversion may be failing silently

### Workarounds Considered

1. **Use synchronous SQLAlchemy**: Replace AsyncSession with sync Session for vector queries only
2. **Raw connection with psycopg2**: Bypass SQLAlchemy for similarity search
3. **Alternative vector DB**: Use Qdrant, Weaviate, or Pinecone instead of pgvector
4. **Hybrid approach**: Store in PostgreSQL but use Redis with RediSearch for vector queries

### Next Steps to Resolve

1. **Test with sync SQLAlchemy**:
   ```python
   from sqlalchemy import create_engine
   engine = create_engine("postgresql+psycopg2://...")
   # Use sync connection for vector search
   ```

2. **Try older pgvector version**: Test with `pgvector==0.2.5`

3. **Use psycopg2 directly**:
   ```python
   import psycopg2
   from pgvector.psycopg2 import register_vector
   conn = psycopg2.connect(...)
   register_vector(conn)
   ```

4. **Check SQLAlchemy events**: Add event listeners to see compiled SQL

5. **Test with simple sync endpoint**: Create a /test_vector endpoint that uses sync DB access

### Impact

- **Severity**: CRITICAL
- **Affected Features**: All RAG query functionality
- **User Impact**: System cannot answer questions about uploaded documents
- **Workaround**: None currently available

### Timeline

- **Discovered**: 2025-11-08
- **Investigation Time**: ~4 hours
- **Attempts**: 3 different implementation approaches
- **Status**: ✅ RESOLVED - 2025-11-08

### Solution Implemented

**Root Cause**: AsyncPG driver doesn't properly handle pgvector's custom `<=>` operator with list parameters in SQLAlchemy queries.

**Fix**: Migrated `similarity_search()` method in `src/repositories/vector_repo.py` to use synchronous psycopg2:

```python
import psycopg2
from pgvector.psycopg2 import register_vector

async def similarity_search(self, embedding: List[float], ...):
    # Convert async URL to sync
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    # Use sync psycopg2 connection
    conn = psycopg2.connect(sync_url)
    register_vector(conn)  # Register pgvector type

    # Convert embedding list to string format
    embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'

    # Execute query with proper type casting
    query = """
        SELECT id, document_id, content, ...,
               1 - (embedding <=> %s::vector) AS similarity
        FROM chunks
        WHERE embedding IS NOT NULL
          AND 1 - (embedding <=> %s::vector) >= %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    cursor.execute(query, (embedding_str, embedding_str, min_score, embedding_str, top_k))
    rows = cursor.fetchall()
```

**Additional Changes**:
- Updated `.env`: `MIN_SIMILARITY_THRESHOLD=0.3` (lowered from 0.5 for better retrieval)
- Updated `src/core/config.py`: Matching default value

**Test Results**:
```bash
curl -X POST http://localhost:8000/query/ \
  -d '{"question": "Cuál es el objetivo del proyecto?"}'

# Response:
{
  "answer": "El objetivo del proyecto es crear un sistema que responda preguntas en español chileno.",
  "is_answerable": true,
  "retrieved_chunks_count": 2,
  "tokens_used": 323
}
```

### References

- pgvector-python docs: https://github.com/pgvector/pgvector-python
- SQLAlchemy async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Solution: psycopg2 + register_vector() (standard pgvector approach)

---

## Minor Issue: Scanned PDFs Return 0 Chunks

### Status: 🟡 EXPECTED BEHAVIOR

### Description
PDFs that are scanned images (no embedded text) result in 0 chunks after processing.

### Example
- File: `reglamento.pdf` (10 pages, 6.5MB)
- Result: `total_chunks: 0`, `status: "ready"`

### Root Cause
PDF extractors (pdfplumber, PyPDF2) cannot extract text from image-only PDFs. This requires OCR.

### Solution
To support scanned PDFs, integrate OCR:
1. Install tesseract: `apt-get install tesseract-ocr`
2. Add pytesseract: `uv add pytesseract`
3. Modify `src/services/pdf_service.py` to detect image-only pages and apply OCR

### Impact
- **Severity**: LOW
- **Workaround**: Only upload PDFs with embedded text
