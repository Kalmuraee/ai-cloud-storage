"""
MinIO client module for object storage operations
"""
from typing import BinaryIO, Optional
from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.core.exceptions import StorageError

class MinioClient:
    """MinIO client wrapper for object storage operations"""
    
    def __init__(self):
        """Initialize MinIO client"""
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_USE_SSL
            )
            
            # Ensure bucket exists
            if not self.client.bucket_exists(settings.MINIO_BUCKET_NAME):
                self.client.make_bucket(settings.MINIO_BUCKET_NAME)
                
        except Exception as e:
            raise StorageError(f"Failed to initialize MinIO client: {str(e)}")
    
    async def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        length: int,
        content_type: Optional[str] = None
    ) -> None:
        """
        Upload an object to MinIO storage
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            data: File-like object containing the data
            length: Size of the data in bytes
            content_type: MIME type of the object
        
        Raises:
            StorageError: If upload fails
        """
        try:
            await self.client.put_object(
                bucket_name,
                object_name,
                data,
                length,
                content_type=content_type
            )
        except S3Error as e:
            raise StorageError(f"Failed to upload object: {str(e)}")
    
    async def get_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> BinaryIO:
        """
        Download an object from MinIO storage
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            
        Returns:
            BinaryIO: File-like object containing the data
            
        Raises:
            StorageError: If download fails
        """
        try:
            return await self.client.get_object(bucket_name, object_name)
        except S3Error as e:
            raise StorageError(f"Failed to download object: {str(e)}")
    
    async def remove_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> None:
        """
        Remove an object from MinIO storage
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            
        Raises:
            StorageError: If removal fails
        """
        try:
            await self.client.remove_object(bucket_name, object_name)
        except S3Error as e:
            raise StorageError(f"Failed to remove object: {str(e)}")
    
    async def stat_object(
        self,
        bucket_name: str,
        object_name: str
    ):
        """
        Get object statistics
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
            
        Returns:
            ObjectStat: Object statistics
            
        Raises:
            StorageError: If operation fails
        """
        try:
            return await self.client.stat_object(bucket_name, object_name)
        except S3Error as e:
            raise StorageError(f"Failed to get object stats: {str(e)}")
