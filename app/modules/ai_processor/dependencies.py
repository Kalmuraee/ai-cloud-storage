"""
AI Processor dependencies
"""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from .service import AIProcessorService

logger = get_logger(__name__)

async def get_ai_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> AIProcessorService:
    """Get AI processor service instance."""
    return AIProcessorService(db)
