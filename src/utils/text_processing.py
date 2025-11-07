"""Text processing utilities for cleaning and token counting."""

import re
import unicodedata

import tiktoken


def clean_text(text: str) -> str:
    """
    Clean text by normalizing unicode and removing extra whitespace.

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text with normalized spacing and unicode
    """
    # Normalize unicode (NFD -> NFC for Spanish characters)
    text = unicodedata.normalize("NFC", text)

    # Replace multiple whitespace with single space
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in text for a given model.

    Args:
        text: Text to count tokens for
        model: Model name for tokenization (default: gpt-4)

    Returns:
        Number of tokens in the text
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for unknown models
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)
    return len(tokens)
