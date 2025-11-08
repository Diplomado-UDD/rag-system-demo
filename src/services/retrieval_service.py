"""Retrieval service for finding relevant document chunks."""

import logging
from typing import Optional
from uuid import UUID

from src.models.chunk import Chunk
from src.repositories.vector_repo import VectorRepository
from src.services.embedding_service import EmbeddingService
from src.utils.exceptions import RAGSystemError

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for retrieving relevant chunks based on queries."""

    def __init__(
        self,
        vector_repo: VectorRepository,
        embedding_service: EmbeddingService,
        top_k: int = 5,
        min_similarity: float = 0.3,
    ):
        """
        Initialize retrieval service.

        Args:
            vector_repo: Repository for vector operations
            embedding_service: Service for generating embeddings
            top_k: Number of results to retrieve
            min_similarity: Minimum similarity threshold (0-1)
        """
        self.vector_repo = vector_repo
        self.embedding_service = embedding_service
        self.top_k = top_k
        self.min_similarity = min_similarity

    async def retrieve_relevant_chunks(
        self,
        query: str,
        document_id: Optional[UUID] = None,
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None,
    ) -> list[tuple[Chunk, float]]:
        """
        Retrieve chunks relevant to a query.

        Args:
            query: User query text
            document_id: Optional document ID to filter results
            top_k: Override default number of results
            min_similarity: Override default similarity threshold

        Returns:
            List of (chunk, similarity_score) tuples ordered by relevance

        Raises:
            RAGSystemError: If retrieval fails
        """
        if not query or not query.strip():
            raise RAGSystemError("No se puede buscar con consulta vacía")

        try:
            logger.info(f"retrieve_relevant_chunks called with query='{query[:50]}...', document_id={document_id}")

            # Generate embedding for query
            query_embedding = self.embedding_service.embed_text(query)
            logger.info(f"Generated embedding with {len(query_embedding)} dimensions")

            # Use provided values or defaults
            k = top_k if top_k is not None else self.top_k
            min_score = (
                min_similarity if min_similarity is not None else self.min_similarity
            )

            logger.info(f"Calling similarity_search with top_k={k}, min_score={min_score}")

            # Perform similarity search
            results = await self.vector_repo.similarity_search(
                embedding=query_embedding,
                top_k=k,
                min_score=min_score,
                document_id=document_id,
            )

            logger.info(f"similarity_search returned {len(results)} results")

            return results

        except Exception as e:
            if isinstance(e, RAGSystemError):
                raise
            raise RAGSystemError(f"Error al recuperar chunks relevantes: {str(e)}")
