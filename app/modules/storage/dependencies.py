"""
Dependencies for the storage module.
"""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.minio import get_minio_client
from app.modules.storage.repository import StorageRepository
from app.modules.storage.service import StorageService

async def get_storage_service(
    session: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
) -> StorageService:
    """
    Dependency to get the storage service instance with injected dependencies.
    """
    repo = StorageRepository(session)
    return StorageService(repo=repo, minio_client=minio_client)

StorageServiceDep = Annotated[StorageService, Depends(get_storage_service)]
