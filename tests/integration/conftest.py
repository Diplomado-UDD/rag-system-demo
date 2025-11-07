"""Fixtures for integration tests."""

import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_db_session
from src.main import app
from src.models.document import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine."""
    # Use test database URL (you might want to configure this separately)
    engine = create_async_engine(
        "postgresql+asyncpg://rag_user:rag_password@127.0.0.1:5433/rag_db",
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="session")
def async_session_maker(test_db_engine):
    """Create async session maker."""
    return sessionmaker(test_db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def client(async_session_maker) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with database override."""
    from httpx import ASGITransport

    async def override_get_db():
        async with async_session_maker() as session:
            try:
                yield session
            finally:
                await session.rollback()

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
