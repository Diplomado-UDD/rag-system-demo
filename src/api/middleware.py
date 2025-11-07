"""FastAPI middleware for error handling, CORS, and logging."""

import logging
import time
from typing import Callable

from fastapi import Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.exceptions import (
    DocumentNotFoundError,
    FileSizeExceededError,
    InvalidFileTypeError,
    PDFProcessingError,
    RAGSystemError,
)

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle requests and catch exceptions."""
        try:
            response = await call_next(request)
            return response
        except DocumentNotFoundError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e), "error_type": "DocumentNotFound"},
            )
        except InvalidFileTypeError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": str(e), "error_type": "InvalidFileType"},
            )
        except FileSizeExceededError as e:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": str(e), "error_type": "FileSizeExceeded"},
            )
        except PDFProcessingError as e:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": str(e), "error_type": "PDFProcessingError"},
            )
        except RAGSystemError as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": str(e), "error_type": "RAGSystemError"},
            )
        except Exception as e:
            logger.exception("Unhandled exception")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Error interno del servidor",
                    "error_type": "InternalServerError",
                },
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
            },
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {response.status_code} ({duration:.3f}s)",
            extra={
                "status_code": response.status_code,
                "duration_seconds": duration,
            },
        )

        # Add timing header
        response.headers["X-Process-Time"] = f"{duration:.3f}"

        return response


def add_cors_middleware(app):
    """
    Add CORS middleware to FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def add_error_handler_middleware(app):
    """
    Add error handler middleware to FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(ErrorHandlerMiddleware)


def add_logging_middleware(app):
    """
    Add request logging middleware to FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RequestLoggingMiddleware)
