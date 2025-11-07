"""Tests for retrieval service."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.models.chunk import Chunk
from src.services.retrieval_service import RetrievalService
from src.utils.exceptions import RAGSystemError


@pytest.fixture
def mock_vector_repo():
    """Create mock vector repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_embedding_service():
    """Create mock embedding service."""
    service = AsyncMock()
    service.embed_text = AsyncMock(return_value=[0.1] * 1536)
    return service


@pytest.fixture
def retrieval_service(mock_vector_repo, mock_embedding_service):
    """Create retrieval service with mocks."""
    return RetrievalService(
        vector_repo=mock_vector_repo,
        embedding_service=mock_embedding_service,
        top_k=5,
        min_similarity=0.7,
    )


@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_returns_results(
    retrieval_service, mock_vector_repo, mock_embedding_service
):
    """Test that retrieve_relevant_chunks returns results."""
    doc_id = uuid4()
    chunk = Chunk(
        id=uuid4(),
        document_id=doc_id,
        content="Test content",
        page_number=1,
        chunk_index=0,
        word_count=2,
    )
    mock_vector_repo.similarity_search.return_value = [(chunk, 0.85)]

    results = await retrieval_service.retrieve_relevant_chunks("test query")

    assert len(results) == 1
    assert results[0][0].content == "Test content"
    assert results[0][1] == 0.85
    mock_embedding_service.embed_text.assert_called_once_with("test query")


@pytest.mark.asyncio
async def test_retrieve_calls_vector_repo_with_correct_params(
    retrieval_service, mock_vector_repo, mock_embedding_service
):
    """Test that retrieve calls vector repository with correct parameters."""
    mock_vector_repo.similarity_search.return_value = []

    await retrieval_service.retrieve_relevant_chunks("test query", top_k=3, min_similarity=0.8)

    mock_vector_repo.similarity_search.assert_called_once()
    call_args = mock_vector_repo.similarity_search.call_args[1]
    assert call_args["top_k"] == 3
    assert call_args["min_score"] == 0.8
    assert call_args["document_id"] is None
    assert len(call_args["embedding"]) == 1536


@pytest.mark.asyncio
async def test_retrieve_with_document_id_filter(
    retrieval_service, mock_vector_repo, mock_embedding_service
):
    """Test retrieval with document ID filter."""
    doc_id = uuid4()
    mock_vector_repo.similarity_search.return_value = []

    await retrieval_service.retrieve_relevant_chunks("test query", document_id=doc_id)

    call_args = mock_vector_repo.similarity_search.call_args[1]
    assert call_args["document_id"] == doc_id


@pytest.mark.asyncio
async def test_retrieve_uses_default_parameters(
    retrieval_service, mock_vector_repo, mock_embedding_service
):
    """Test that retrieve uses default parameters when not specified."""
    mock_vector_repo.similarity_search.return_value = []

    await retrieval_service.retrieve_relevant_chunks("test query")

    call_args = mock_vector_repo.similarity_search.call_args[1]
    assert call_args["top_k"] == 5
    assert call_args["min_score"] == 0.7


@pytest.mark.asyncio
async def test_retrieve_raises_error_for_empty_query(retrieval_service):
    """Test that retrieve raises error for empty query."""
    with pytest.raises(RAGSystemError) as exc_info:
        await retrieval_service.retrieve_relevant_chunks("")

    assert "consulta vacía" in str(exc_info.value)


@pytest.mark.asyncio
async def test_retrieve_raises_error_for_whitespace_query(retrieval_service):
    """Test that retrieve raises error for whitespace-only query."""
    with pytest.raises(RAGSystemError) as exc_info:
        await retrieval_service.retrieve_relevant_chunks("   ")

    assert "consulta vacía" in str(exc_info.value)


@pytest.mark.asyncio
async def test_retrieve_handles_embedding_service_error(
    retrieval_service, mock_embedding_service
):
    """Test that retrieve handles embedding service errors."""
    mock_embedding_service.embed_text.side_effect = Exception("API error")

    with pytest.raises(RAGSystemError) as exc_info:
        await retrieval_service.retrieve_relevant_chunks("test query")

    assert "Error al recuperar chunks relevantes" in str(exc_info.value)


@pytest.mark.asyncio
async def test_retrieve_handles_vector_repo_error(
    retrieval_service, mock_vector_repo, mock_embedding_service
):
    """Test that retrieve handles vector repository errors."""
    mock_vector_repo.similarity_search.side_effect = Exception("Database error")

    with pytest.raises(RAGSystemError) as exc_info:
        await retrieval_service.retrieve_relevant_chunks("test query")

    assert "Error al recuperar chunks relevantes" in str(exc_info.value)


@pytest.mark.asyncio
async def test_retrieve_returns_multiple_chunks_ordered(
    retrieval_service, mock_vector_repo, mock_embedding_service
):
    """Test that retrieve returns multiple chunks in order."""
    doc_id = uuid4()
    chunks = [
        (
            Chunk(
                id=uuid4(),
                document_id=doc_id,
                content=f"Chunk {i}",
                page_number=i,
                chunk_index=i,
                word_count=2,
            ),
            0.9 - (i * 0.1),
        )
        for i in range(3)
    ]
    mock_vector_repo.similarity_search.return_value = chunks

    results = await retrieval_service.retrieve_relevant_chunks("test query")

    assert len(results) == 3
    assert results[0][1] == 0.9
    assert results[1][1] == 0.8
    assert results[2][1] == 0.7


@pytest.mark.asyncio
async def test_retrieve_returns_empty_when_no_matches(
    retrieval_service, mock_vector_repo, mock_embedding_service
):
    """Test that retrieve returns empty list when no matches found."""
    mock_vector_repo.similarity_search.return_value = []

    results = await retrieval_service.retrieve_relevant_chunks("test query")

    assert len(results) == 0
