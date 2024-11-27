"""
MinIO client module for object storage operations
"""
from typing import Optional, BinaryIO, Any
from functools import lru_cache
from minio import Minio
from minio.commonconfig import ENABLED, Filter
from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration
from minio.deleteobjects import DeleteObject
from minio.error import S3Error

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class MinioClient:
    def __init__(self):
        """Initialize MinIO client"""
        try:
            self.client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            self._ensure_bucket()
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}")
            raise

    def _ensure_bucket(self):
        """Ensure the storage bucket exists"""
        try:
            if not self.client.bucket_exists(settings.MINIO_BUCKET_NAME):
                self.client.make_bucket(settings.MINIO_BUCKET_NAME)
                logger.info(f"Created bucket: {settings.MINIO_BUCKET_NAME}")
                
                # Set lifecycle policy for temporary uploads
                config = LifecycleConfig(
                    [
                        Rule(
                            ENABLED,
                            rule_filter=Filter(prefix="uploads/temp/"),
                            rule_id="delete_old_uploads",
                            expiration=Expiration(days=1)
                        )
                    ]
                )
                self.client.set_bucket_lifecycle(settings.MINIO_BUCKET_NAME, config)
        except S3Error as e:
            logger.error(f"Failed to ensure bucket: {str(e)}")
            raise

    async def get_object(self, bucket_name: str, object_name: str) -> BinaryIO:
        """Get object from MinIO"""
        try:
            return self.client.get_object(
                bucket_name=bucket_name,
                object_name=object_name
            )
        except S3Error as e:
            logger.error(f"Failed to get object {object_name}: {str(e)}")
            raise

    async def put_object(self, bucket_name: str, object_name: str, data: BinaryIO, length: int) -> None:
        """Put object in MinIO"""
        try:
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=data,
                length=length
            )
        except S3Error as e:
            logger.error(f"Failed to put object {object_name}: {str(e)}")
            raise

    async def remove_object(self, bucket_name: str, object_name: str) -> None:
        """Remove object from MinIO"""
        try:
            self.client.remove_object(
                bucket_name=bucket_name,
                object_name=object_name
            )
        except S3Error as e:
            logger.error(f"Failed to remove object {object_name}: {str(e)}")
            raise

    async def stat_object(self, bucket_name: str, object_name: str) -> Any:
        """Get object stats from MinIO"""
        try:
            return self.client.stat_object(
                bucket_name=bucket_name,
                object_name=object_name
            )
        except S3Error as e:
            logger.error(f"Failed to get stats for object {object_name}: {str(e)}")
            raise

    async def list_objects(self, bucket_name: str, prefix: Optional[str] = None, recursive: bool = True) -> list:
        """List objects in MinIO"""
        try:
            objects = self.client.list_objects(
                bucket_name=bucket_name,
                prefix=prefix,
                recursive=recursive
            )
            return list(objects)
        except S3Error as e:
            logger.error(f"Failed to list objects: {str(e)}")
            raise

    async def upload_file(self, bucket_name: str, object_name: str, file_path: str) -> None:
        """Upload a file to MinIO from a file path"""
        try:
            self.client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path
            )
        except S3Error as e:
            logger.error(f"Failed to upload file: {str(e)}")
            raise

    async def upload_fileobj(self, bucket_name: str, object_name: str, file: BinaryIO) -> None:
        """Upload a file to MinIO from a file object"""
        try:
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=file,
                length=-1,
                part_size=10*1024*1024
            )
        except S3Error as e:
            logger.error(f"Failed to upload file: {str(e)}")
            raise

    async def download_file(self, bucket_name: str, object_name: str) -> BinaryIO:
        """Download a file from MinIO"""
        try:
            return self.client.get_object(
                bucket_name=bucket_name,
                object_name=object_name
            )
        except S3Error as e:
            logger.error(f"Failed to download file: {str(e)}")
            raise

    async def delete_file(self, bucket_name: str, object_name: str) -> None:
        """Delete a file from MinIO"""
        try:
            self.client.remove_object(
                bucket_name=bucket_name,
                object_name=object_name
            )
        except S3Error as e:
            logger.error(f"Failed to delete file: {str(e)}")
            raise

    async def delete_files(self, bucket_name: str, object_names: list[str]) -> None:
        """Delete multiple files from MinIO"""
        try:
            delete_objects = [DeleteObject(name) for name in object_names]
            errors = self.client.remove_objects(bucket_name, delete_objects)
            
            for error in errors:
                logger.error(f"Failed to delete object: {error}")
        except S3Error as e:
            logger.error(f"Failed to delete files: {str(e)}")
            raise

    async def get_presigned_put_url(self, bucket_name: str, object_name: str, expires: int = 3600) -> str:
        """Get presigned URL for file upload"""
        try:
            return self.client.presigned_put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expires
            )
        except S3Error as e:
            logger.error(f"Failed to get presigned put URL: {str(e)}")
            raise

    async def get_presigned_get_url(self, bucket_name: str, object_name: str, expires: int = 3600) -> str:
        """Get presigned URL for file download"""
        try:
            return self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expires
            )
        except S3Error as e:
            logger.error(f"Failed to get presigned get URL: {str(e)}")
            raise

@lru_cache()
def get_minio_client() -> MinioClient:
    """Get MinIO client instance"""
    try:
        return MinioClient()
    except Exception as e:
        logger.error(f"Failed to create MinIO client: {str(e)}")
        raise
