"""Tests for Chunk model."""

from uuid import UUID, uuid4

from src.models.chunk import Chunk


def test_chunk_model_instantiation():
    """Test that Chunk model can be instantiated."""
    doc_id = uuid4()
    chunk = Chunk(
        document_id=doc_id,
        content="This is a test chunk of text.",
        page_number=1,
        chunk_index=0,
        word_count=7,
    )

    assert chunk.document_id == doc_id
    assert chunk.content == "This is a test chunk of text."
    assert chunk.page_number == 1
    assert chunk.chunk_index == 0
    assert chunk.word_count == 7
    assert chunk.embedding is None


def test_chunk_with_embedding():
    """Test Chunk with embedding vector."""
    doc_id = uuid4()
    embedding = [0.1] * 1536  # 1536-dimensional vector

    chunk = Chunk(
        document_id=doc_id,
        content="Test content",
        embedding=embedding,
        page_number=1,
        chunk_index=0,
        word_count=2,
    )

    assert chunk.embedding == embedding
    assert len(chunk.embedding) == 1536


def test_chunk_repr():
    """Test Chunk __repr__ method."""
    doc_id = UUID("12345678-1234-5678-1234-567812345678")
    chunk = Chunk(
        document_id=doc_id,
        content="Test",
        page_number=5,
        chunk_index=2,
        word_count=1,
    )
    chunk.id = UUID("87654321-4321-8765-4321-876543218765")

    repr_str = repr(chunk)
    assert "Chunk" in repr_str
    assert "87654321-4321-8765-4321-876543218765" in repr_str
    assert "page=5" in repr_str
