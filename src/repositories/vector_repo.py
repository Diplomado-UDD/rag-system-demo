"""Vector repository for similarity search operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.chunk import Chunk
from src.repositories.base import BaseRepository


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
        Perform similarity search using cosine distance.

        Args:
            embedding: Query embedding vector
            top_k: Number of results to return
            min_score: Minimum similarity score (0-1)
            document_id: Optional document ID to filter results

        Returns:
            List of (chunk, similarity_score) tuples ordered by relevance
        """
        # Convert embedding to pgvector format
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        # Build query with cosine similarity
        # pgvector uses <=> for cosine distance (0 = identical, 2 = opposite)
        # Convert to similarity score: 1 - (distance / 2)
        # Build conditional WHERE clause for optional document_id filter
        if document_id is not None:
            where_clause = "WHERE document_id = :doc_id"
        else:
            where_clause = "WHERE TRUE"

        query = text(
            f"""
            SELECT *, 1 - (embedding <=> :embedding_vec) AS similarity
            FROM chunks
            {where_clause}
              AND embedding IS NOT NULL
              AND 1 - (embedding <=> :embedding_vec) >= :min_score
            ORDER BY embedding <=> :embedding_vec
            LIMIT :top_k
            """
        )

        # Build parameters dict, only including doc_id if provided
        params = {
            "embedding_vec": embedding_str,
            "min_score": min_score,
            "top_k": top_k,
        }
        if document_id is not None:
            params["doc_id"] = document_id

        result = await self.session.execute(query, params)

        rows = result.fetchall()

        # Convert rows to Chunk objects and extract similarity scores
        chunks_with_scores = []
        for row in rows:
            chunk = Chunk(
                id=row.id,
                document_id=row.document_id,
                content=row.content,
                embedding=row.embedding,
                page_number=row.page_number,
                chunk_index=row.chunk_index,
                word_count=row.word_count,
                created_at=row.created_at,
            )
            similarity = float(row.similarity)
            chunks_with_scores.append((chunk, similarity))

        return chunks_with_scores
