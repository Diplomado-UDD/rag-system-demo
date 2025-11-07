"""QueryLog model for storing query history and analytics."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from src.models.document import Base


class QueryLog(Base):
    """QueryLog model for storing user queries and responses."""

    __tablename__ = "query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    retrieved_chunks = Column(JSON, nullable=True)
    is_answerable = Column(Boolean, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<QueryLog(id={self.id}, is_answerable={self.is_answerable})>"
