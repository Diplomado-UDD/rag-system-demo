"""Integration tests for document deletion endpoint."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.dependencies import get_document_repo, get_vector_repo
from src.main import app
from src.models.document import Document, DocumentStatus


class DummySession:
    """Minimal async session stub for transaction assertions."""

    def __init__(self):
        self.commit_calls = 0
        self.rollback_calls = 0

    async def commit(self):
        self.commit_calls += 1

    async def rollback(self):
        self.rollback_calls += 1


class DummyDocumentRepo:
    """Document repository stub for delete route tests."""

    def __init__(self, document, session: DummySession, fail_on_delete: bool = False):
        self.document = document
        self.session = session
        self.fail_on_delete = fail_on_delete
        self.deleted_document = None

    async def get_by_id(self, document_id):
        return self.document

    async def delete(self, document, commit: bool = True):
        self.deleted_document = document
        if self.fail_on_delete:
            raise RuntimeError('delete failed')


class DummyVectorRepo:
    """Vector repository stub for delete route tests."""

    def __init__(self, session: DummySession):
        self.session = session
        self.deleted_document_id = None

    async def delete_chunks_by_document_id(self, document_id, commit: bool = True):
        self.deleted_document_id = document_id


@pytest.fixture
async def delete_client():
    """Provide a helper that mounts repo overrides for delete tests."""

    async def _make_client(document_repo, vector_repo):
        async def override_get_document_repo():
            return document_repo

        async def override_get_vector_repo():
            return vector_repo

        app.dependency_overrides[get_document_repo] = override_get_document_repo
        app.dependency_overrides[get_vector_repo] = override_get_vector_repo

        return AsyncClient(transport=ASGITransport(app=app), base_url='http://test')

    yield _make_client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_document_returns_204_and_commits_once(delete_client):
    """Delete succeeds and finalizes the transaction once."""
    document_id = uuid4()
    session = DummySession()
    document = Document(
        id=document_id,
        filename='demo.pdf',
        file_size=123,
        status=DocumentStatus.ready,
    )
    document_repo = DummyDocumentRepo(document=document, session=session)
    vector_repo = DummyVectorRepo(session=session)

    async with await delete_client(document_repo, vector_repo) as client:
        response = await client.delete(f'/documents/{document_id}')

    assert response.status_code == 204
    assert response.text == ''
    assert vector_repo.deleted_document_id == document_id
    assert document_repo.deleted_document == document
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


@pytest.mark.asyncio
async def test_delete_document_returns_404_when_missing(delete_client):
    """Delete returns not found when the document does not exist."""
    document_id = uuid4()
    session = DummySession()
    document_repo = DummyDocumentRepo(document=None, session=session)
    vector_repo = DummyVectorRepo(session=session)

    async with await delete_client(document_repo, vector_repo) as client:
        response = await client.delete(f'/documents/{document_id}')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Documento no encontrado'
    assert vector_repo.deleted_document_id is None
    assert session.commit_calls == 0


@pytest.mark.asyncio
async def test_delete_document_rolls_back_when_delete_fails(delete_client):
    """Delete failure rolls back instead of leaving a partial commit path."""
    document_id = uuid4()
    session = DummySession()
    document = Document(
        id=document_id,
        filename='demo.pdf',
        file_size=123,
        status=DocumentStatus.ready,
    )
    document_repo = DummyDocumentRepo(document=document, session=session, fail_on_delete=True)
    vector_repo = DummyVectorRepo(session=session)

    async with await delete_client(document_repo, vector_repo) as client:
        response = await client.delete(f'/documents/{document_id}')

    assert response.status_code == 500
    assert response.json()['detail'] == 'Error interno del servidor'
    assert vector_repo.deleted_document_id == document_id
    assert session.commit_calls == 0
    assert session.rollback_calls == 1