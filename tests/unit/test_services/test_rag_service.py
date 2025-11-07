"""Tests for RAG service."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.models.chunk import Chunk
from src.services.rag_service import RAGService
from src.utils.exceptions import RAGSystemError


@pytest.fixture
def mock_retrieval_service():
    """Create mock retrieval service."""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    from unittest.mock import Mock

    service = Mock()
    return service


@pytest.fixture
def rag_service(mock_retrieval_service, mock_llm_service):
    """Create RAG service with mocks."""
    return RAGService(
        retrieval_service=mock_retrieval_service, llm_service=mock_llm_service
    )


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing."""
    doc_id = uuid4()
    return [
        (
            Chunk(
                id=uuid4(),
                document_id=doc_id,
                content="El sistema RAG combina recuperación y generación.",
                page_number=1,
                chunk_index=0,
                word_count=7,
            ),
            0.92,
        ),
        (
            Chunk(
                id=uuid4(),
                document_id=doc_id,
                content="La búsqueda por similitud usa embeddings vectoriales.",
                page_number=2,
                chunk_index=1,
                word_count=6,
            ),
            0.85,
        ),
    ]


@pytest.mark.asyncio
async def test_answer_question_returns_response(
    rag_service, mock_retrieval_service, mock_llm_service, sample_chunks
):
    """Test that answer_question returns a complete response."""
    mock_retrieval_service.retrieve_relevant_chunks.return_value = sample_chunks
    mock_llm_service.generate_answer.return_value = (
        "El sistema RAG combina recuperación y generación usando embeddings. [Página 1, 2]",
        250,
    )

    response = await rag_service.answer_question("¿Qué es RAG?")

    assert response.answer is not None
    assert response.is_answerable is True
    assert response.retrieved_chunks_count == 2
    assert response.tokens_used == 250
    assert len(response.chunk_ids) == 2


@pytest.mark.asyncio
async def test_answer_question_calls_retrieval_service(
    rag_service, mock_retrieval_service, mock_llm_service, sample_chunks
):
    """Test that answer_question calls retrieval service correctly."""
    mock_retrieval_service.retrieve_relevant_chunks.return_value = sample_chunks
    mock_llm_service.generate_answer.return_value = ("Respuesta", 100)

    await rag_service.answer_question("test question")

    mock_retrieval_service.retrieve_relevant_chunks.assert_called_once_with(
        query="test question", document_id=None
    )


@pytest.mark.asyncio
async def test_answer_question_with_document_id(
    rag_service, mock_retrieval_service, mock_llm_service, sample_chunks
):
    """Test answer_question with document ID filter."""
    doc_id = uuid4()
    mock_retrieval_service.retrieve_relevant_chunks.return_value = sample_chunks
    mock_llm_service.generate_answer.return_value = ("Respuesta", 100)

    await rag_service.answer_question("test", document_id=doc_id)

    mock_retrieval_service.retrieve_relevant_chunks.assert_called_once_with(
        query="test", document_id=doc_id
    )


@pytest.mark.asyncio
async def test_answer_question_builds_prompt_with_context(
    rag_service, mock_retrieval_service, mock_llm_service, sample_chunks
):
    """Test that answer_question builds prompt with context."""
    mock_retrieval_service.retrieve_relevant_chunks.return_value = sample_chunks
    mock_llm_service.generate_answer.return_value = ("Respuesta", 100)

    await rag_service.answer_question("¿Qué es RAG?")

    # Check that LLM was called with a prompt containing the question
    call_args = mock_llm_service.generate_answer.call_args[0]
    prompt = call_args[0]
    assert "¿Qué es RAG?" in prompt
    assert "El sistema RAG" in prompt
    assert "Página 1" in prompt


@pytest.mark.asyncio
async def test_answer_question_no_chunks_found(
    rag_service, mock_retrieval_service, mock_llm_service
):
    """Test answer_question when no relevant chunks are found."""
    mock_retrieval_service.retrieve_relevant_chunks.return_value = []

    response = await rag_service.answer_question("irrelevant question")

    assert response.is_answerable is False
    assert response.retrieved_chunks_count == 0
    assert response.tokens_used == 0
    assert "no encontré información relevante" in response.answer
    mock_llm_service.generate_answer.assert_not_called()


@pytest.mark.asyncio
async def test_answer_question_detects_not_answerable(
    rag_service, mock_retrieval_service, mock_llm_service, sample_chunks
):
    """Test that answer_question detects when LLM says it cannot answer."""
    mock_retrieval_service.retrieve_relevant_chunks.return_value = sample_chunks
    mock_llm_service.generate_answer.return_value = (
        "Lo siento, esa información no se encuentra en el documento.",
        50,
    )

    response = await rag_service.answer_question("¿Cuál es el precio?")

    assert response.is_answerable is False
    assert response.retrieved_chunks_count == 2
    assert response.tokens_used == 50


@pytest.mark.asyncio
async def test_answer_question_raises_error_for_empty_question(rag_service):
    """Test that answer_question raises error for empty question."""
    with pytest.raises(RAGSystemError) as exc_info:
        await rag_service.answer_question("")

    assert "pregunta vacía" in str(exc_info.value)


@pytest.mark.asyncio
async def test_answer_question_raises_error_for_whitespace_question(rag_service):
    """Test that answer_question raises error for whitespace question."""
    with pytest.raises(RAGSystemError) as exc_info:
        await rag_service.answer_question("   ")

    assert "pregunta vacía" in str(exc_info.value)


@pytest.mark.asyncio
async def test_answer_question_handles_retrieval_error(
    rag_service, mock_retrieval_service
):
    """Test that answer_question handles retrieval errors."""
    mock_retrieval_service.retrieve_relevant_chunks.side_effect = Exception(
        "Retrieval failed"
    )

    with pytest.raises(RAGSystemError) as exc_info:
        await rag_service.answer_question("test")

    assert "Error al responder pregunta" in str(exc_info.value)


@pytest.mark.asyncio
async def test_answer_question_handles_llm_error(
    rag_service, mock_retrieval_service, mock_llm_service, sample_chunks
):
    """Test that answer_question handles LLM errors."""
    mock_retrieval_service.retrieve_relevant_chunks.return_value = sample_chunks
    mock_llm_service.generate_answer.side_effect = Exception("LLM failed")

    with pytest.raises(RAGSystemError) as exc_info:
        await rag_service.answer_question("test")

    assert "Error al responder pregunta" in str(exc_info.value)


@pytest.mark.asyncio
async def test_answer_question_extracts_chunk_ids(
    rag_service, mock_retrieval_service, mock_llm_service, sample_chunks
):
    """Test that answer_question extracts chunk IDs correctly."""
    mock_retrieval_service.retrieve_relevant_chunks.return_value = sample_chunks
    mock_llm_service.generate_answer.return_value = ("Respuesta", 100)

    response = await rag_service.answer_question("test")

    assert len(response.chunk_ids) == 2
    assert response.chunk_ids[0] == sample_chunks[0][0].id
    assert response.chunk_ids[1] == sample_chunks[1][0].id


@pytest.mark.asyncio
async def test_rag_response_initialization():
    """Test RAGResponse initialization."""
    from src.services.rag_service import RAGResponse

    chunk_ids = [uuid4(), uuid4()]
    response = RAGResponse(
        answer="Test answer",
        is_answerable=True,
        retrieved_chunks_count=5,
        tokens_used=150,
        chunk_ids=chunk_ids,
    )

    assert response.answer == "Test answer"
    assert response.is_answerable is True
    assert response.retrieved_chunks_count == 5
    assert response.tokens_used == 150
    assert response.chunk_ids == chunk_ids
