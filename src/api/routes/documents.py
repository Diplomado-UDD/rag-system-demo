"""Document management endpoints."""

import logging
import tempfile
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from src.api.dependencies import (
    get_chunking_service,
    get_db_session,
    get_document_repo,
    get_embedding_service,
    get_pdf_service,
    get_vector_repo,
)
from src.api.schemas import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
)
from src.models.chunk import Chunk
from src.models.document import Document, DocumentStatus
from src.repositories.document_repo import DocumentRepository
from src.repositories.vector_repo import VectorRepository
from src.services.chunking_service import ChunkingService
from src.services.embedding_service import EmbeddingService
from src.services.pdf_service import PDFService
from src.utils.exceptions import (
    DocumentNotFoundError,
    FileSizeExceededError,
    InvalidFileTypeError,
    PDFProcessingError,
)
from src.utils.validators import validate_file_size, validate_file_type

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir documento PDF",
    description="Sube un PDF y comienza el procesamiento asíncrono",
)
async def upload_document(
    file: Annotated[UploadFile, File(description="Archivo PDF a procesar")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    document_repo: Annotated[DocumentRepository, Depends(get_document_repo)],
    vector_repo: Annotated[VectorRepository, Depends(get_vector_repo)],
    pdf_service: Annotated[PDFService, Depends(get_pdf_service)],
    chunking_service: Annotated[ChunkingService, Depends(get_chunking_service)],
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding_service)],
):
    """
    Upload and process a PDF document.

    The document is processed asynchronously:
    1. Validates file type and size
    2. Extracts text from PDF
    3. Chunks the text
    4. Generates embeddings
    5. Stores in vector database

    Returns document metadata with processing status.
    """
    try:
        # Validate file
        validate_file_type(file.filename)

        # Read file content
        content = await file.read()
        file_size = len(content)
        validate_file_size(file_size)

        # Create document record
        document = Document(
            filename=file.filename,
            file_size=file_size,
            status=DocumentStatus.processing,
        )
        document = await document_repo.create(document)

        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".pdf"
            ) as temp_file:
                temp_file.write(content)
                temp_path = Path(temp_file.name)

            # Extract text with page numbers
            pages_text = pdf_service.extract_text_with_pages(str(temp_path))
            logger.info(f"Extracted {len(pages_text)} pages from {file.filename}")

            # Clean up temp file
            temp_path.unlink()

            # Update total pages
            document.total_pages = len(pages_text)

            # Chunk text
            chunks_data = chunking_service.chunk_text(pages_text)
            logger.info(f"Generated {len(chunks_data)} chunks from {file.filename}")

            # Generate embeddings and create chunk records
            chunk_texts = [chunk_data["content"] for chunk_data in chunks_data]
            embeddings = embedding_service.embed_batch(chunk_texts)

            # Create chunk objects
            chunks = []
            for chunk_data, embedding in zip(chunks_data, embeddings):
                chunk = Chunk(
                    document_id=document.id,
                    content=chunk_data["content"],
                    embedding=embedding,
                    page_number=chunk_data["page_number"],
                    chunk_index=chunk_data["chunk_index"],
                    word_count=chunk_data["word_count"],
                )
                chunk = await vector_repo.create_chunk(chunk)
                chunks.append(chunk)

            # Update document status
            document.total_chunks = len(chunks)
            document.status = DocumentStatus.ready
            document = await document_repo.update(document)

            return DocumentResponse.model_validate(document)

        except (PDFProcessingError, Exception) as e:
            # Update document with error
            await document_repo.update_status(
                document.id,
                DocumentStatus.failed,
                error_message=f"Error procesando documento: {str(e)}",
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Error procesando documento: {str(e)}",
            )

    except InvalidFileTypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except FileSizeExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e)
        )


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    summary="Obtener estado de documento",
    description="Obtiene el estado de procesamiento de un documento",
)
async def get_document_status(
    document_id: UUID,
    document_repo: Annotated[DocumentRepository, Depends(get_document_repo)],
):
    """Get document processing status."""
    document = await document_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado"
        )

    # Build progress message
    if document.status == DocumentStatus.processing:
        progress_message = "Procesando documento..."
    elif document.status == DocumentStatus.ready:
        progress_message = f"Documento listo. {document.total_chunks} fragmentos generados."
    elif document.status == DocumentStatus.failed:
        progress_message = f"Error: {document.error_message}"
    else:
        progress_message = "Estado desconocido"

    return DocumentStatusResponse(
        id=document.id,
        filename=document.filename,
        status=document.status.value,
        error_message=document.error_message,
        total_pages=document.total_pages,
        total_chunks=document.total_chunks,
        progress_message=progress_message,
    )


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="Listar documentos",
    description="Obtiene la lista de todos los documentos subidos",
)
async def list_documents(
    document_repo: Annotated[DocumentRepository, Depends(get_document_repo)],
    limit: int = 100,
):
    """List all uploaded documents."""
    documents = await document_repo.list_all(limit=limit)
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=len(documents),
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar documento",
    description="Elimina un documento y todos sus fragmentos",
)
async def delete_document(
    document_id: UUID,
    document_repo: Annotated[DocumentRepository, Depends(get_document_repo)],
    vector_repo: Annotated[VectorRepository, Depends(get_vector_repo)],
):
    """Delete a document and all its chunks."""
    document = await document_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado"
        )

    # Delete chunks first
    await vector_repo.delete_chunks_by_document_id(document_id)

    # Delete document
    await document_repo.delete(document)

    return None
