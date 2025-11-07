"""FastAPI application main entry point."""

import logging

from fastapi import FastAPI

from src.api.middleware import (
    add_cors_middleware,
    add_error_handler_middleware,
    add_logging_middleware,
)
from src.api.routes import documents, health, query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create FastAPI app
app = FastAPI(
    title="Sistema RAG en Español",
    description="""
    Sistema de Recuperación y Generación Aumentada (RAG) para documentos PDF en español chileno.

    ## Características

    * **Subir documentos PDF**: Procesa y vectoriza automáticamente
    * **Búsqueda semántica**: Encuentra información relevante usando embeddings
    * **Respuestas en español**: Genera respuestas en español chileno natural
    * **Prevención de alucinaciones**: Solo responde con información del documento
    * **Referencias de páginas**: Incluye citas de páginas en las respuestas

    ## Flujo de uso

    1. Sube un documento PDF con `/documents/upload`
    2. Verifica el estado con `/documents/{document_id}/status`
    3. Realiza preguntas con `/query/`
    4. Obtén respuestas basadas en el contenido del documento
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add middleware (order matters - last added runs first)
add_logging_middleware(app)
add_error_handler_middleware(app)
add_cors_middleware(app)

# Include routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(query.router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Sistema RAG en Español",
        "version": "1.0.0",
        "docs": "/docs",
    }
