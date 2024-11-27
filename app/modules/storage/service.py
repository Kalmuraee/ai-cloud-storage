"""
Storage service module
"""
from typing import Optional, List, Dict, Any, Tuple, BinaryIO
from datetime import datetime
import hashlib
import os
import uuid
import secrets
from sqlalchemy.exc import IntegrityError

from fastapi import UploadFile
from app.core.minio import MinioClient
from app.core.logging import get_logger
from app.core.config import settings
from app.core.events import event_bus
from app.core.exceptions import (
    NotFoundException,
    ValidationError,
    StorageError,
    PermissionError,
    ConflictError
)
from app.modules.storage.repository import StorageRepository
from app.modules.storage.models import File, FileStatus, ShareStatus, SharedItem
from app.modules.storage.schemas import (
    FileCreate,
    FileUpdate,
    FolderCreate,
    FolderUpdate,
    FileVersionCreate,
    FileMetadataCreate,
    SharedItemInDB,
    FileUploadResponse,
    FileMetadata,
    ShareItemRequest
)

logger = get_logger(__name__)

class StorageService:
    """Service for handling file storage operations"""
    
    def __init__(self, repo: StorageRepository, minio_client: MinioClient):
        self.repo = repo
        self.minio_client = minio_client
        self.db = repo.db  # Add db reference from repo
        self.chunk_size = 8 * 1024 * 1024  # 8MB chunks for large files

    async def compute_file_hash(self, file_path: str) -> str:
        """
        Compute SHA-256 hash of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: SHA-256 hash of the file
            
        Raises:
            StorageError: If file cannot be read
        """
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(self.chunk_size), b""):
                    sha256_hash.update(byte_block)
                    
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute file hash: {str(e)}")
            raise StorageError(f"Failed to compute file hash: {str(e)}")

    async def upload_file(
        self,
        upload_file: UploadFile,
        owner_id: int,
        folder_id: Optional[int] = None,
        check_duplicates: bool = True
    ) -> FileUploadResponse:
        """
        Upload a file
        
        Args:
            upload_file: FastAPI UploadFile object
            owner_id: ID of the file owner
            folder_id: Optional folder ID to place the file in
            check_duplicates: Whether to check for duplicates
            
        Returns:
            FileUploadResponse: Upload response with file info
            
        Raises:
            StorageError: If upload fails
            ValidationError: If input is invalid
        """
        try:
            # Check duplicates if requested
            if check_duplicates:
                duplicates = await self.repo.get_duplicate_files_by_user(owner_id)
                if duplicates:
                    return FileUploadResponse(
                        file=duplicates[0],
                        is_duplicate=True,
                        duplicate_of=duplicates[0].id
                    )

            # Create file record
            file_data = FileCreate(
                filename=upload_file.filename,
                original_filename=upload_file.filename,
                content_type=upload_file.content_type,
                owner_id=owner_id,
                folder_id=folder_id,
                status=FileStatus.UPLOADING,
                path=f"{owner_id}/{uuid.uuid4()}/{upload_file.filename}",
                bucket=settings.MINIO_BUCKET,
                size=0  # Will be updated after upload
            )
            
            file = await self.repo.create_file(file_data)
            
            try:
                # Upload to MinIO
                content = await upload_file.read()
                await self.minio_client.upload_file(
                    bucket=file.bucket,
                    path=file.path,
                    content=content,
                    content_type=file.content_type
                )
                
                # Update file size and status
                file.size = len(content)
                file.status = FileStatus.PROCESSING
                await self.repo.update_file(file.id, FileUpdate(
                    size=file.size,
                    status=file.status
                ))
                
                # Trigger AI processing
                await event_bus.publish(
                    "file.uploaded",
                    {
                        "file_id": file.id,
                        "tasks": ["analyze_content", "extract_metadata"]
                    }
                )
                
                return FileUploadResponse(
                    file=file,
                    is_duplicate=False
                )
                
            except Exception as e:
                # Cleanup on upload failure
                if file.id:
                    await self.repo.delete_file(file.id)
                raise StorageError(f"Failed to upload file: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise StorageError(f"Failed to create file record: {str(e)}")

    async def download_file(self, file_path: str, user_id: int) -> BinaryIO:
        """
        Download a file
        
        Args:
            file_path: Path of the file to download
            user_id: ID of the user requesting download
            
        Returns:
            BinaryIO: File stream
            
        Raises:
            NotFoundException: If file not found
            PermissionError: If user doesn't have access
            StorageError: If download fails
        """
        try:
            # Input validation
            if not file_path:
                raise ValidationError("File path is required")
                
            if not user_id:
                raise ValidationError("User ID is required")
            
            # Get file metadata
            file = await self.repo.get_file_by_path(file_path, user_id)
            if not file:
                raise NotFoundException(f"File not found: {file_path}")
                
            if file.status != FileStatus.PROCESSED:
                raise NotFoundException(f"File is not processed: {file_path}")
            
            # Check permissions
            if file.owner_id != user_id:
                # Check if file is shared with user
                try:
                    shared_items = await self.repo.get_shared_items(user_id)
                    if not any(item.file_id == file.id and item.status == ShareStatus.ACTIVE for item in shared_items):
                        raise PermissionError("You don't have access to this file")
                except Exception as e:
                    logger.error(f"Failed to check file sharing permissions: {str(e)}")
                    raise StorageError("Failed to verify file access permissions")
            
            # Get file from storage
            try:
                return await self.minio_client.get_object(
                    bucket_name=file.bucket,
                    object_name=file.path
                )
            except Exception as e:
                logger.error(f"Failed to get file from storage: {str(e)}")
                raise StorageError("Failed to retrieve file from storage")
                
        except (ValidationError, NotFoundException, PermissionError):
            raise
        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
            raise StorageError(f"Failed to download file: {str(e)}")

    async def delete_file(self, *, file_id: int, user_id: int) -> None:
        """
        Delete a file
        
        Args:
            file_id: ID of the file to delete
            user_id: ID of the user requesting deletion
            
        Raises:
            NotFoundException: If file not found
            PermissionError: If user doesn't have permission
            StorageError: If deletion fails
        """
        try:
            # Input validation
            if not file_id:
                raise ValidationError("File ID is required")
                
            if not user_id:
                raise ValidationError("User ID is required")
            
            # Get file metadata
            file = await self.repo.get_file_by_id(file_id)
            if not file:
                raise NotFoundException(f"File not found: {file_id}")
                
            if file.status == FileStatus.DELETED:
                return  # Already deleted
            
            # Check permissions
            if file.owner_id != user_id:
                raise PermissionError("You don't have permission to delete this file")
            
            # Delete from storage first
            try:
                await self.minio_client.remove_object(
                    bucket_name=file.bucket,
                    object_name=file.path
                )
            except Exception as e:
                logger.error(f"Failed to delete file from storage: {str(e)}")
                raise StorageError("Failed to delete file from storage")
            
            # Delete file record
            await self.repo.delete_file(file_id)
            
            # Publish file deleted event
            try:
                await event_bus.publish("file.deleted", {
                    "file_id": file_id,
                    "owner_id": user_id,
                    "path": file.path
                })
            except Exception as e:
                logger.error(f"Failed to publish file deleted event: {str(e)}")
                # Continue since this is not critical
                
        except (ValidationError, NotFoundException, PermissionError):
            raise
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            raise StorageError(f"Failed to delete file: {str(e)}")

    async def get_storage_usage(self, user_id: int) -> Dict[str, Any]:
        """
        Get storage usage statistics for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict[str, Any]: Storage usage statistics
            
        Raises:
            StorageError: If statistics cannot be calculated
        """
        try:
            return await self.repo.get_storage_usage(user_id)
        except Exception as e:
            logger.error(f"Failed to get storage usage: {str(e)}")
            raise StorageError(f"Failed to get storage usage: {str(e)}")

    async def search_files(
        self,
        owner_id: int,
        query: str,
        file_type: Optional[str] = None,
        folder_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[File], int]:
        """
        Search files by various criteria
        
        Args:
            owner_id: ID of the file owner
            query: Search query
            file_type: Optional file type filter
            folder_id: Optional folder filter
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Tuple[List[File], int]: List of files and total count
            
        Raises:
            ValidationError: If search parameters are invalid
            StorageError: If search fails
        """
        try:
            return await self.repo.search_files(
                owner_id=owner_id,
                query=query,
                file_type=file_type,
                folder_id=folder_id,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Failed to search files: {str(e)}")
            raise StorageError(f"Failed to search files: {str(e)}")

    async def list_files(
        self,
        user_id: int,
        prefix: Optional[str] = None,
        recursive: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[File], int]:
        """List files for a user"""
        try:
            if not user_id:
                raise ValidationError("User ID is required")
                
            files, total = await self.repo.list_files_by_user(
                owner_id=user_id,
                prefix=prefix,
                recursive=recursive,
                limit=limit,
                offset=offset
            )
            
            return files, total
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            raise StorageError(f"Failed to list files: {str(e)}")

    async def get_duplicate_files(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get duplicate files for a user"""
        try:
            if not user_id:
                raise ValidationError("User ID is required")
                
            duplicates, total = await self.repo.get_duplicate_files_by_user(
                owner_id=user_id,
                limit=limit,
                offset=offset
            )
            
            return duplicates, total
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get duplicate files: {str(e)}")
            raise StorageError(f"Failed to get duplicate files: {str(e)}")

    async def create_file_metadata(self, metadata: FileMetadataCreate) -> FileMetadata:
        """Create file metadata"""
        try:
            if not metadata:
                raise ValidationError("Metadata is required")
                
            if not metadata.file_id:
                raise ValidationError("File ID is required")
                
            return await self.repo.create_file_metadata(metadata)
        except (ValidationError, ConflictError):
            raise
        except Exception as e:
            logger.error(f"Failed to create file metadata: {str(e)}")
            raise StorageError(f"Failed to create file metadata: {str(e)}")

    async def get_file_metadata(self, file_id: int) -> Optional[FileMetadata]:
        """Get file metadata"""
        try:
            if not file_id:
                raise ValidationError("File ID is required")
                
            file = await self.repo.get_file_by_id(file_id, with_metadata=True)
            if not file:
                raise NotFoundException(f"File with ID {file_id} not found")
                
            if not file.file_metadata:
                return None
                
            return file.file_metadata[0] if file.file_metadata else None
        except (ValidationError, NotFoundException):
            raise
        except Exception as e:
            logger.error(f"Failed to get file metadata: {str(e)}")
            raise StorageError(f"Failed to get file metadata: {str(e)}")

    async def get_shared_items(self, user_id: int) -> List[SharedItemInDB]:
        """
        Get all active shared items for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            List[SharedItemInDB]: List of active shared items
            
        Raises:
            ValidationError: If user ID is invalid
            StorageError: If shared items cannot be retrieved
        """
        try:
            if not user_id:
                raise ValidationError("User ID is required")
                
            return await self.repo.get_shared_items(user_id)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get shared items: {str(e)}")
            raise StorageError(f"Failed to get shared items: {str(e)}")

    async def update_file_status(self, file_id: int, status: FileStatus) -> None:
        """
        Update the status of a file
        
        Args:
            file_id: ID of the file to update
            status: New file status
            
        Raises:
            ValidationError: If file ID or status is invalid
            NotFoundException: If file not found
            StorageError: If status update fails
        """
        try:
            if not file_id:
                raise ValidationError("File ID is required")
                
            if not status:
                raise ValidationError("Status is required")
                
            # Check if file exists
            file = await self.repo.get_file_by_id(file_id)
            if not file:
                raise NotFoundException(f"File not found: {file_id}")
                
            await self.repo.update_file_status(file_id, status)
            
            # Publish file status updated event
            try:
                await event_bus.publish("file_status_updated", {
                    "file_id": file_id,
                    "old_status": file.status,
                    "new_status": status
                })
            except Exception as e:
                logger.error(f"Failed to publish file status updated event: {str(e)}")
                # Continue since this is not critical
                
        except (ValidationError, NotFoundException):
            raise
        except Exception as e:
            logger.error(f"Failed to update file status: {str(e)}")
            raise StorageError(f"Failed to update file status: {str(e)}")

    async def share_file(self, file_id: int, owner_id: int, share: ShareItemRequest) -> SharedItemInDB:
        """Share a file with another user"""
        try:
            # First verify file exists and user has permission
            file = await self.repo.get_file_by_id(file_id)
            if not file:
                raise NotFoundException(f"File {file_id} not found")
                
            if file.owner_id != owner_id:
                raise PermissionError("You don't have permission to share this file")
                
            # Create share record
            share_data = {
                "file_id": file_id,
                "owner_id": owner_id,
                "shared_with_id": None,  # For public share links
                "status": ShareStatus.PENDING,
                "share_link": secrets.token_urlsafe(32) if share.public else None
            }
            
            try:
                shared_item = await self.repo.create_shared_item(SharedItem(**share_data))
                return SharedItemInDB.from_orm(shared_item)
            except IntegrityError as e:
                logger.error(f"Failed to create share: {str(e)}")
                raise StorageError("Failed to create share: duplicate or invalid data")
        except (ValidationError, NotFoundException, PermissionError):
            raise
        except Exception as e:
            logger.error(f"Failed to share file: {str(e)}")
            raise StorageError(f"Failed to share file: {str(e)}")
