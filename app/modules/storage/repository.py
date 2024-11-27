"""
Storage repository implementation
"""
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
import logging

from app.core.exceptions import (
    NotFoundException,
    DatabaseError,
    ConflictError,
    ValidationError
)
from app.modules.storage.models import (
    File,
    Folder,
    FileVersion,
    SharedItem,
    FileMetadata,
    FileTag,
    FolderCollaborator,
    FileStatus,
    ShareStatus
)
from app.modules.storage.schemas import (
    FileCreate,
    FileUpdate,
    FolderCreate,
    FolderUpdate,
    FileVersionCreate,
    FileMetadataCreate,
    SharedItemInDB
)

logger = logging.getLogger(__name__)

class StorageRepository:
    """Repository for storage-related database operations"""
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_file_by_id(self, file_id: int, with_metadata: bool = False) -> Optional[File]:
        """Get file by ID with optional metadata"""
        try:
            if not file_id:
                raise ValidationError("File ID is required")
                
            query = select(File)
            if with_metadata:
                query = query.options(
                    selectinload(File.file_metadata),
                    selectinload(File.file_versions),
                    selectinload(File.file_tags)
                )
            query = query.where(
                and_(
                    File.id == file_id,
                    File.status != FileStatus.DELETED
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except ValidationError:
            raise
        except Exception as e:
            raise DatabaseError(f"Error fetching file by ID: {str(e)}")

    async def get_file_by_path(self, path: str, owner_id: int) -> Optional[File]:
        """Get file by path and owner ID"""
        try:
            if not path:
                raise ValidationError("File path is required")
                
            if not owner_id:
                raise ValidationError("Owner ID is required")
                
            query = select(File).where(
                and_(
                    File.path == path,
                    File.owner_id == owner_id,
                    File.status != FileStatus.DELETED
                )
            ).options(
                selectinload(File.file_metadata),
                selectinload(File.file_versions)
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except ValidationError:
            raise
        except Exception as e:
            raise DatabaseError(f"Error fetching file by path: {str(e)}")

    async def create_file(self, file_data: FileCreate) -> File:
        """Create a new file"""
        try:
            if not file_data:
                raise ValidationError("File data is required")
            file = File(**file_data.model_dump())
            self.db.add(file)
            await self.db.commit()
            await self.db.refresh(file)
            return file
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error creating file: {str(e)}")

    async def update_file(self, file_id: int, file_data: FileUpdate) -> File:
        """Update file details"""
        try:
            if not file_id:
                raise ValidationError("File ID is required")
                
            if not file_data:
                raise ValidationError("File data is required")

            file = await self.get_file_by_id(file_id)
            if not file:
                raise NotFoundException(f"File with ID {file_id} not found")
                
            if file.status == FileStatus.DELETED:
                raise NotFoundException(f"File with ID {file_id} is deleted")

            update_data = file_data.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            for key, value in update_data.items():
                setattr(file, key, value)

            await self.db.commit()
            await self.db.refresh(file)
            return file
            
        except (ValidationError, NotFoundException):
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error updating file: {str(e)}")

    async def delete_file(self, file_id: int) -> None:
        """Delete a file"""
        try:
            if not file_id:
                raise ValidationError("File ID is required")

            file = await self.get_file_by_id(file_id)
            if not file:
                raise NotFoundException(f"File with ID {file_id} not found")
                
            if file.status == FileStatus.DELETED:
                return  # Already deleted

            # Soft delete
            file.status = FileStatus.DELETED
            file.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
        except (ValidationError, NotFoundException):
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error deleting file: {str(e)}")

    async def get_folder_by_id(self, folder_id: int) -> Optional[Folder]:
        """Get folder by ID"""
        try:
            query = select(Folder).options(
                selectinload(Folder.files),
                selectinload(Folder.subfolders)
            ).where(Folder.id == folder_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"Error fetching folder by ID: {str(e)}")

    async def get_folder_by_path(self, path: str, owner_id: int) -> Optional[Folder]:
        """Get folder by path and owner ID"""
        try:
            query = select(Folder).where(
                and_(
                    Folder.path == path,
                    Folder.owner_id == owner_id
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"Error fetching folder by path: {str(e)}")

    async def create_folder(self, folder_data: FolderCreate) -> Folder:
        """Create a new folder"""
        try:
            # Check if folder already exists in the same path
            existing_folder = await self.get_folder_by_path(folder_data.path, folder_data.owner_id)
            if existing_folder:
                raise ConflictError(f"Folder already exists at path: {folder_data.path}")

            folder = Folder(**folder_data.model_dump())
            self.db.add(folder)
            await self.db.commit()
            await self.db.refresh(folder)
            return folder
        except ConflictError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error creating folder: {str(e)}")

    async def update_folder(self, folder_id: int, folder_data: FolderUpdate) -> Folder:
        """Update folder details"""
        try:
            folder = await self.get_folder_by_id(folder_id)
            if not folder:
                raise NotFoundException(f"Folder with ID {folder_id} not found")

            update_data = folder_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(folder, key, value)

            await self.db.commit()
            await self.db.refresh(folder)
            return folder
        except NotFoundException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error updating folder: {str(e)}")

    async def delete_folder(self, folder_id: int) -> None:
        """Delete a folder"""
        try:
            folder = await self.get_folder_by_id(folder_id)
            if not folder:
                raise NotFoundException(f"Folder with ID {folder_id} not found")

            # Check if folder is empty
            if folder.files or folder.subfolders:
                raise ValidationError("Cannot delete non-empty folder")

            await self.db.delete(folder)
            await self.db.commit()
        except (NotFoundException, ValidationError):
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error deleting folder: {str(e)}")

    async def create_file_version(self, version_data: FileVersionCreate) -> FileVersion:
        """Create a new file version"""
        try:
            version = FileVersion(**version_data.model_dump())
            self.db.add(version)
            await self.db.commit()
            await self.db.refresh(version)
            return version
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error creating file version: {str(e)}")

    async def get_file_versions(self, file_id: int) -> List[FileVersion]:
        """Get all versions of a file"""
        try:
            query = select(FileVersion).where(
                FileVersion.file_id == file_id
            ).order_by(FileVersion.version.desc())
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Error fetching file versions: {str(e)}")

    async def create_file_metadata(self, metadata: FileMetadataCreate) -> FileMetadata:
        """Create file metadata"""
        try:
            if not metadata:
                raise ValidationError("Metadata is required")
                
            if not metadata.file_id:
                raise ValidationError("File ID is required")
                
            # Check if metadata already exists
            existing = await self.db.execute(
                select(FileMetadata).where(FileMetadata.file_id == metadata.file_id)
            )
            if existing.scalar_one_or_none():
                raise ConflictError(f"Metadata already exists for file {metadata.file_id}")
            
            file_metadata = FileMetadata(**metadata.model_dump())
            file_metadata.created_at = datetime.utcnow()
            
            self.db.add(file_metadata)
            await self.db.commit()
            await self.db.refresh(file_metadata)
            
            return file_metadata
            
        except (ValidationError, ConflictError):
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error creating file metadata: {str(e)}")

    async def list_files_by_user(
        self,
        owner_id: int,
        prefix: Optional[str] = None,
        recursive: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[File], int]:
        """List files for a user with pagination"""
        try:
            if not owner_id:
                raise ValidationError("Owner ID is required")
            
            if limit < 0:
                limit = 100
            if offset < 0:
                offset = 0

            filters = [
                and_(
                    File.owner_id == owner_id,
                    File.status == FileStatus.PROCESSED,
                    File.is_latest == True
                )
            ]
            
            if prefix:
                if recursive:
                    filters.append(File.path.like(f"{prefix}%"))
                else:
                    filters.append(File.path.like(f"{prefix}/%"))
                    filters.append(~File.path.like(f"{prefix}/%/%"))
            
            # Base query for files
            query = select(File).where(and_(*filters))
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.db.scalar(count_query)
            
            # Add sorting and pagination
            query = query.order_by(File.path).offset(offset).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            files = list(result.scalars().all())
            
            return files, total
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            raise DatabaseError(f"Error listing files: {str(e)}")

    async def get_duplicate_files_by_user(self, owner_id: int) -> List[File]:
        """Get duplicate files for a user based on checksum"""
        try:
            if not owner_id:
                raise ValidationError("Owner ID is required")

            # First get the checksums that have duplicates
            subquery = (
                select(File.checksum)
                .where(
                    and_(
                        File.owner_id == owner_id,
                        File.status != FileStatus.DELETED,
                        File.checksum.isnot(None)
                    )
                )
                .group_by(File.checksum)
                .having(func.count(File.checksum) > 1)
            )
            
            # Then get all files with those checksums
            query = (
                select(File)
                .where(
                    and_(
                        File.owner_id == owner_id,
                        File.status != FileStatus.DELETED,
                        File.checksum.in_(subquery)
                    )
                )
            )
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except ValidationError:
            raise
        except Exception as e:
            raise DatabaseError(f"Error fetching duplicate files: {str(e)}")

    async def get_file_metadata(self, file_id: int) -> Optional[FileMetadata]:
        """Get metadata for a file"""
        try:
            query = select(FileMetadata).where(FileMetadata.file_id == file_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"Error fetching file metadata: {str(e)}")

    async def get_shared_items(self, user_id: int) -> List[SharedItem]:
        """Get all active shared items for a user"""
        try:
            if not user_id:
                raise ValidationError("User ID is required")

            query = select(SharedItem).where(
                and_(
                    SharedItem.shared_with_id == user_id,
                    SharedItem.status == ShareStatus.ACCEPTED
                )
            ).options(
                joinedload(SharedItem.file)
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except ValidationError:
            raise
        except Exception as e:
            raise DatabaseError(f"Error fetching shared items: {str(e)}")

    async def get_shared_items_by_file(self, file_id: int) -> List[SharedItem]:
        """Get shared items for a specific file"""
        try:
            if not file_id:
                raise ValidationError("File ID is required")
                
            query = select(SharedItem).where(
                and_(
                    SharedItem.file_id == file_id,
                    SharedItem.status != ShareStatus.DELETED
                )
            ).options(
                joinedload(SharedItem.file),
                joinedload(SharedItem.owner),
                joinedload(SharedItem.shared_with)
            )
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Error fetching shared items: {str(e)}")

    async def delete_shared_item(self, share_id: int) -> None:
        """Delete a shared item"""
        try:
            if not share_id:
                raise ValidationError("Share ID is required")
                
            query = update(SharedItem).where(
                SharedItem.id == share_id
            ).values({
                SharedItem.status: ShareStatus.DECLINED,
                SharedItem.updated_at: datetime.utcnow()
            })
            await self.db.execute(query)
            await self.db.commit()
        except ValidationError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error deleting shared item: {str(e)}")

    async def get_duplicate_files(self, content_hash: str) -> List[File]:
        """Get all active files with the same content hash"""
        try:
            if not content_hash:
                raise ValidationError("Content hash is required")
                
            query = select(File).join(
                FileMetadata,
                FileMetadata.file_id == File.id
            ).where(
                and_(
                    FileMetadata.content_hash == content_hash,
                    File.status == FileStatus.ACTIVE
                )
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except ValidationError:
            raise
        except Exception as e:
            raise DatabaseError(f"Error fetching duplicate files: {str(e)}")

    async def delete_file_metadata(self, file_id: int) -> None:
        """Delete file metadata"""
        try:
            if not file_id:
                raise ValidationError("File ID is required")
                
            query = update(FileMetadata).where(
                FileMetadata.file_id == file_id
            ).values(
                deleted_at=datetime.utcnow()
            )
            await self.db.execute(query)
            await self.db.commit()
        except ValidationError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error deleting file metadata: {str(e)}")

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
        Returns tuple of (files, total_count)
        """
        try:
            # Base query
            query_filter = and_(
                File.owner_id == owner_id,
                File.is_latest == True,
                or_(
                    File.filename.ilike(f"%{query}%"),
                    File.path.ilike(f"%{query}%")
                )
            )

            # Add optional filters
            if file_type:
                query_filter = and_(query_filter, File.content_type == file_type)
            if folder_id:
                query_filter = and_(query_filter, File.folders.any(Folder.id == folder_id))

            # Count total results
            count_query = select(func.count()).select_from(File).where(query_filter)
            total = await self.db.scalar(count_query)

            # Get paginated results
            files_query = select(File).where(query_filter).options(
                selectinload(File.file_metadata)
            ).order_by(
                File.created_at.desc()
            ).offset(offset).limit(limit)

            result = await self.db.execute(files_query)
            files = list(result.scalars().all())

            return files, total
        except Exception as e:
            raise DatabaseError(f"Error searching files: {str(e)}")

    async def get_storage_usage(self, owner_id: int) -> Dict[str, Any]:
        """Get storage usage statistics for a user"""
        try:
            # Get total size of all files
            size_query = select(func.sum(File.size)).where(
                and_(
                    File.owner_id == owner_id,
                    File.is_latest == True
                )
            )
            total_size = await self.db.scalar(size_query) or 0

            # Get count of files by type
            type_query = select(
                File.content_type,
                func.count(File.id)
            ).where(
                and_(
                    File.owner_id == owner_id,
                    File.is_latest == True
                )
            ).group_by(File.content_type)
            
            result = await self.db.execute(type_query)
            type_counts = dict(result.all())

            return {
                "total_size": total_size,
                "file_count": sum(type_counts.values()),
                "type_distribution": type_counts
            }
        except Exception as e:
            raise DatabaseError(f"Error calculating storage usage: {str(e)}")

    async def create_shared_item(
        self, 
        shared_item: SharedItem
    ) -> SharedItem:
        """Create a new shared item"""
        try:
            self.db.add(shared_item)
            await self.db.commit()
            await self.db.refresh(shared_item)
            return shared_item
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error creating shared item: {str(e)}")

    async def update_file_status(self, file_id: int, status: FileStatus) -> None:
        """Update file status"""
        try:
            query = update(File).where(File.id == file_id).values(status=status)
            await self.db.execute(query)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error updating file status: {str(e)}")
