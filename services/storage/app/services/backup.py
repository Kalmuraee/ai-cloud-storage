from datetime import datetime
import asyncio
import logging
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError
import tempfile
import os
import json

from app.core.config import settings
from app.services.minio import minio_service

class BackupService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

    async def create_backup(self, bucket_name: Optional[str] = None) -> str:
        """Create a backup of one or all buckets."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_id = f"backup_{timestamp}"
            
            if bucket_name:
                await self._backup_bucket(bucket_name, backup_id)
            else:
                buckets = await minio_service.list_buckets()
                for bucket in buckets:
                    await self._backup_bucket(bucket.name, backup_id)
            
            return backup_id
        
        except Exception as e:
            self.logger.error(f"Backup failed: {str(e)}")
            raise

    async def restore_backup(self, backup_id: str, bucket_name: Optional[str] = None) -> None:
        """Restore from a backup."""
        try:
            # List backup objects
            prefix = f"{backup_id}/{bucket_name}" if bucket_name else backup_id
            response = self.s3_client.list_objects_v2(
                Bucket=settings.AWS_BACKUP_BUCKET,
                Prefix=prefix
            )
            
            for obj in response.get('Contents', []):
                # Extract bucket and object names from backup path
                parts = obj['Key'].split('/', 2)
                if len(parts) < 3:
                    continue
                    
                _, bucket, object_name = parts
                
                if bucket_name and bucket != bucket_name:
                    continue
                
                # Download from backup
                with tempfile.NamedTemporaryFile() as tmp:
                    self.s3_client.download_file(
                        settings.AWS_BACKUP_BUCKET,
                        obj['Key'],
                        tmp.name
                    )
                    
                    # Restore to MinIO
                    with open(tmp.name, 'rb') as f:
                        await minio_service.restore_object(bucket, object_name, f)
        
        except Exception as e:
            self.logger.error(f"Restore failed: {str(e)}")
            raise

    async def list_backups(self) -> List[dict]:
        """List available backups."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=settings.AWS_BACKUP_BUCKET,
                Delimiter='/'
            )
            
            backups = []
            for prefix in response.get('CommonPrefixes', []):
                backup_id = prefix['Prefix'].rstrip('/')
                # Get backup metadata
                try:
                    metadata = self.s3_client.get_object(
                        Bucket=settings.AWS_BACKUP_BUCKET,
                        Key=f"{backup_id}/metadata.json"
                    )
                    backup_info = json.loads(metadata['Body'].read().decode())
                except:
                    backup_info = {}
                
                backups.append({
                    'backup_id': backup_id,
                    'created_at': backup_info.get('created_at'),
                    'size': backup_info.get('total_size', 0),
                    'bucket_count': backup_info.get('bucket_count', 0),
                    'object_count': backup_info.get('object_count', 0)
                })
            
            return backups
        
        except Exception as e:
            self.logger.error(f"Failed to list backups: {str(e)}")
            raise

    async def _backup_bucket(self, bucket_name: str, backup_id: str) -> None:
        """Backup a single bucket."""
        try:
            # Get bucket objects
            objects = await minio_service.list_objects(bucket_name)
            
            total_size = 0
            object_count = 0
            
            for obj in objects:
                # Download object from MinIO
                data, content_type, _ = await minio_service.download_file(
                    bucket_name,
                    obj.name
                )
                
                # Upload to backup storage
                backup_key = f"{backup_id}/{bucket_name}/{obj.name}"
                self.s3_client.upload_fileobj(
                    data,
                    settings.AWS_BACKUP_BUCKET,
                    backup_key,
                    ExtraArgs={'ContentType': content_type}
                )
                
                total_size += obj.size
                object_count += 1
            
            # Store backup metadata
            metadata = {
                'created_at': datetime.now().isoformat(),
                'bucket': bucket_name,
                'total_size': total_size,
                'object_count': object_count
            }
            
            self.s3_client.put_object(
                Bucket=settings.AWS_BACKUP_BUCKET,
                Key=f"{backup_id}/metadata.json",
                Body=json.dumps(metadata),
                ContentType='application/json'
            )
        
        except Exception as e:
            self.logger.error(f"Failed to backup bucket {bucket_name}: {str(e)}")
            raise

backup_service = BackupService()