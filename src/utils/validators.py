"""File validation utilities."""

import os
from pathlib import Path

from src.utils.exceptions import FileSizeExceededError, InvalidFileTypeError


def validate_file_type(filename: str, allowed_extensions: list[str] = None) -> None:
    """
    Validate that the file has an allowed extension.

    Args:
        filename: Name of the file to validate
        allowed_extensions: List of allowed extensions (e.g., [".pdf"])

    Raises:
        InvalidFileTypeError: If file extension is not allowed
    """
    if allowed_extensions is None:
        allowed_extensions = [".pdf"]

    file_ext = Path(filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise InvalidFileTypeError(
            f"Solo se aceptan archivos {', '.join(allowed_extensions)}. "
            f"Recibido: {file_ext or 'sin extensión'}"
        )


def validate_file_size(file_size: int, max_size_mb: int = 50) -> None:
    """
    Validate that the file size does not exceed the maximum allowed.

    Args:
        file_size: Size of the file in bytes
        max_size_mb: Maximum allowed size in megabytes

    Raises:
        FileSizeExceededError: If file size exceeds the limit
    """
    max_size_bytes = max_size_mb * 1024 * 1024

    if file_size > max_size_bytes:
        actual_mb = file_size / (1024 * 1024)
        raise FileSizeExceededError(
            f"Tamaño máximo permitido: {max_size_mb}MB. "
            f"Archivo recibido: {actual_mb:.2f}MB"
        )
