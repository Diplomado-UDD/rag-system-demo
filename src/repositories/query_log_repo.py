"""QueryLog repository for database operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.query_log import QueryLog
from src.repositories.base import BaseRepository


class QueryLogRepository(BaseRepository[QueryLog]):
    """Repository for QueryLog operations."""

    def __init__(self, session: AsyncSession):
        """Initialize query log repository."""
        super().__init__(QueryLog, session)
