"""Query endpoints for RAG question-answering."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_rag_service
from src.api.schemas import QueryRequest, QueryResponse
from src.services.rag_service import RAGService
from src.utils.exceptions import RAGSystemError

router = APIRouter(prefix="/query", tags=["query"])


@router.post(
    "/",
    response_model=QueryResponse,
    summary="Hacer pregunta sobre documentos",
    description="Realiza una pregunta y obtiene respuesta usando RAG",
)
async def query_documents(
    request: QueryRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
):
    """
    Query documents using RAG approach.

    The system will:
    1. Search for relevant document chunks
    2. Generate an answer based on the context
    3. Indicate if the question can be answered from the documents

    Returns answer with metadata about retrieved chunks and tokens used.
    """
    try:
        response = await rag_service.answer_question(
            question=request.question,
            document_id=request.document_id,
        )

        return QueryResponse(
            answer=response.answer,
            is_answerable=response.is_answerable,
            retrieved_chunks_count=response.retrieved_chunks_count,
            tokens_used=response.tokens_used,
            chunk_ids=response.chunk_ids,
        )

    except RAGSystemError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando consulta: {str(e)}",
        )
