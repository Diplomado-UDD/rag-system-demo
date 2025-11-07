"""Tests for text processing utilities."""

from src.utils.text_processing import clean_text, count_tokens


def test_clean_text_removes_extra_whitespace():
    """Test that clean_text removes extra whitespace."""
    text = "Este  es   un    texto   con    espacios"
    cleaned = clean_text(text)
    assert cleaned == "Este es un texto con espacios"


def test_clean_text_removes_newlines():
    """Test that clean_text replaces newlines with spaces."""
    text = "Línea 1\nLínea 2\n\nLínea 3"
    cleaned = clean_text(text)
    assert cleaned == "Línea 1 Línea 2 Línea 3"


def test_clean_text_removes_tabs():
    """Test that clean_text replaces tabs with spaces."""
    text = "Columna1\tColumna2\tColumna3"
    cleaned = clean_text(text)
    assert cleaned == "Columna1 Columna2 Columna3"


def test_clean_text_strips_leading_trailing():
    """Test that clean_text strips leading and trailing whitespace."""
    text = "   texto con espacios   \n"
    cleaned = clean_text(text)
    assert cleaned == "texto con espacios"


def test_clean_text_normalizes_unicode():
    """Test that clean_text normalizes Spanish characters."""
    text = "Niño, España, más información"
    cleaned = clean_text(text)
    # Should preserve Spanish characters
    assert "ñ" in cleaned
    assert "ó" in cleaned
    assert "á" in cleaned


def test_clean_text_chilean_spanish():
    """Test clean_text with Chilean Spanish phrases."""
    text = "   ¿Cuál  es  el   cacho?   "
    cleaned = clean_text(text)
    assert cleaned == "¿Cuál es el cacho?"


def test_count_tokens_simple_text():
    """Test token counting for simple text."""
    text = "Hello world"
    token_count = count_tokens(text)
    # Should be 2 tokens
    assert token_count == 2


def test_count_tokens_spanish_text():
    """Test token counting for Spanish text."""
    text = "El objetivo del proyecto es desarrollar un sistema RAG"
    token_count = count_tokens(text)
    # Should be > 0 tokens
    assert token_count > 0
    assert isinstance(token_count, int)


def test_count_tokens_empty_string():
    """Test token counting for empty string."""
    token_count = count_tokens("")
    assert token_count == 0


def test_count_tokens_with_model():
    """Test token counting with specific model."""
    text = "This is a test"
    gpt4_count = count_tokens(text, model="gpt-4")
    gpt35_count = count_tokens(text, model="gpt-3.5-turbo")

    # Both should return valid counts
    assert gpt4_count > 0
    assert gpt35_count > 0


def test_count_tokens_long_text():
    """Test token counting for longer text."""
    text = "Este es un documento más largo con múltiples oraciones. " * 10
    token_count = count_tokens(text)
    # Should have many tokens
    assert token_count > 50
