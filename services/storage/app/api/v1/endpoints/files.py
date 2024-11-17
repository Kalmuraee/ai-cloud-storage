from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from datetime import datetime

from app.services.minio import minio_service
from app.services.quota import quota_service
from app.schemas.file import FileMetadata, FileShare, FileVersion, FileTag
from app.api import deps

router = APIRouter()

@router.post("/{bucket_name}/folders", response_model=None)
async def create_folder(
    bucket_name: str,
    folder_name: str,
    current_user = Depends(deps.get_current_user)
):
    """
    Create a new folder in a bucket.
    """
    return await minio_service.create_folder(bucket_name, folder_name)

@router.post("/{bucket_name}/files", response_model=None)
async def upload_file(
    bucket_name: str,
    file: UploadFile = File(...),
    object_name: str = Form(None),
    tags: List[str] = Form([]),
    retention_days: Optional[int] = Form(None),
    current_user = Depends(deps.get_current_user)
):
    """
    Upload a file to a bucket.
    """
    # Check quota before upload
    if not await quota_service.check_quota(current_user.id, file.size):
        raise HTTPException(
            status_code=400,
            detail="Quota exceeded"
        )
    
    try:
        result = await minio_service.upload_file(
            bucket_name,
            object_name or file.filename,
            file,
            tags=dict(zip(tags, tags)),
            retention_days=retention_days
        )
        
        # Update quota usage
        await quota_service.update_usage(current_user.id, file.size)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/{bucket_name}/files/{object_name}/versions", response_model=List[FileVersion])
async def list_versions(
    bucket_name: str,
    object_name: str,
    current_user = Depends(deps.get_current_user)
):
    """
    List all versions of a file.
    """
    return await minio_service.list_versions(bucket_name, object_name)

@router.get("/{bucket_name}/files/{object_name}")
async def download_file(
    bucket_name: str,
    object_name: str,
    version_id: Optional[str] = None,
    current_user = Depends(deps.get_current_user)
):
    """
    Download a file from a bucket.
    """
    data, content_type, size = await minio_service.download_file(
        bucket_name,
        object_name,
        version_id
    )
    
    return StreamingResponse(
        data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{object_name}"',
            "Content-Length": str(size)
        }
    )

@router.post("/{bucket_name}/files/{object_name}/share")
async def share_file(
    bucket_name: str,
    object_name: str,
    share: FileShare,
    current_user = Depends(deps.get_current_user)
):
    """
    Share a file with another user.
    """
    url = await minio_service.share_file(bucket_name, object_name, share)
    return {"share_url": url} if url else {"message": "File shared successfully"}

@router.get("/{bucket_name}/files/{object_name}/metadata", response_model=FileMetadata)
async def get_metadata(
    bucket_name: str,
    object_name: str,
    current_user = Depends(deps.get_current_user)
):
    """
    Get file metadata.
    """
    metadata = await minio_service._get_metadata(bucket_name, object_name)
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
    return metadata

@router.put("/{bucket_name}/files/{object_name}/tags")
async def update_tags(
    bucket_name: str,
    object_name: str,
    tags: List[FileTag],
    current_user = Depends(deps.get_current_user)
):
    """
    Update file tags.
    """
    metadata = await minio_service._get_metadata(bucket_name, object_name)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    metadata.tags = [tag.tag for tag in tags]
    await minio_service._store_metadata(bucket_name, object_name, metadata)
    
    # Update MinIO tags
    await minio_service.client.set_object_tags(
        bucket_name,
        object_name,
        {tag.tag: tag.tag for tag in tags}
    )
    
    return {"message": "Tags updated"}