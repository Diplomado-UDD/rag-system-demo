"""Chunk model for storing document chunks with embeddings."""

from datetime import datetime
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from src.models.document import Base


class Chunk(Base):
    """Chunk model for storing text chunks with vector embeddings."""

    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    word_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_chunks_document_id", "document_id"),
        Index("ix_chunks_document_chunk", "document_id", "chunk_index"),
        Index("ix_chunks_embedding", "embedding", postgresql_using="ivfflat"),
    )

    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, page={self.page_number})>"
