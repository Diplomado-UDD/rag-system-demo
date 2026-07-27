"""QueryLog repository for database operations."""

from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.query_log import QueryLog
from src.repositories.base import BaseRepository


class QueryLogRepository(BaseRepository[QueryLog]):
    """Repository for QueryLog operations."""

    def __init__(self, session: AsyncSession):
        """Initialize query log repository."""
        super().__init__(QueryLog, session)

    async def delete_by_document_id(self, document_id: UUID, commit: bool = True) -> None:
        """
        Delete all query logs for a document.

        Args:
            document_id: Document UUID
            commit: Whether to commit immediately
        """
        await self.session.execute(
            delete(QueryLog).where(QueryLog.document_id == document_id)
        )
        if commit:
            await self.session.commit()
