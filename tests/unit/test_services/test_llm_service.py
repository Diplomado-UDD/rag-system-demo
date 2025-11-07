"""Tests for LLM service."""

from unittest.mock import Mock, patch

import pytest

from src.services.llm_service import LLMService
from src.utils.exceptions import LLMServiceError


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    with patch("src.services.llm_service.OpenAI") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def llm_service(mock_openai_client):
    """Create LLMService with mocked OpenAI client."""
    return LLMService(api_key="test-key", model="gpt-4-turbo-preview")


def test_generate_answer_returns_text_and_tokens(llm_service, mock_openai_client):
    """Test that generate_answer returns response text and token count."""
    # Mock response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Esta es la respuesta"))]
    mock_response.usage = Mock(total_tokens=150)
    mock_openai_client.chat.completions.create.return_value = mock_response

    text, tokens = llm_service.generate_answer("Test prompt")

    assert text == "Esta es la respuesta"
    assert tokens == 150


def test_generate_answer_calls_api_with_correct_params(llm_service, mock_openai_client):
    """Test that generate_answer calls OpenAI API with correct parameters."""
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Respuesta"))]
    mock_response.usage = Mock(total_tokens=100)
    mock_openai_client.chat.completions.create.return_value = mock_response

    llm_service.generate_answer("Test prompt")

    mock_openai_client.chat.completions.create.assert_called_once_with(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": "Test prompt"}],
        temperature=0.1,
        max_tokens=1000,
    )


def test_generate_answer_raises_error_for_empty_prompt(llm_service):
    """Test that generate_answer raises error for empty prompt."""
    with pytest.raises(LLMServiceError) as exc_info:
        llm_service.generate_answer("")

    assert "prompt vacío" in str(exc_info.value)


def test_generate_answer_raises_error_on_api_failure(llm_service, mock_openai_client):
    """Test that generate_answer raises error on API failure."""
    mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

    with pytest.raises(LLMServiceError) as exc_info:
        llm_service.generate_answer("test prompt")

    assert "Error al generar respuesta del LLM" in str(exc_info.value)


def test_generate_answer_with_spanish_prompt(llm_service, mock_openai_client):
    """Test generate_answer with Spanish prompt."""
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="El objetivo es desarrollar un sistema RAG"))
    ]
    mock_response.usage = Mock(total_tokens=200)
    mock_openai_client.chat.completions.create.return_value = mock_response

    prompt = "¿Cuál es el objetivo del proyecto?"
    text, tokens = llm_service.generate_answer(prompt)

    assert "RAG" in text
    assert tokens > 0


def test_llm_service_uses_custom_parameters():
    """Test that LLMService can use custom parameters."""
    with patch("src.services.llm_service.OpenAI") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test"))]
        mock_response.usage = Mock(total_tokens=50)
        mock_client.chat.completions.create.return_value = mock_response

        service = LLMService(
            api_key="test",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=500,
        )
        service.generate_answer("test")

        mock_client.chat.completions.create.assert_called_with(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            temperature=0.5,
            max_tokens=500,
        )


def test_generate_answer_handles_long_response(llm_service, mock_openai_client):
    """Test that generate_answer handles long responses."""
    long_response = "Esta es una respuesta muy larga. " * 100
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content=long_response))]
    mock_response.usage = Mock(total_tokens=500)
    mock_openai_client.chat.completions.create.return_value = mock_response

    text, tokens = llm_service.generate_answer("prompt")

    assert len(text) > 100
    assert tokens == 500
