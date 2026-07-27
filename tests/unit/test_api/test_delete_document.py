"""Tests for document deletion endpoint."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.api.routes.documents import delete_document
from src.models.document import Document, DocumentStatus


@pytest.mark.asyncio
async def test_delete_document_removes_query_logs_before_document():
    """Deleting a document must clear query_logs to avoid FK violation."""
    document_id = uuid4()
    document = Document(
        id=document_id,
        filename="test.pdf",
        file_size=1000,
        status=DocumentStatus.ready,
    )

    session = AsyncMock()
    document_repo = AsyncMock()
    document_repo.session = session
    document_repo.get_by_id.return_value = document
    document_repo.delete = AsyncMock()

    vector_repo = AsyncMock()
    vector_repo.delete_chunks_by_document_id = AsyncMock()

    query_log_repo = AsyncMock()
    query_log_repo.delete_by_document_id = AsyncMock()

    result = await delete_document(
        document_id=document_id,
        document_repo=document_repo,
        vector_repo=vector_repo,
        query_log_repo=query_log_repo,
    )

    assert result is None
    query_log_repo.delete_by_document_id.assert_awaited_once_with(document_id, commit=False)
    vector_repo.delete_chunks_by_document_id.assert_awaited_once_with(document_id, commit=False)
    document_repo.delete.assert_awaited_once_with(document, commit=False)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_document_not_found_raises_404():
    """Deleting a missing document returns 404."""
    document_repo = AsyncMock()
    document_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await delete_document(
            document_id=uuid4(),
            document_repo=document_repo,
            vector_repo=AsyncMock(),
            query_log_repo=AsyncMock(),
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_query_log_repo_delete_by_document_id_executes_delete():
    """QueryLogRepository.delete_by_document_id issues a filtered delete."""
    from sqlalchemy.sql.dml import Delete

    from src.repositories.query_log_repo import QueryLogRepository

    document_id = uuid4()
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()

    repo = QueryLogRepository(session)
    await repo.delete_by_document_id(document_id)

    session.execute.assert_awaited_once()
    statement = session.execute.await_args.args[0]
    assert isinstance(statement, Delete)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_query_log_repo_delete_by_document_id_skips_commit_when_requested():
    """commit=False leaves the transaction open for the caller."""
    from src.repositories.query_log_repo import QueryLogRepository

    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()

    repo = QueryLogRepository(session)
    await repo.delete_by_document_id(uuid4(), commit=False)

    session.execute.assert_awaited_once()
    session.commit.assert_not_awaited()
