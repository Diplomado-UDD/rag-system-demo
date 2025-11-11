"""FastAPI dependencies for database and services."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings
from src.repositories.document_repo import DocumentRepository
from src.repositories.query_log_repo import QueryLogRepository
from src.repositories.vector_repo import VectorRepository
from src.services.chunking_service import ChunkingService
from src.services.embedding_service import EmbeddingService
from src.services.llm_service import LLMService
from src.services.pdf_service import PDFService
from src.services.rag_service import RAGService
from src.services.retrieval_service import RetrievalService

# Database engine (created once at startup)
_engine = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database_url, echo=False)
    return _engine


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for database session.

    Yields:
        AsyncSession instance
    """
    engine = get_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_document_repo(
    session: AsyncSession = Depends(get_db_session),
) -> DocumentRepository:
    """
    Dependency for document repository.

    Args:
        session: Database session from get_db_session

    Returns:
        DocumentRepository instance
    """
    return DocumentRepository(session)


async def get_vector_repo(
    session: AsyncSession = Depends(get_db_session),
) -> VectorRepository:
    """
    Dependency for vector repository.

    Args:
        session: Database session from get_db_session

    Returns:
        VectorRepository instance
    """
    return VectorRepository(session)


async def get_query_log_repo(
    session: AsyncSession = Depends(get_db_session),
) -> QueryLogRepository:
    """
    Dependency for query log repository.

    Args:
        session: Database session from get_db_session

    Returns:
        QueryLogRepository instance
    """
    return QueryLogRepository(session)


def get_pdf_service() -> PDFService:
    """
    Dependency for PDF service.

    Returns:
        PDFService instance
    """
    return PDFService()


def get_chunking_service() -> ChunkingService:
    """
    Dependency for chunking service.

    Returns:
        ChunkingService instance
    """
    settings = get_settings()
    return ChunkingService(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )


def get_embedding_service() -> EmbeddingService:
    """
    Dependency for embedding service.

    Returns:
        EmbeddingService instance
    """
    settings = get_settings()
    return EmbeddingService(
        api_key=settings.openai_api_key, model=settings.embedding_model
    )


def get_llm_service() -> LLMService:
    """
    Dependency for LLM service.

    Returns:
        LLMService instance
    """
    settings = get_settings()
    return LLMService(api_key=settings.openai_api_key, model=settings.llm_model)


async def get_retrieval_service(
    vector_repo: VectorRepository = Depends(get_vector_repo),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> RetrievalService:
    """
    Dependency for retrieval service.

    Args:
        vector_repo: Vector repository from get_vector_repo
        embedding_service: Embedding service from get_embedding_service

    Returns:
        RetrievalService instance
    """
    settings = get_settings()
    return RetrievalService(
        vector_repo=vector_repo,
        embedding_service=embedding_service,
        top_k=settings.top_k_results,
        min_similarity=settings.min_similarity_threshold,
    )


async def get_rag_service(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    llm_service: LLMService = Depends(get_llm_service),
    query_log_repo: QueryLogRepository = Depends(get_query_log_repo),
    document_repo: DocumentRepository = Depends(get_document_repo),
) -> RAGService:
    """
    Dependency for RAG service.

    Args:
        retrieval_service: Retrieval service from get_retrieval_service
        llm_service: LLM service from get_llm_service
        query_log_repo: Query log repository from get_query_log_repo
        document_repo: Document repository from get_document_repo

    Returns:
        RAGService instance
    """
    return RAGService(
        retrieval_service=retrieval_service,
        llm_service=llm_service,
        query_log_repo=query_log_repo,
        document_repo=document_repo,
    )
