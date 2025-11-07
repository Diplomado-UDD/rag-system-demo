"""Health check endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session
from src.api.schemas import HealthCheckResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Verifica el estado del servicio y la base de datos",
)
async def health_check(
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Health check endpoint.

    Verifies:
    - Service is running
    - Database connection is working
    """
    # Check database connection
    try:
        await session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthCheckResponse(
        status="healthy",
        database=db_status,
        timestamp=datetime.utcnow(),
    )
