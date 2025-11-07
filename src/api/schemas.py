"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Document schemas
class DocumentResponse(BaseModel):
    """Document response schema."""

    id: UUID
    filename: str
    file_size: int
    upload_date: datetime
    status: str
    error_message: Optional[str] = None
    total_pages: Optional[int] = None
    total_chunks: Optional[int] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Document list response schema."""

    documents: list[DocumentResponse]
    total: int


class DocumentStatusResponse(BaseModel):
    """Document status response schema."""

    id: UUID
    filename: str
    status: str
    error_message: Optional[str] = None
    total_pages: Optional[int] = None
    total_chunks: Optional[int] = None
    progress_message: str


# Query schemas
class QueryRequest(BaseModel):
    """Query request schema."""

    question: str = Field(..., min_length=1, description="Pregunta del usuario")
    document_id: Optional[UUID] = Field(
        None, description="ID del documento para filtrar búsqueda"
    )


class QueryResponse(BaseModel):
    """Query response schema."""

    answer: str = Field(..., description="Respuesta generada")
    is_answerable: bool = Field(
        ..., description="Indica si la pregunta pudo responderse del contexto"
    )
    retrieved_chunks_count: int = Field(
        ..., description="Número de fragmentos recuperados"
    )
    tokens_used: int = Field(..., description="Tokens utilizados por el LLM")
    chunk_ids: list[UUID] = Field(..., description="IDs de los chunks utilizados")


# Error schemas
class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str = Field(..., description="Descripción del error")
    error_type: Optional[str] = Field(None, description="Tipo de error")


# Health check schema
class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Estado del servicio")
    database: str = Field(..., description="Estado de la base de datos")
    timestamp: datetime = Field(..., description="Timestamp de la verificación")
