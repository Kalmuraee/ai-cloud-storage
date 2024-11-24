"""
Dependency injection functions for FastAPI.
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.storage.service import StorageService
from app.modules.ai_processor.service import AIProcessorService
from app.modules.auth.service import AuthService

# Singleton instances
_storage_service: Optional[StorageService] = None
_ai_processor_service: Optional[AIProcessorService] = None
_auth_service: Optional[AuthService] = None

async def get_storage_service(db: AsyncSession = Depends(get_db)) -> StorageService:
    """Get storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService(db)
    return _storage_service

async def get_ai_processor_service(db: AsyncSession = Depends(get_db)) -> AIProcessorService:
    """Get AI processor service instance."""
    global _ai_processor_service
    if _ai_processor_service is None:
        _ai_processor_service = AIProcessorService(db)
    return _ai_processor_service

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get authentication service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService(db)
    return _auth_service
