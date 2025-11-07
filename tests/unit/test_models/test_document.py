"""Tests for Document model."""

from datetime import datetime
from uuid import UUID

from src.models.document import Document, DocumentStatus


def test_document_model_instantiation():
    """Test that Document model can be instantiated."""
    doc = Document(
        filename="test.pdf",
        file_size=1024,
        status=DocumentStatus.uploading,
    )

    assert doc.filename == "test.pdf"
    assert doc.file_size == 1024
    assert doc.status == DocumentStatus.uploading
    assert doc.error_message is None
    assert doc.total_pages is None
    assert doc.total_chunks is None


def test_document_status_enum():
    """Test DocumentStatus enum values."""
    assert DocumentStatus.uploading.value == "uploading"
    assert DocumentStatus.processing.value == "processing"
    assert DocumentStatus.ready.value == "ready"
    assert DocumentStatus.failed.value == "failed"


def test_document_repr():
    """Test Document __repr__ method."""
    doc = Document(
        filename="test.pdf",
        file_size=1024,
        status=DocumentStatus.ready,
    )
    doc.id = UUID("12345678-1234-5678-1234-567812345678")

    repr_str = repr(doc)
    assert "Document" in repr_str
    assert "test.pdf" in repr_str
    assert "ready" in repr_str
