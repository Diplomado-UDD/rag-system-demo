"""Tests for custom exceptions."""

import pytest
from src.utils.exceptions import (
    DocumentNotFoundError,
    EmbeddingServiceError,
    FileSizeExceededError,
    InvalidFileTypeError,
    LLMServiceError,
    PDFProcessingError,
    RAGSystemError,
)


def test_document_not_found_error():
    """Test DocumentNotFoundError can be raised and caught."""
    with pytest.raises(DocumentNotFoundError):
        raise DocumentNotFoundError("Document not found")


def test_invalid_file_type_error():
    """Test InvalidFileTypeError can be raised and caught."""
    with pytest.raises(InvalidFileTypeError):
        raise InvalidFileTypeError("Invalid file type")


def test_file_size_exceeded_error():
    """Test FileSizeExceededError can be raised and caught."""
    with pytest.raises(FileSizeExceededError):
        raise FileSizeExceededError("File too large")


def test_pdf_processing_error():
    """Test PDFProcessingError can be raised and caught."""
    with pytest.raises(PDFProcessingError):
        raise PDFProcessingError("PDF processing failed")


def test_embedding_service_error():
    """Test EmbeddingServiceError can be raised and caught."""
    with pytest.raises(EmbeddingServiceError):
        raise EmbeddingServiceError("Embedding service error")


def test_llm_service_error():
    """Test LLMServiceError can be raised and caught."""
    with pytest.raises(LLMServiceError):
        raise LLMServiceError("LLM service error")


def test_all_exceptions_inherit_from_base():
    """Test all custom exceptions inherit from RAGSystemError."""
    assert issubclass(DocumentNotFoundError, RAGSystemError)
    assert issubclass(InvalidFileTypeError, RAGSystemError)
    assert issubclass(FileSizeExceededError, RAGSystemError)
    assert issubclass(PDFProcessingError, RAGSystemError)
    assert issubclass(EmbeddingServiceError, RAGSystemError)
    assert issubclass(LLMServiceError, RAGSystemError)
