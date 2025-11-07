"""Text chunking service for splitting documents into semantic chunks."""

from typing import Dict, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.utils.text_processing import clean_text, count_tokens


class ChunkingService:
    """Service for splitting text into semantic chunks with overlap."""

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        """
        Initialize chunking service.

        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Number of tokens to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(
        self, pages_dict: Dict[int, str], chunk_size: int = None, overlap: int = None
    ) -> List[Dict]:
        """
        Split text into chunks preserving page numbers.

        Args:
            pages_dict: Dictionary mapping page number to text
            chunk_size: Override default chunk size
            overlap: Override default overlap

        Returns:
            List of dictionaries with keys:
                - content: chunk text
                - page_number: source page number
                - chunk_index: index of chunk in document
                - word_count: number of words in chunk
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap

        # Create text splitter (using character-based approximation)
        # Approximate 1 token ≈ 4 characters
        char_chunk_size = chunk_size * 4
        char_overlap = overlap * 4

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=char_chunk_size,
            chunk_overlap=char_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        chunks = []
        chunk_index = 0

        for page_num in sorted(pages_dict.keys()):
            page_text = pages_dict[page_num]

            if not page_text.strip():
                continue

            # Clean the text
            cleaned_text = clean_text(page_text)

            # Split into chunks
            page_chunks = splitter.split_text(cleaned_text)

            for chunk_text in page_chunks:
                if not chunk_text.strip():
                    continue

                chunks.append(
                    {
                        "content": chunk_text.strip(),
                        "page_number": page_num,
                        "chunk_index": chunk_index,
                        "word_count": len(chunk_text.split()),
                    }
                )
                chunk_index += 1

        return chunks
