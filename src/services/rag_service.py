"""RAG service orchestrating the complete question-answering flow."""

import logging
import time
from typing import Optional
from uuid import UUID

from src.core.prompts import SYSTEM_PROMPT_TEMPLATE, format_context_from_chunks
from src.models.query_log import QueryLog
from src.repositories.document_repo import DocumentRepository
from src.repositories.query_log_repo import QueryLogRepository
from src.services.llm_service import LLMService
from src.services.retrieval_service import RetrievalService
from src.utils.exceptions import RAGSystemError

logger = logging.getLogger(__name__)


class RAGResponse:
    """Response from RAG service."""

    def __init__(
        self,
        answer: str,
        is_answerable: bool,
        retrieved_chunks_count: int,
        tokens_used: int,
        chunk_ids: list[UUID],
    ):
        """
        Initialize RAG response.

        Args:
            answer: Generated answer text
            is_answerable: Whether question was answerable from context
            retrieved_chunks_count: Number of chunks retrieved
            tokens_used: Total tokens used in LLM call
            chunk_ids: List of chunk IDs used
        """
        self.answer = answer
        self.is_answerable = is_answerable
        self.retrieved_chunks_count = retrieved_chunks_count
        self.tokens_used = tokens_used
        self.chunk_ids = chunk_ids


class RAGService:
    """Service orchestrating RAG question-answering flow."""

    # Phrase indicating question cannot be answered from context
    NOT_ANSWERABLE_PHRASE = "Lo siento, esa información no se encuentra en el documento"

    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_service: LLMService,
        query_log_repo: QueryLogRepository,
        document_repo: DocumentRepository,
    ):
        """
        Initialize RAG service.

        Args:
            retrieval_service: Service for retrieving relevant chunks
            llm_service: Service for generating answers
            query_log_repo: Repository for logging queries
            document_repo: Repository for document operations
        """
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service
        self.query_log_repo = query_log_repo
        self.document_repo = document_repo

    async def answer_question(
        self,
        question: str,
        document_id: Optional[UUID] = None,
    ) -> RAGResponse:
        """
        Answer a question using RAG approach.

        Args:
            question: User's question
            document_id: Optional document ID to limit search

        Returns:
            RAGResponse with answer and metadata

        Raises:
            RAGSystemError: If answering fails
        """
        if not question or not question.strip():
            raise RAGSystemError("No se puede responder pregunta vacía")

        start_time = time.time()

        # Get document_id for logging (use provided or get first available)
        log_document_id = document_id
        if not log_document_id:
            log_document_id = await self._get_first_document_id()

        try:
            logger.info(f"answer_question called with question='{question[:50]}...', document_id={document_id}")

            # Retrieve relevant chunks
            logger.info("Calling retrieval_service.retrieve_relevant_chunks")
            chunks_with_scores = (
                await self.retrieval_service.retrieve_relevant_chunks(
                    query=question, document_id=document_id
                )
            )

            logger.info(f"Retrieved {len(chunks_with_scores)} chunks")

            # Check if we found any relevant context
            if not chunks_with_scores:
                logger.warning("No relevant chunks found for query")
                answer = "Lo siento, no encontré información relevante en el documento para responder tu pregunta."
                is_answerable = False
                chunk_ids = []
                tokens_used = 0

                # Log query even when no chunks found
                if log_document_id:
                    await self._log_query(
                        document_id=log_document_id,
                        question=question,
                        answer=answer,
                        is_answerable=is_answerable,
                        chunk_ids=chunk_ids,
                        response_time_ms=int((time.time() - start_time) * 1000),
                    )

                return RAGResponse(
                    answer=answer,
                    is_answerable=is_answerable,
                    retrieved_chunks_count=0,
                    tokens_used=tokens_used,
                    chunk_ids=chunk_ids,
                )

            # Format context from retrieved chunks
            context = format_context_from_chunks(chunks_with_scores)

            # Build prompt
            prompt = f"{SYSTEM_PROMPT_TEMPLATE}\n\nContexto:\n{context}\n\nPregunta: {question}"

            # Generate answer
            answer, tokens_used = self.llm_service.generate_answer(prompt)

            # Determine if question was answerable
            is_answerable = self.NOT_ANSWERABLE_PHRASE not in answer

            # Extract chunk IDs
            chunk_ids = [chunk.id for chunk, _ in chunks_with_scores]

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Log query to database
            if log_document_id:
                await self._log_query(
                    document_id=log_document_id,
                    question=question,
                    answer=answer,
                    is_answerable=is_answerable,
                    chunk_ids=chunk_ids,
                    response_time_ms=response_time_ms,
                )

            return RAGResponse(
                answer=answer,
                is_answerable=is_answerable,
                retrieved_chunks_count=len(chunks_with_scores),
                tokens_used=tokens_used,
                chunk_ids=chunk_ids,
            )

        except Exception as e:
            if isinstance(e, RAGSystemError):
                raise
            raise RAGSystemError(f"Error al responder pregunta: {str(e)}")

    async def _log_query(
        self,
        document_id: UUID,
        question: str,
        answer: str,
        is_answerable: bool,
        chunk_ids: list[UUID],
        response_time_ms: int,
    ):
        """
        Log query to database.

        Args:
            document_id: Document UUID
            question: User's question
            answer: Generated answer
            is_answerable: Whether question was answerable
            chunk_ids: List of chunk IDs used
            response_time_ms: Response time in milliseconds
        """
        try:
            query_log = QueryLog(
                document_id=document_id,
                query_text=question,
                answer_text=answer,
                retrieved_chunks=[str(chunk_id) for chunk_id in chunk_ids],
                is_answerable=is_answerable,
                response_time_ms=response_time_ms,
            )
            await self.query_log_repo.create(query_log)
            logger.info(f"Query logged successfully for document {document_id}")
        except Exception as e:
            # Don't fail the request if logging fails
            logger.error(f"Failed to log query: {str(e)}")

    async def _get_first_document_id(self) -> Optional[UUID]:
        """
        Get first available document ID for logging queries without document_id.

        Returns:
            First document UUID or None if no documents exist
        """
        try:
            documents = await self.document_repo.list_all(limit=1)
            if documents:
                return documents[0].id
            logger.warning("No documents found in database for query logging")
            return None
        except Exception as e:
            logger.error(f"Failed to get first document ID: {str(e)}")
            return None
