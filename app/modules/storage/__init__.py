"""
Storage Module
"""
from fastapi import APIRouter
from minio import Minio
from app.core.config import settings

# Create router for storage module
router = APIRouter(prefix="/storage", tags=["Storage"])

# Initialize MinIO client
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ROOT_USER,
    secret_key=settings.MINIO_ROOT_PASSWORD,
    secure=settings.MINIO_SECURE,
    region=settings.MINIO_REGION,
)

def init_storage_module() -> APIRouter:
    """Initialize storage module."""
    if not settings.STORAGE_MODULE_ENABLED:
        return router
        
    # Import handlers here to avoid circular imports
    from .routes import router as storage_router
    from .api.files import router as files_router
    
    # Include routes
    router.include_router(storage_router)
    router.include_router(files_router)
    
    # Ensure bucket exists
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
        minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
        # Set bucket policy for public access if needed
        # minio_client.set_bucket_policy(settings.MINIO_BUCKET_NAME, PUBLIC_READ_POLICY)
    
    return router

# Export dependencies and clients
from .dependencies import get_storage_service
from .service import StorageService
