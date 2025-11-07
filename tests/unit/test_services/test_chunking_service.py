"""Tests for chunking service."""

import pytest

from src.services.chunking_service import ChunkingService


@pytest.fixture
def chunking_service():
    """Create ChunkingService instance."""
    return ChunkingService(chunk_size=100, chunk_overlap=20)


def test_chunk_text_basic(chunking_service):
    """Test basic text chunking."""
    pages_dict = {
        1: "Este es un texto de prueba. Contiene varias oraciones. Debe ser dividido.",
        2: "Esta es la segunda página con más contenido para procesar.",
    }

    chunks = chunking_service.chunk_text(pages_dict)

    # Should have chunks
    assert len(chunks) > 0

    # Each chunk should have required fields
    for chunk in chunks:
        assert "content" in chunk
        assert "page_number" in chunk
        assert "chunk_index" in chunk
        assert "word_count" in chunk


def test_chunk_preserves_page_numbers(chunking_service):
    """Test that chunks preserve source page numbers."""
    pages_dict = {
        1: "Contenido de la página uno.",
        2: "Contenido de la página dos.",
        3: "Contenido de la página tres.",
    }

    chunks = chunking_service.chunk_text(pages_dict)

    # Should have chunks from all pages
    page_numbers = {chunk["page_number"] for chunk in chunks}
    assert 1 in page_numbers
    assert 2 in page_numbers
    assert 3 in page_numbers


def test_chunk_index_sequential(chunking_service):
    """Test that chunk indexes are sequential."""
    pages_dict = {
        1: "Texto corto página uno.",
        2: "Texto corto página dos.",
    }

    chunks = chunking_service.chunk_text(pages_dict)

    # Indexes should be sequential starting from 0
    indexes = [chunk["chunk_index"] for chunk in chunks]
    assert indexes == list(range(len(chunks)))


def test_chunk_word_count_accurate(chunking_service):
    """Test that word count is accurate."""
    pages_dict = {1: "uno dos tres cuatro cinco"}

    chunks = chunking_service.chunk_text(pages_dict)

    assert len(chunks) == 1
    assert chunks[0]["word_count"] == 5


def test_chunk_skips_empty_pages(chunking_service):
    """Test that empty pages are skipped."""
    pages_dict = {1: "Contenido válido", 2: "", 3: "   ", 4: "Más contenido"}

    chunks = chunking_service.chunk_text(pages_dict)

    # Should only have chunks from pages 1 and 4
    page_numbers = {chunk["page_number"] for chunk in chunks}
    assert 1 in page_numbers
    assert 4 in page_numbers
    assert 2 not in page_numbers
    assert 3 not in page_numbers


def test_chunk_cleans_text(chunking_service):
    """Test that text is cleaned during chunking."""
    pages_dict = {1: "Texto  con    espacios    extras\n\n\ny   saltos"}

    chunks = chunking_service.chunk_text(pages_dict)

    # Extra whitespace should be normalized
    assert chunks[0]["content"] == "Texto con espacios extras y saltos"


def test_chunk_long_text_splits(chunking_service):
    """Test that long text is split into multiple chunks."""
    # Create a long text
    long_text = " ".join(["palabra"] * 500)
    pages_dict = {1: long_text}

    chunks = chunking_service.chunk_text(pages_dict)

    # Should create multiple chunks
    assert len(chunks) > 1


def test_chunk_custom_size():
    """Test chunking with custom size parameters."""
    service = ChunkingService(chunk_size=50, chunk_overlap=10)

    pages_dict = {1: " ".join(["test"] * 200)}

    chunks = service.chunk_text(pages_dict)

    # Should have multiple smaller chunks
    assert len(chunks) > 2


def test_chunk_spanish_text(chunking_service):
    """Test chunking with Spanish text."""
    pages_dict = {
        1: "El objetivo del proyecto es desarrollar un sistema RAG "
        "que responda preguntas en español chileno.",
        2: "El sistema debe procesar documentos PDF y extraer información relevante.",
    }

    chunks = chunking_service.chunk_text(pages_dict)

    # Should successfully chunk Spanish text
    assert len(chunks) > 0

    # Spanish characters should be preserved
    combined_text = " ".join(chunk["content"] for chunk in chunks)
    assert "ñ" in combined_text or "á" in combined_text
