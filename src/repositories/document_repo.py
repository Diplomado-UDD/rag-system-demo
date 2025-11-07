"""Document repository for database operations."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import Document, DocumentStatus
from src.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document operations."""

    def __init__(self, session: AsyncSession):
        """Initialize document repository."""
        super().__init__(Document, session)

    async def get_by_filename(self, filename: str) -> Optional[Document]:
        """
        Get document by filename.

        Args:
            filename: Name of the file

        Returns:
            Document instance or None
        """
        result = await self.session.execute(
            select(Document).where(Document.filename == filename)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self, document_id: UUID, status: DocumentStatus, error_message: Optional[str] = None
    ) -> Document:
        """
        Update document status.

        Args:
            document_id: Document UUID
            status: New status
            error_message: Error message if status is failed

        Returns:
            Updated document
        """
        document = await self.get_by_id(document_id)
        if document:
            document.status = status
            if error_message:
                document.error_message = error_message
            return await self.update(document)
        return None
