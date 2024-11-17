from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.schemas.bucket import Bucket, BucketCreate, ObjectInfo, ObjectList
from app.services.minio import minio_service

router = APIRouter()


@router.get("/", response_model=List[Bucket], summary="List all buckets")
async def list_buckets():
    """
    List all storage buckets.
    """
    return await minio_service.list_buckets()


@router.post("/", response_model=None, status_code=201, summary="Create a new bucket")
async def create_bucket(bucket: BucketCreate):
    """
    Create a new storage bucket.
    """
    await minio_service.create_bucket(bucket.name)
    return {"message": "Bucket created successfully"}


@router.delete("/{bucket_name}", status_code=204, summary="Delete a bucket")
async def delete_bucket(bucket_name: str):
    """
    Delete a storage bucket.
    """
    await minio_service.delete_bucket(bucket_name)


@router.get("/{bucket_name}/objects", response_model=ObjectList, summary="List objects in bucket")
async def list_objects(bucket_name: str, prefix: str = ""):
    """
    List all objects in a bucket.
    """
    objects = await minio_service.list_objects(bucket_name, prefix)
    return ObjectList(objects=objects)


@router.post("/{bucket_name}/objects", response_model=ObjectInfo, summary="Upload a file")
async def upload_file(
    bucket_name: str,
    file: UploadFile = File(...),
    object_name: str = Form(None),
):
    """
    Upload a file to a bucket.
    """
    if not object_name:
        object_name = file.filename
    
    return await minio_service.upload_file(bucket_name, object_name, file)


@router.get("/{bucket_name}/objects/{object_name}", summary="Download a file")
async def download_file(bucket_name: str, object_name: str):
    """
    Download a file from a bucket.
    """
    data, content_type, size = await minio_service.download_file(bucket_name, object_name)
    
    return StreamingResponse(
        data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{object_name}"',
            "Content-Length": str(size),
        },
    )


@router.delete("/{bucket_name}/objects/{object_name}", status_code=204, summary="Delete a file")
async def delete_file(bucket_name: str, object_name: str):
    """
    Delete a file from a bucket.
    """
    await minio_service.delete_file(bucket_name, object_name)