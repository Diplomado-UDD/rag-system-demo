"""Document model for storing PDF metadata."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DocumentStatus(enum.Enum):
    """Document processing status."""

    uploading = "uploading"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class Document(Base):
    """Document model for storing PDF metadata."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.uploading, nullable=False)
    error_message = Column(Text, nullable=True)
    total_pages = Column(Integer, nullable=True)
    total_chunks = Column(Integer, nullable=True)
    doc_metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
