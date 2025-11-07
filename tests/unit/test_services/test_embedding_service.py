"""Tests for embedding service."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.services.embedding_service import EmbeddingService
from src.utils.exceptions import EmbeddingServiceError


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    with patch("src.services.embedding_service.OpenAI") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def embedding_service(mock_openai_client):
    """Create EmbeddingService with mocked OpenAI client."""
    return EmbeddingService(api_key="test-key", model="text-embedding-3-small")


def test_embed_text_returns_vector(embedding_service, mock_openai_client):
    """Test that embed_text returns a vector."""
    # Mock response
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
    mock_openai_client.embeddings.create.return_value = mock_response

    result = embedding_service.embed_text("test text")

    assert result == [0.1, 0.2, 0.3]
    assert isinstance(result, list)
    mock_openai_client.embeddings.create.assert_called_once()


def test_embed_text_calls_api_with_correct_params(embedding_service, mock_openai_client):
    """Test that embed_text calls OpenAI API with correct parameters."""
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1])]
    mock_openai_client.embeddings.create.return_value = mock_response

    embedding_service.embed_text("Spanish text")

    mock_openai_client.embeddings.create.assert_called_once_with(
        input="Spanish text", model="text-embedding-3-small"
    )


def test_embed_text_raises_error_for_empty_string(embedding_service):
    """Test that embed_text raises error for empty string."""
    with pytest.raises(EmbeddingServiceError) as exc_info:
        embedding_service.embed_text("")

    assert "texto vacío" in str(exc_info.value)


def test_embed_text_raises_error_on_api_failure(embedding_service, mock_openai_client):
    """Test that embed_text raises error on API failure."""
    mock_openai_client.embeddings.create.side_effect = Exception("API Error")

    with pytest.raises(EmbeddingServiceError) as exc_info:
        embedding_service.embed_text("test")

    assert "Error al generar embedding" in str(exc_info.value)


def test_embed_batch_returns_multiple_vectors(embedding_service, mock_openai_client):
    """Test that embed_batch returns multiple vectors."""
    mock_response = Mock()
    mock_response.data = [
        Mock(embedding=[0.1, 0.2]),
        Mock(embedding=[0.3, 0.4]),
        Mock(embedding=[0.5, 0.6]),
    ]
    mock_openai_client.embeddings.create.return_value = mock_response

    texts = ["text1", "text2", "text3"]
    result = embedding_service.embed_batch(texts)

    assert len(result) == 3
    assert result[0] == [0.1, 0.2]
    assert result[1] == [0.3, 0.4]
    assert result[2] == [0.5, 0.6]


def test_embed_batch_handles_empty_list(embedding_service):
    """Test that embed_batch handles empty list."""
    result = embedding_service.embed_batch([])
    assert result == []


def test_embed_batch_filters_empty_strings(embedding_service, mock_openai_client):
    """Test that embed_batch filters out empty strings."""
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1]), Mock(embedding=[0.2])]
    mock_openai_client.embeddings.create.return_value = mock_response

    texts = ["text1", "", "text2", "   "]
    result = embedding_service.embed_batch(texts)

    # Should only process non-empty texts
    assert len(result) == 2
    mock_openai_client.embeddings.create.assert_called_once()


def test_embed_batch_processes_in_batches(embedding_service, mock_openai_client):
    """Test that embed_batch processes large lists in batches."""
    # Mock to return correct number of embeddings per batch
    def create_mock_response(input, model):
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[float(i)]) for i in range(len(input))]
        return mock_response

    mock_openai_client.embeddings.create.side_effect = create_mock_response

    # Create 150 texts, should be processed in 2 batches (100 + 50)
    texts = [f"text{i}" for i in range(150)]
    result = embedding_service.embed_batch(texts, max_batch_size=100)

    # Should make 2 API calls
    assert mock_openai_client.embeddings.create.call_count == 2
    assert len(result) == 150


def test_embed_batch_raises_error_on_api_failure(embedding_service, mock_openai_client):
    """Test that embed_batch raises error on API failure."""
    mock_openai_client.embeddings.create.side_effect = Exception("API Error")

    with pytest.raises(EmbeddingServiceError) as exc_info:
        embedding_service.embed_batch(["text1", "text2"])

    assert "Error al generar embeddings en batch" in str(exc_info.value)


def test_embedding_service_uses_custom_model():
    """Test that EmbeddingService can use custom model."""
    with patch("src.services.embedding_service.OpenAI") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1])]
        mock_client.embeddings.create.return_value = mock_response

        service = EmbeddingService(api_key="test", model="custom-model")
        service.embed_text("test")

        mock_client.embeddings.create.assert_called_with(
            input="test", model="custom-model"
        )
