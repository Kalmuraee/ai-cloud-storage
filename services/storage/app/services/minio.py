from datetime import datetime
from typing import BinaryIO, List, Optional

from fastapi import HTTPException, UploadFile
from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.schemas.bucket import Bucket, ObjectInfo


class MinioService:
    def __init__(self):
        self.client = Minio(
            f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_USE_SSL,
        )

    async def list_buckets(self) -> List[Bucket]:
        try:
            buckets = self.client.list_buckets()
            return [
                Bucket(name=bucket.name, creation_date=bucket.creation_date)
                for bucket in buckets
            ]
        except S3Error as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def create_bucket(self, name: str) -> None:
        try:
            self.client.make_bucket(name)
        except S3Error as e:
            if "already exists" in str(e):
                raise HTTPException(status_code=409, detail="Bucket already exists")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_bucket(self, name: str) -> None:
        try:
            self.client.remove_bucket(name)
        except S3Error as e:
            if "NoSuchBucket" in str(e):
                raise HTTPException(status_code=404, detail="Bucket not found")
            raise HTTPException(status_code=500, detail=str(e))

    async def list_objects(self, bucket_name: str, prefix: str = "") -> List[ObjectInfo]:
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
            return [
                ObjectInfo(
                    bucket_name=bucket_name,
                    object_name=obj.object_name,
                    size=obj.size,
                    last_modified=obj.last_modified,
                    etag=obj.etag,
                    content_type=obj.content_type,
                )
                for obj in objects
            ]
        except S3Error as e:
            if "NoSuchBucket" in str(e):
                raise HTTPException(status_code=404, detail="Bucket not found")
            raise HTTPException(status_code=500, detail=str(e))

    async def upload_file(
        self, bucket_name: str, object_name: str, file: UploadFile
    ) -> ObjectInfo:
        try:
            # Check if bucket exists
            if not self.client.bucket_exists(bucket_name):
                raise HTTPException(status_code=404, detail="Bucket not found")

            # Upload the file
            result = self.client.put_object(
                bucket_name,
                object_name,
                file.file,
                file.size,
                content_type=file.content_type,
            )

            # Return object info
            return ObjectInfo(
                bucket_name=bucket_name,
                object_name=object_name,
                size=file.size,
                last_modified=datetime.now(),
                etag=result.etag,
                content_type=file.content_type,
            )
        except S3Error as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def download_file(self, bucket_name: str, object_name: str) -> tuple[BinaryIO, str, int]:
        try:
            # Get object stats
            stat = self.client.stat_object(bucket_name, object_name)
            
            # Get the object
            data = self.client.get_object(bucket_name, object_name)
            
            return data, stat.content_type, stat.size
        except S3Error as e:
            if "NoSuchKey" in str(e):
                raise HTTPException(status_code=404, detail="Object not found")
            if "NoSuchBucket" in str(e):
                raise HTTPException(status_code=404, detail="Bucket not found")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_file(self, bucket_name: str, object_name: str) -> None:
        try:
            self.client.remove_object(bucket_name, object_name)
        except S3Error as e:
            if "NoSuchKey" in str(e):
                raise HTTPException(status_code=404, detail="Object not found")
            if "NoSuchBucket" in str(e):
                raise HTTPException(status_code=404, detail="Bucket not found")
            raise HTTPException(status_code=500, detail=str(e))


minio_service = MinioService()