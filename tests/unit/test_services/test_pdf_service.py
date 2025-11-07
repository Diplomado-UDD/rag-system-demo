"""Tests for PDF extraction service."""

import os
from pathlib import Path

import pytest

from src.services.pdf_service import PDFService
from src.utils.exceptions import PDFProcessingError


@pytest.fixture
def pdf_service():
    """Create PDFService instance."""
    return PDFService()


@pytest.fixture
def sample_pdf_path():
    """Path to sample test PDF."""
    return str(Path(__file__).parent.parent.parent / "fixtures" / "sample.pdf")


def test_extract_text_from_spanish_pdf(pdf_service, sample_pdf_path):
    """Test extraction from Spanish PDF file."""
    pages = pdf_service.extract_text_with_pages(sample_pdf_path)

    # Should have 2 pages
    assert len(pages) == 2

    # Page 1 should contain Spanish text
    assert "Documento de Prueba en Español" in pages[1]
    assert "sistema RAG" in pages[1]

    # Page 2 should contain project objectives
    assert "Objetivos del Proyecto" in pages[2]
    assert "español chileno" in pages[2]


def test_extract_preserves_page_numbers(pdf_service, sample_pdf_path):
    """Test that page numbers are correctly tracked."""
    pages = pdf_service.extract_text_with_pages(sample_pdf_path)

    # Pages should be 1-indexed
    assert 1 in pages
    assert 2 in pages
    assert 0 not in pages


def test_extract_returns_dict(pdf_service, sample_pdf_path):
    """Test that extract returns a dictionary."""
    result = pdf_service.extract_text_with_pages(sample_pdf_path)

    assert isinstance(result, dict)
    assert all(isinstance(k, int) for k in result.keys())
    assert all(isinstance(v, str) for v in result.values())


def test_extract_nonexistent_file_raises_error(pdf_service):
    """Test that extracting from nonexistent file raises error."""
    with pytest.raises(PDFProcessingError) as exc_info:
        pdf_service.extract_text_with_pages("/nonexistent/file.pdf")

    assert "No se pudo procesar" in str(exc_info.value)


def test_extract_strips_whitespace(pdf_service, sample_pdf_path):
    """Test that extracted text has whitespace stripped."""
    pages = pdf_service.extract_text_with_pages(sample_pdf_path)

    for text in pages.values():
        # No leading/trailing whitespace
        assert text == text.strip()
