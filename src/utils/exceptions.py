"""Custom exceptions for the RAG system."""


class RAGSystemError(Exception):
    """Base exception for RAG system errors."""

    pass


class DocumentNotFoundError(RAGSystemError):
    """Raised when a document is not found in the database."""

    pass


class InvalidFileTypeError(RAGSystemError):
    """Raised when an uploaded file has an invalid type."""

    pass


class FileSizeExceededError(RAGSystemError):
    """Raised when an uploaded file exceeds the maximum size limit."""

    pass


class PDFProcessingError(RAGSystemError):
    """Raised when PDF extraction or processing fails."""

    pass


class EmbeddingServiceError(RAGSystemError):
    """Raised when the embedding service encounters an error."""

    pass


class LLMServiceError(RAGSystemError):
    """Raised when the LLM service encounters an error."""

    pass
