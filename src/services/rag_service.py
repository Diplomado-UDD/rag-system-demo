"""RAG service orchestrating the complete question-answering flow."""

from typing import Optional
from uuid import UUID

from src.core.prompts import SYSTEM_PROMPT_TEMPLATE, format_context_from_chunks
from src.services.llm_service import LLMService
from src.services.retrieval_service import RetrievalService
from src.utils.exceptions import RAGSystemError


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
        self, retrieval_service: RetrievalService, llm_service: LLMService
    ):
        """
        Initialize RAG service.

        Args:
            retrieval_service: Service for retrieving relevant chunks
            llm_service: Service for generating answers
        """
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service

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

        try:
            # Retrieve relevant chunks
            chunks_with_scores = (
                await self.retrieval_service.retrieve_relevant_chunks(
                    query=question, document_id=document_id
                )
            )

            # Check if we found any relevant context
            if not chunks_with_scores:
                return RAGResponse(
                    answer="Lo siento, no encontré información relevante en el documento para responder tu pregunta.",
                    is_answerable=False,
                    retrieved_chunks_count=0,
                    tokens_used=0,
                    chunk_ids=[],
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
