"""Tests for Spanish prompt templates."""

from uuid import uuid4

from src.core.prompts import (
    REFUSAL_MESSAGE,
    SYSTEM_PROMPT_TEMPLATE,
    format_context_from_chunks,
    format_prompt,
)
from src.models.chunk import Chunk


def test_system_prompt_template_has_context_placeholder():
    """Test that system prompt has context placeholder."""
    assert "{context}" in SYSTEM_PROMPT_TEMPLATE


def test_system_prompt_template_in_spanish():
    """Test that system prompt is in Spanish."""
    assert "español" in SYSTEM_PROMPT_TEMPLATE.lower()
    assert "pregunta" in SYSTEM_PROMPT_TEMPLATE.lower()
    assert "contexto" in SYSTEM_PROMPT_TEMPLATE.lower()


def test_system_prompt_has_hallucination_prevention():
    """Test that system prompt prevents hallucinations."""
    assert "NO inventes" in SYSTEM_PROMPT_TEMPLATE
    assert "EXCLUSIVAMENTE" in SYSTEM_PROMPT_TEMPLATE
    assert "ÚNICAMENTE" in SYSTEM_PROMPT_TEMPLATE


def test_system_prompt_requires_citations():
    """Test that system prompt requires page citations."""
    assert "Página" in SYSTEM_PROMPT_TEMPLATE
    assert "páginas de referencia" in SYSTEM_PROMPT_TEMPLATE.lower()


def test_format_prompt_includes_context():
    """Test that format_prompt includes context."""
    context = "El proyecto tiene como objetivo crear un sistema RAG."
    question = "¿Cuál es el objetivo del proyecto?"

    prompt = format_prompt(context, question)

    assert context in prompt
    assert question in prompt


def test_format_prompt_includes_question():
    """Test that format_prompt includes question."""
    context = "Contexto de prueba"
    question = "¿Cuál es la respuesta?"

    prompt = format_prompt(context, question)

    assert "PREGUNTA:" in prompt
    assert question in prompt


def test_format_prompt_spanish_structure():
    """Test that formatted prompt has Spanish structure."""
    context = "Información del documento"
    question = "¿Qué dice el documento?"

    prompt = format_prompt(context, question)

    assert "PREGUNTA:" in prompt
    assert "RESPUESTA:" in prompt


def test_format_context_from_chunks_single_chunk():
    """Test formatting context from single chunk."""
    doc_id = uuid4()
    chunk = Chunk(
        id=uuid4(),
        document_id=doc_id,
        content="Este es el contenido",
        page_number=5,
        chunk_index=0,
        word_count=4,
    )
    chunks_with_scores = [(chunk, 0.95)]

    context = format_context_from_chunks(chunks_with_scores)

    assert "Fragmento 1" in context
    assert "Página 5" in context
    assert "Este es el contenido" in context


def test_format_context_from_chunks_multiple_chunks():
    """Test formatting context from multiple chunks."""
    doc_id = uuid4()
    chunks_with_scores = [
        (
            Chunk(
                id=uuid4(),
                document_id=doc_id,
                content="Primer fragmento",
                page_number=1,
                chunk_index=0,
                word_count=2,
            ),
            0.95,
        ),
        (
            Chunk(
                id=uuid4(),
                document_id=doc_id,
                content="Segundo fragmento",
                page_number=2,
                chunk_index=1,
                word_count=2,
            ),
            0.85,
        ),
        (
            Chunk(
                id=uuid4(),
                document_id=doc_id,
                content="Tercer fragmento",
                page_number=3,
                chunk_index=2,
                word_count=2,
            ),
            0.75,
        ),
    ]

    context = format_context_from_chunks(chunks_with_scores)

    assert "Fragmento 1" in context
    assert "Fragmento 2" in context
    assert "Fragmento 3" in context
    assert "Página 1" in context
    assert "Página 2" in context
    assert "Página 3" in context


def test_format_context_from_chunks_empty():
    """Test formatting context with no chunks."""
    chunks = []

    context = format_context_from_chunks(chunks)

    assert "No se encontró información relevante" in context


def test_format_context_preserves_spanish_text():
    """Test that context formatting preserves Spanish characters."""
    doc_id = uuid4()
    chunks_with_scores = [
        (
            Chunk(
                id=uuid4(),
                document_id=doc_id,
                content="Información sobre el año pasado",
                page_number=1,
                chunk_index=0,
                word_count=5,
            ),
            0.9,
        ),
        (
            Chunk(
                id=uuid4(),
                document_id=doc_id,
                content="El niño comió mañana",
                page_number=2,
                chunk_index=1,
                word_count=4,
            ),
            0.8,
        ),
    ]

    context = format_context_from_chunks(chunks_with_scores)

    assert "ñ" in context
    assert "ó" in context


def test_refusal_message_in_spanish():
    """Test that refusal message is in Spanish."""
    assert "Lo siento" in REFUSAL_MESSAGE
    assert "no se encuentra en el documento" in REFUSAL_MESSAGE
    assert "reformular" in REFUSAL_MESSAGE


def test_refusal_message_suggests_rephrase():
    """Test that refusal message suggests rephrasing."""
    assert "reformular" in REFUSAL_MESSAGE or "otra" in REFUSAL_MESSAGE
