"""PDF text extraction service."""

from pathlib import Path
from typing import Dict

import pdfplumber
import PyPDF2

from src.utils.exceptions import PDFProcessingError


class PDFService:
    """Service for extracting text from PDF files."""

    def extract_text_with_pages(self, file_path: str) -> Dict[int, str]:
        """
        Extract text from PDF with page numbers.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary mapping page number (1-indexed) to extracted text

        Raises:
            PDFProcessingError: If PDF extraction fails
        """
        try:
            # Try pdfplumber first (better text extraction)
            return self._extract_with_pdfplumber(file_path)
        except Exception as e:
            # Fallback to PyPDF2
            try:
                return self._extract_with_pypdf2(file_path)
            except Exception as fallback_error:
                raise PDFProcessingError(
                    f"No se pudo procesar el archivo PDF. "
                    f"Error principal: {str(e)}. "
                    f"Error alternativo: {str(fallback_error)}"
                )

    def _extract_with_pdfplumber(self, file_path: str) -> Dict[int, str]:
        """Extract text using pdfplumber."""
        pages_text = {}

        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) == 0:
                raise PDFProcessingError("El PDF está vacío (0 páginas)")

            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    pages_text[page_num] = text.strip()
                else:
                    pages_text[page_num] = ""

        return pages_text

    def _extract_with_pypdf2(self, file_path: str) -> Dict[int, str]:
        """Extract text using PyPDF2 as fallback."""
        pages_text = {}

        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)

            if len(reader.pages) == 0:
                raise PDFProcessingError("El PDF está vacío (0 páginas)")

            if reader.is_encrypted:
                raise PDFProcessingError("El PDF está encriptado y no se puede procesar")

            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text:
                    pages_text[page_num + 1] = text.strip()
                else:
                    pages_text[page_num + 1] = ""

        return pages_text
