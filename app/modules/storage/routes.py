"""
Storage module routes
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Path, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.minio import get_minio_client
from app.core.logging import get_logger
from app.modules.storage.service import StorageService
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.storage.schemas import (
    FileUploadResponse,
    DuplicateFilesResponse,
    FileResponse,
    FileListResponse,
    MetadataUpdate,
    FileMetadataResponse
)

router = APIRouter()
logger = get_logger(__name__)

@router.post("/upload/", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[int] = Form(None),
    check_duplicates: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
):
    """
    Upload a file with deduplication support
    
    - **file**: The file to upload
    - **folder_id**: Optional folder ID to store the file in
    - **check_duplicates**: Whether to check for duplicates (default: True)
    """
    service = StorageService(db, minio_client)
    
    # Save uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process file with deduplication
        file_obj, is_duplicate = await service.upload_file(
            file_path=temp_path,
            owner_id=current_user.id,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            folder_id=folder_id,
            check_duplicates=check_duplicates
        )
        
        return FileUploadResponse(
            file=FileResponse.from_orm(file_obj),
            is_duplicate=is_duplicate
        )
    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        import os
        try:
            os.remove(temp_path)
        except:
            pass

@router.get("/duplicates/", response_model=List[DuplicateFilesResponse])
async def get_duplicate_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
):
    """
    Get all duplicate files grouped by content hash
    """
    try:
        service = StorageService(db, minio_client)
        duplicates = await service.get_duplicate_files()
        
        return [
            DuplicateFilesResponse(
                content_hash=hash_value,
                files=[FileResponse.from_orm(f) for f in files]
            )
            for hash_value, files in duplicates
        ]
    except Exception as e:
        logger.error(f"Failed to get duplicate files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_path}", response_class=StreamingResponse, tags=["Storage"])
async def download_file(
    file_path: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
):
    """
    Download a file from storage.
    
    - **file_path**: Path of the file to download
    """
    try:
        # Verify file access
        service = StorageService(db, minio_client)
        file = await service.get_file(file_path, current_user.id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_stream = await service.download_file(file_path)
        return StreamingResponse(
            file_stream,
            media_type=file.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file.original_filename}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{file_path}", response_model=Dict[str, str], tags=["Storage"])
async def delete_file(
    file_path: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
):
    """
    Delete a file from storage.
    
    - **file_path**: Path of the file to delete
    """
    try:
        # Verify file access
        service = StorageService(db, minio_client)
        file = await service.get_file(file_path, current_user.id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        await service.delete_file(file_path)
        await db.delete(file)
        await db.commit()
        
        return {"message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=FileListResponse, tags=["Storage"])
async def list_files(
    prefix: Optional[str] = Query(None, description="Optional prefix to filter files"),
    recursive: bool = Query(True, description="Whether to list files recursively"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
):
    """
    List files in storage.
    
    - **prefix**: Optional prefix to filter files
    - **recursive**: Whether to list files recursively
    """
    try:
        # Get user's files from database
        service = StorageService(db, minio_client)
        files = await service.list_files(current_user.id, prefix, recursive)
        
        return {
            "files": [
                {
                    "id": file.id,
                    "filename": file.original_filename,
                    "path": file.path,
                    "size": file.size,
                    "content_type": file.content_type,
                    "status": file.status,
                    "created_at": file.created_at
                }
                for file in files
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_path}/metadata", response_model=FileMetadataResponse, tags=["Storage"])
async def get_file_metadata(
    file_path: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
):
    """
    Get file metadata.
    
    - **file_path**: Path of the file to get metadata for
    """
    try:
        # Get file from database
        service = StorageService(db, minio_client)
        file = await service.get_file(file_path, current_user.id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get storage metadata
        storage_metadata = await service.get_file_metadata(file_path)
        
        # Combine with database metadata
        return {
            "id": file.id,
            "filename": file.original_filename,
            "path": file.path,
            "size": file.size,
            "content_type": file.content_type,
            "status": file.status,
            "created_at": file.created_at,
            "storage_metadata": storage_metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
