"""
API endpoints for file operations.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.modules.storage.service import StorageService
from app.core.exceptions import StorageError
from app.core.logging import get_logger
from app.core.dependencies import get_storage_service

router = APIRouter()
logger = get_logger(__name__)

class UploadUrlRequest(BaseModel):
    filename: str
    content_type: str

@router.post("/upload-url/", response_model=Dict[str, Any])
async def get_upload_url(
    request: UploadUrlRequest,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get a pre-signed URL for file upload."""
    try:
        url = await storage_service.get_upload_url(
            request.filename,
            request.content_type
        )
        return {"upload_url": url}
    except StorageError as e:
        logger.error(f"Failed to get upload URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    path: Optional[str] = Query(None),
    metadata: Optional[Dict[str, str]] = None,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Upload a file to storage."""
    try:
        file_info = await storage_service.upload_file(
            file.file,
            file.filename,
            path=path,
            metadata=metadata
        )
        return file_info
    except StorageError as e:
        logger.error(f"Failed to upload file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{file_path:path}", response_model=Dict[str, str])
async def delete_file(
    file_path: str = Path(...),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Delete a file from storage."""
    try:
        await storage_service.delete_file(file_path)
        return {"message": f"File {file_path} deleted successfully"}
    except StorageError as e:
        logger.error(f"Failed to delete file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Dict[str, Any]])
async def list_files(
    prefix: Optional[str] = Query(None),
    recursive: bool = Query(True),
    storage_service: StorageService = Depends(get_storage_service)
):
    """List files in storage."""
    try:
        files = await storage_service.list_files(prefix=prefix, recursive=recursive)
        return files
    except StorageError as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_path:path}/metadata", response_model=Dict[str, Any])
async def get_file_metadata(
    file_path: str = Path(...),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get file metadata."""
    try:
        metadata = await storage_service.get_file_metadata(file_path)
        return metadata
    except StorageError as e:
        logger.error(f"Failed to get file metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_path:path}/url", response_model=Dict[str, str])
async def get_presigned_url(
    file_path: str = Path(...),
    expires: int = Query(3600, description="URL expiration time in seconds"),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get a presigned URL for file access."""
    try:
        url = await storage_service.get_presigned_url(file_path, expires)
        return {"url": url}
    except StorageError as e:
        logger.error(f"Failed to get presigned URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
