"""Tests for file validation utilities."""

import pytest

from src.utils.exceptions import FileSizeExceededError, InvalidFileTypeError
from src.utils.validators import validate_file_size, validate_file_type


def test_validate_file_type_valid_pdf():
    """Test validation passes for valid PDF file."""
    # Should not raise exception
    validate_file_type("document.pdf")
    validate_file_type("document.PDF")  # Case insensitive
    validate_file_type("/path/to/document.pdf")


def test_validate_file_type_invalid_extension():
    """Test validation fails for invalid file type."""
    with pytest.raises(InvalidFileTypeError) as exc_info:
        validate_file_type("document.txt")

    assert "Solo se aceptan archivos" in str(exc_info.value)
    assert ".txt" in str(exc_info.value)


def test_validate_file_type_no_extension():
    """Test validation fails for file without extension."""
    with pytest.raises(InvalidFileTypeError) as exc_info:
        validate_file_type("document")

    assert "sin extensión" in str(exc_info.value)


def test_validate_file_type_custom_extensions():
    """Test validation with custom allowed extensions."""
    validate_file_type("document.docx", allowed_extensions=[".docx", ".pdf"])

    with pytest.raises(InvalidFileTypeError):
        validate_file_type("document.txt", allowed_extensions=[".docx", ".pdf"])


def test_validate_file_size_within_limit():
    """Test validation passes for file within size limit."""
    # 10 MB file
    file_size = 10 * 1024 * 1024
    validate_file_size(file_size, max_size_mb=50)


def test_validate_file_size_exceeds_limit():
    """Test validation fails for file exceeding size limit."""
    # 60 MB file
    file_size = 60 * 1024 * 1024

    with pytest.raises(FileSizeExceededError) as exc_info:
        validate_file_size(file_size, max_size_mb=50)

    assert "Tamaño máximo permitido: 50MB" in str(exc_info.value)
    assert "60.00MB" in str(exc_info.value)


def test_validate_file_size_exact_limit():
    """Test validation passes for file at exact size limit."""
    # Exactly 50 MB
    file_size = 50 * 1024 * 1024
    validate_file_size(file_size, max_size_mb=50)


def test_validate_file_size_custom_limit():
    """Test validation with custom size limit."""
    file_size = 5 * 1024 * 1024  # 5 MB

    # Should pass with 10 MB limit
    validate_file_size(file_size, max_size_mb=10)

    # Should fail with 2 MB limit
    with pytest.raises(FileSizeExceededError):
        validate_file_size(file_size, max_size_mb=2)
