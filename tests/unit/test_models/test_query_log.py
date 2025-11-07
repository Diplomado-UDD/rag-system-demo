"""Tests for QueryLog model."""

from uuid import UUID, uuid4

from src.models.query_log import QueryLog


def test_query_log_model_instantiation():
    """Test that QueryLog model can be instantiated."""
    doc_id = uuid4()
    query_log = QueryLog(
        document_id=doc_id,
        query_text="¿Cuál es el objetivo del proyecto?",
        answer_text="El objetivo del proyecto es...",
        retrieved_chunks=[{"chunk_id": "abc", "score": 0.9}],
        is_answerable=True,
        response_time_ms=1500,
    )

    assert query_log.document_id == doc_id
    assert query_log.query_text == "¿Cuál es el objetivo del proyecto?"
    assert query_log.answer_text == "El objetivo del proyecto es..."
    assert query_log.is_answerable is True
    assert query_log.response_time_ms == 1500
    assert len(query_log.retrieved_chunks) == 1


def test_query_log_unanswerable():
    """Test QueryLog with unanswerable query."""
    doc_id = uuid4()
    query_log = QueryLog(
        document_id=doc_id,
        query_text="¿Cuántos años tiene el presidente?",
        answer_text="Lo siento, esa información no se encuentra en el documento.",
        retrieved_chunks=[],
        is_answerable=False,
        response_time_ms=800,
    )

    assert query_log.is_answerable is False
    assert query_log.retrieved_chunks == []


def test_query_log_repr():
    """Test QueryLog __repr__ method."""
    query_log = QueryLog(
        document_id=uuid4(),
        query_text="Test query",
        answer_text="Test answer",
        is_answerable=True,
        response_time_ms=1000,
    )
    query_log.id = UUID("12345678-1234-5678-1234-567812345678")

    repr_str = repr(query_log)
    assert "QueryLog" in repr_str
    assert "is_answerable=True" in repr_str
