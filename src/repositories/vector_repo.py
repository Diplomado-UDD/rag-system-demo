"""Vector repository for similarity search operations."""

import logging
import os
from typing import List, Optional
from uuid import UUID

import psycopg2
from pgvector.psycopg2 import register_vector
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.chunk import Chunk
from src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class VectorRepository(BaseRepository[Chunk]):
    """Repository for vector operations and similarity search."""

    def __init__(self, session: AsyncSession):
        """Initialize vector repository."""
        super().__init__(Chunk, session)

    async def create_chunk(self, chunk: Chunk) -> Chunk:
        """
        Create a new chunk.

        Args:
            chunk: Chunk instance to create

        Returns:
            Created chunk
        """
        return await self.create(chunk)

    async def get_chunks_by_document_id(self, document_id: UUID) -> List[Chunk]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document UUID

        Returns:
            List of chunks ordered by chunk_index
        """
        result = await self.session.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
        )
        return list(result.scalars().all())

    async def delete_chunks_by_document_id(self, document_id: UUID) -> None:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document UUID
        """
        await self.session.execute(delete(Chunk).where(Chunk.document_id == document_id))
        await self.session.commit()

    async def similarity_search(
        self,
        embedding: List[float],
        top_k: int = 5,
        min_score: float = 0.0,
        document_id: Optional[UUID] = None,
    ) -> List[tuple[Chunk, float]]:
        """
        Perform similarity search using cosine distance with sync psycopg2.

        Uses synchronous psycopg2 connection for vector search as it has
        better pgvector compatibility than async drivers.

        Args:
            embedding: Query embedding vector
            top_k: Number of results to return
            min_score: Minimum similarity score (0-1)
            document_id: Optional document ID to filter results

        Returns:
            List of (chunk, similarity_score) tuples ordered by relevance
        """
        logger.info(f"[SYNC] Vector search: doc_id={document_id}, min_score={min_score}, top_k={top_k}")

        # Get sync connection string from async one
        database_url = os.getenv("DATABASE_URL", "")
        # Convert asyncpg URL to psycopg2 URL
        sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

        # Use sync psycopg2 for vector search
        conn = None
        try:
            conn = psycopg2.connect(sync_url)
            register_vector(conn)

            cursor = conn.cursor()

            # Convert embedding list to string format for pgvector
            # pgvector expects format: '[0.1,0.2,0.3,...]'
            embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'

            # Build query with optional document filter
            if document_id is not None:
                query = """
                    SELECT
                        id, document_id, content, page_number,
                        chunk_index, word_count, created_at,
                        1 - (embedding <=> %s::vector) AS similarity
                    FROM chunks
                    WHERE document_id = %s
                      AND embedding IS NOT NULL
                      AND 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                params = (embedding_str, str(document_id), embedding_str, min_score, embedding_str, top_k)
            else:
                query = """
                    SELECT
                        id, document_id, content, page_number,
                        chunk_index, word_count, created_at,
                        1 - (embedding <=> %s::vector) AS similarity
                    FROM chunks
                    WHERE embedding IS NOT NULL
                      AND 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                params = (embedding_str, embedding_str, min_score, embedding_str, top_k)

            logger.info(f"[SYNC] Executing query with params: doc_id={document_id if document_id else 'all'}, min_score={min_score}, top_k={top_k}, embedding_len={len(embedding)}")
            cursor.execute(query, params)
            rows = cursor.fetchall()

            logger.info(f"[SYNC] Vector search returned {len(rows)} rows")
            if len(rows) > 0:
                logger.info(f"[SYNC] Top result similarity: {float(rows[0][7])}")

            # Convert rows to Chunk objects with scores
            chunks_with_scores = []
            for row in rows:
                chunk = Chunk(
                    id=row[0],
                    document_id=row[1],
                    content=row[2],
                    page_number=row[3],
                    chunk_index=row[4],
                    word_count=row[5],
                    created_at=row[6],
                )
                similarity = float(row[7])
                chunks_with_scores.append((chunk, similarity))

            cursor.close()
            conn.close()

            return chunks_with_scores

        except Exception as e:
            logger.error(f"[SYNC] Error in vector search: {e}")
            if conn:
                conn.close()
            raise
