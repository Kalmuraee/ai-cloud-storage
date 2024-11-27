"""
Storage module routes.

This module provides endpoints for file storage operations, including:
- File upload with deduplication
- File download and streaming
- File metadata management
- File listing and search
- File deletion
- Duplicate file detection
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Path, Form, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.minio import get_minio_client
from app.core.logging import logger
from app.modules.storage.service import StorageService
from app.modules.storage.repository import StorageRepository
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
from app.modules.ai_processor.service import AIProcessorService

router = APIRouter()

@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "File successfully uploaded",
            "model": FileUploadResponse
        },
        400: {
            "description": "Invalid file or request parameters"
        },
        401: {
            "description": "Not authenticated"
        },
        413: {
            "description": "File too large"
        },
        422: {
            "description": "Validation error in request parameters"
        }
    }
)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    folder_id: Optional[int] = Form(None, description="Optional folder ID to store the file in"),
    check_duplicates: bool = Form(True, description="Whether to check for duplicates"),
    process_file: bool = Form(True, description="Whether to process the file with AI models"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
) -> FileUploadResponse:
    """Upload a file to storage with optional deduplication and AI processing."""
    try:
        repo = StorageRepository(db)
        service = StorageService(repo, minio_client)
        response = await service.upload_file(file, current_user.id, folder_id, check_duplicates)
        
        # Only process file if requested and not a duplicate
        if process_file and not response.is_duplicate:
            ai_processor = AIProcessorService(db)
            await ai_processor.process_file(response.file.id)
            
        return response
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get(
    "/duplicates",
    response_model=List[DuplicateFilesResponse],
    responses={
        200: {
            "description": "List of duplicate files",
            "model": DuplicateFilesResponse
        },
        401: {
            "description": "Not authenticated"
        }
    }
)
async def get_duplicate_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
) -> List[DuplicateFilesResponse]:
    """Get list of duplicate files."""
    repo = StorageRepository(db)
    service = StorageService(repo, minio_client)
    return await service.get_duplicate_files(current_user.id)

@router.get(
    "/download/{file_path:path}",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "File content stream"
        },
        401: {
            "description": "Not authenticated"
        },
        404: {
            "description": "File not found"
        }
    }
)
async def download_file(
    file_path: str = Path(..., description="Path of the file to download"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
) -> StreamingResponse:
    """Download a file from storage."""
    try:
        repo = StorageRepository(db)
        service = StorageService(repo, minio_client)
        
        # Get file stream
        content = await service.download_file(file_path, current_user.id)
        
        # Get file metadata for content type
        metadata = await service.get_file_metadata(file_path, current_user.id)
        
        return StreamingResponse(
            content,
            media_type=metadata.get("content_type", "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="{metadata.get("filename", "download")}"'
            }
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.get(
    "/list",
    response_model=FileListResponse,
    responses={
        200: {
            "description": "List of files",
            "model": FileListResponse
        },
        401: {
            "description": "Not authenticated"
        }
    }
)
async def list_files(
    prefix: Optional[str] = Query(None, description="Optional prefix to filter files"),
    recursive: bool = Query(True, description="Whether to list files recursively"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
) -> FileListResponse:
    """List files in storage."""
    try:
        repo = StorageRepository(db)
        service = StorageService(repo, minio_client)
        files, _ = await service.list_files(current_user.id, prefix, recursive)
        return FileListResponse(files=files)
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )

@router.get(
    "/metadata/{file_path:path}",
    response_model=FileMetadataResponse,
    responses={
        200: {
            "description": "File metadata",
            "model": FileMetadataResponse
        },
        401: {
            "description": "Not authenticated"
        },
        404: {
            "description": "File not found"
        }
    }
)
async def get_file_metadata(
    file_path: str = Path(..., description="Path of the file to get metadata for"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
) -> FileMetadataResponse:
    """Get file metadata."""
    try:
        repo = StorageRepository(db)
        service = StorageService(repo, minio_client)
        metadata = await service.get_file_metadata(file_path, current_user.id)
        return FileMetadataResponse(**metadata)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting file metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file metadata: {str(e)}"
        )

@router.delete(
    "/{file_path:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {
            "description": "File deleted successfully"
        },
        401: {
            "description": "Not authenticated"
        },
        404: {
            "description": "File not found"
        }
    }
)
async def delete_file(
    file_path: str = Path(..., description="Path of the file to delete"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
):
    """Delete a file from storage."""
    try:
        repo = StorageRepository(db)
        service = StorageService(repo, minio_client)
        await service.delete_file(file_path, current_user.id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

@router.get(
    "/{file_path:path}",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "File content stream",
            "content": {
                "application/octet-stream": {}
            }
        },
        401: {
            "description": "Not authenticated"
        },
        404: {
            "description": "File not found"
        }
    }
)
async def download_file(
    file_path: str = Path(..., description="Path of the file to download"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
) -> StreamingResponse:
    """
    Download a file from storage.
    
    Streams the file content from MinIO storage. The file must belong to
    the requesting user.
    
    Args:
        file_path: Path of the file to download
        current_user: Current authenticated user
        db: Database session
        minio_client: MinIO client instance
    
    Returns:
        StreamingResponse: File content stream
    
    Raises:
        HTTPException(401): If user is not authenticated
        HTTPException(404): If file not found
        HTTPException(500): If download fails
    """
    repo = StorageRepository(db)
    service = StorageService(repo, minio_client)
    return await service.download_file(file_path, current_user.id)

@router.get(
    "/",
    response_model=FileListResponse,
    responses={
        200: {
            "description": "List of files",
            "model": FileListResponse
        },
        401: {
            "description": "Not authenticated"
        }
    }
)
async def list_files(
    prefix: Optional[str] = Query(None, description="Optional prefix to filter files"),
    recursive: bool = Query(True, description="Whether to list files recursively"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
) -> FileListResponse:
    """
    List files in storage.
    
    Lists all files belonging to the requesting user. Can be filtered by
    prefix and recursively list subdirectories.
    
    Args:
        prefix: Optional prefix to filter files
        recursive: Whether to list files recursively (default: True)
        current_user: Current authenticated user
        db: Database session
        minio_client: MinIO client instance
    
    Returns:
        FileListResponse: List of files and their metadata
    
    Raises:
        HTTPException(401): If user is not authenticated
        HTTPException(500): If listing fails
    """
    try:
        repo = StorageRepository(db)
        service = StorageService(repo, minio_client)
        files = await service.list_files(current_user.id, prefix, recursive)
        return FileListResponse(files=files)
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )

@router.get(
    "/{file_path:path}/metadata",
    response_model=FileMetadataResponse,
    responses={
        200: {
            "description": "File metadata",
            "model": FileMetadataResponse
        },
        401: {
            "description": "Not authenticated"
        },
        404: {
            "description": "File not found"
        }
    }
)
async def get_file_metadata(
    file_path: str = Path(..., description="Path of the file to get metadata for"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    minio_client = Depends(get_minio_client)
) -> FileMetadataResponse:
    """
    Get file metadata.
    
    Retrieves metadata for a specific file, including size, content type,
    creation time, and any custom metadata.
    
    Args:
        file_path: Path of the file to get metadata for
        current_user: Current authenticated user
        db: Database session
        minio_client: MinIO client instance
    
    Returns:
        FileMetadataResponse: File metadata
    
    Raises:
        HTTPException(401): If user is not authenticated
        HTTPException(404): If file not found
        HTTPException(500): If operation fails
    """
    try:
        repo = StorageRepository(db)
        service = StorageService(repo, minio_client)
        metadata = await service.get_file_metadata(file_path, current_user.id)
        return FileMetadataResponse(**metadata)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting file metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file metadata: {str(e)}"
        )
