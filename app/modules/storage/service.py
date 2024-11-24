"""
Storage service module
"""
from typing import Optional, List, Dict, Any, Tuple, BinaryIO
from datetime import datetime
import hashlib
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, UploadFile

from app.core.minio import MinioClient
from app.modules.storage.models import File, Folder, FileMetadata, FileVersion
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

class StorageService:
    """Service for handling file storage operations"""
    def __init__(self, db: AsyncSession, minio_client: MinioClient):
        self.db = db
        self.minio_client = minio_client
        self.chunk_size = 8 * 1024 * 1024  # 8MB chunks for large files

    async def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(self.chunk_size), b""):
                sha256_hash.update(byte_block)
                
        return sha256_hash.hexdigest()

    async def find_duplicate(self, content_hash: str) -> Optional[File]:
        """Find a duplicate file based on content hash"""
        query = select(File).join(FileMetadata).where(FileMetadata.content_hash == content_hash)
        result = await self.db.execute(query)
        duplicate = result.scalar_one_or_none()
        return duplicate

    async def upload_file(
        self, 
        file_path: str,
        owner_id: int,
        filename: str,
        content_type: str,
        folder_id: Optional[int] = None,
        check_duplicates: bool = True
    ) -> Tuple[File, bool]:
        """Upload a file with optional deduplication"""
        if check_duplicates:
            # Compute file hash
            content_hash = await self.compute_file_hash(file_path)
            
            # Check for existing duplicate
            duplicate = await self.find_duplicate(content_hash)
            
            if duplicate:
                # Create new file entry pointing to existing content
                new_file = await self.create_file(
                    owner_id=owner_id,
                    filename=filename,
                    original_filename=filename,
                    content_type=content_type,
                    size=duplicate.size,
                    bucket=duplicate.bucket,
                    path=duplicate.path,
                )
                
                # Create metadata entry with same hash
                await self.create_file_metadata(
                    file_id=new_file.id,
                    content_hash=content_hash
                )
                
                return new_file, True
        
        # No duplicate found or deduplication disabled, proceed with normal upload
        new_file = await self._upload_file_internal(
            file_path=file_path,
            owner_id=owner_id,
            filename=filename,
            content_type=content_type
        )
        
        if check_duplicates:
            # Create metadata entry with hash
            await self.create_file_metadata(
                file_id=new_file.id,
                content_hash=await self.compute_file_hash(file_path)
            )
        
        return new_file, False

    async def _upload_file_internal(
        self,
        file_path: str,
        owner_id: int,
        filename: str,
        content_type: str
    ) -> File:
        """Internal method for file upload without deduplication"""
        # Upload to MinIO
        bucket_name = settings.MINIO_BUCKET
        object_name = f"{owner_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        
        await self.minio_client.upload_file(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=file_path
        )
        
        # Get file size
        file_stat = await self.minio_client.stat_object(bucket_name, object_name)
        
        # Create file record
        file = File(
            filename=filename,
            original_filename=filename,
            content_type=content_type,
            size=file_stat.size,
            bucket=bucket_name,
            path=object_name,
            owner_id=owner_id
        )
        
        self.db.add(file)
        await self.db.commit()
        await self.db.refresh(file)
        
        return file

    async def create_file(
        self,
        owner_id: int,
        filename: str,
        original_filename: str,
        content_type: str,
        size: int,
        bucket: str,
        path: str
    ) -> File:
        """Create a new file record pointing to existing content"""
        file = File(
            filename=filename,
            original_filename=original_filename,
            content_type=content_type,
            size=size,
            bucket=bucket,
            path=path,
            owner_id=owner_id
        )
        
        self.db.add(file)
        await self.db.commit()
        await self.db.refresh(file)
        
        return file

    async def create_file_metadata(
        self,
        file_id: int,
        content_hash: str,
        content_summary: Optional[str] = None,
        content_type_detected: Optional[str] = None,
        language_detected: Optional[str] = None,
        tags: Optional[str] = None,
        embedding: Optional[str] = None
    ) -> FileMetadata:
        """Create metadata for a file"""
        metadata = FileMetadata(
            file_id=file_id,
            content_hash=content_hash,
            content_summary=content_summary,
            content_type_detected=content_type_detected,
            language_detected=language_detected,
            tags=tags,
            embedding=embedding
        )
        
        self.db.add(metadata)
        await self.db.commit()
        await self.db.refresh(metadata)
        
        return metadata

    async def get_duplicate_files(self) -> list[tuple[str, list[File]]]:
        """Get all sets of duplicate files grouped by content hash"""
        # Query to find content hashes with multiple files
        query = select(FileMetadata.content_hash, File)\
            .join(File)\
            .where(FileMetadata.content_hash.in_(
                select(FileMetadata.content_hash)\
                .group_by(FileMetadata.content_hash)\
                .having(func.count() > 1)
            ))
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # Group files by content hash
        duplicates = {}
        for hash_value, file in rows:
            if hash_value not in duplicates:
                duplicates[hash_value] = []
            duplicates[hash_value].append(file)
            
        return list(duplicates.items())

    async def create_folder(
        self,
        name: str,
        owner_id: int,
        parent_id: Optional[int] = None
    ) -> Folder:
        """Create a new folder"""
        try:
            # Get parent folder path if provided
            parent_path = ""
            if parent_id:
                parent = await self.get_folder(parent_id)
                if not parent:
                    raise HTTPException(status_code=404, detail="Parent folder not found")
                parent_path = parent.path
            
            # Create folder path
            path = f"{parent_path}/{name}" if parent_path else name
            
            # Create folder
            folder = Folder(
                name=name,
                owner_id=owner_id,
                path=path,
                is_root=parent_id is None
            )
            self.db.add(folder)
            await self.db.commit()
            await self.db.refresh(folder)
            
            return folder
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create folder: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_folder(self, folder_id: int) -> Optional[Folder]:
        """Get a folder by ID"""
        try:
            query = select(Folder).where(Folder.id == folder_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get folder: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def list_folders(
        self,
        owner_id: int,
        parent_id: Optional[int] = None
    ) -> List[Folder]:
        """List folders for a user"""
        try:
            conditions = [Folder.owner_id == owner_id]
            if parent_id:
                parent = await self.get_folder(parent_id)
                if not parent:
                    raise HTTPException(status_code=404, detail="Parent folder not found")
                conditions.append(Folder.parent.any(Folder.id == parent_id))
            else:
                conditions.append(Folder.is_root == True)
            
            query = select(Folder).where(and_(*conditions))
            result = await self.db.execute(query)
            return result.scalars().all()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to list folders: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_folder(
        self,
        folder_id: int,
        name: str
    ) -> Folder:
        """Update a folder"""
        try:
            folder = await self.get_folder(folder_id)
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")
            
            # Update folder name and path
            old_path = folder.path
            new_path = f"{old_path.rsplit('/', 1)[0]}/{name}" if '/' in old_path else name
            
            folder.name = name
            folder.path = new_path
            
            # Update paths of all subfolders
            await self._update_subfolder_paths(folder, old_path, new_path)
            
            await self.db.commit()
            await self.db.refresh(folder)
            
            return folder
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update folder: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _update_subfolder_paths(
        self,
        folder: Folder,
        old_path: str,
        new_path: str
    ):
        """Update paths of all subfolders recursively"""
        try:
            for subfolder in folder.subfolders:
                subfolder.path = subfolder.path.replace(old_path, new_path, 1)
                await self._update_subfolder_paths(subfolder, old_path, new_path)
        except Exception as e:
            logger.error(f"Failed to update subfolder paths: {str(e)}")
            raise

    async def delete_folder(
        self,
        folder_id: int,
        recursive: bool = False
    ) -> None:
        """Delete a folder"""
        try:
            folder = await self.get_folder(folder_id)
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")
            
            if not recursive:
                # Check if folder is empty
                if folder.files or folder.subfolders:
                    raise HTTPException(
                        status_code=400,
                        detail="Folder is not empty. Use recursive=True to delete contents"
                    )
            else:
                # Delete all files in the folder
                for file in folder.files:
                    await self.delete_file(file.path)
                
                # Delete all subfolders recursively
                for subfolder in folder.subfolders:
                    await self.delete_folder(subfolder.id, recursive=True)
            
            # Delete the folder
            await self.db.delete(folder)
            await self.db.commit()
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete folder: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def move_item(
        self,
        item_id: int,
        destination_folder_id: Optional[int]
    ) -> Dict[str, Any]:
        """Move a file or folder to a new location"""
        try:
            # Try to get item as folder first
            item = await self.get_folder(item_id)
            is_folder = True
            
            if not item:
                # If not a folder, try as file
                item = await self.get_file(item_id)
                is_folder = False
                
                if not item:
                    raise HTTPException(status_code=404, detail="Item not found")
            
            # Get destination folder if provided
            dest_folder = None
            if destination_folder_id:
                dest_folder = await self.get_folder(destination_folder_id)
                if not dest_folder:
                    raise HTTPException(status_code=404, detail="Destination folder not found")
            
            if is_folder:
                # Update folder path
                old_path = item.path
                new_path = f"{dest_folder.path}/{item.name}" if dest_folder else item.name
                
                item.path = new_path
                await self._update_subfolder_paths(item, old_path, new_path)
                
                # Update folder relationships
                item.parent = [dest_folder] if dest_folder else []
            else:
                # Update file path
                item.path = f"{dest_folder.path}/{item.filename}" if dest_folder else item.filename
                
                # Update file relationships
                item.folders = [dest_folder] if dest_folder else []
            
            await self.db.commit()
            await self.db.refresh(item)
            
            return item
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to move item: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        folder_id: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Upload a file to storage"""
        try:
            # Get folder path if provided
            folder_path = ""
            if folder_id:
                folder = await self.get_folder(folder_id)
                if not folder:
                    raise HTTPException(status_code=404, detail="Folder not found")
                folder_path = folder.path
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            object_path = f"{folder_path}/{unique_filename}" if folder_path else unique_filename
            
            # Upload file
            result = self.minio_client.put_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_path,
                data=file,
                metadata=metadata or {}
            )
            
            return {
                "filename": unique_filename,
                "path": object_path,
                "size": result.size,
                "metadata": metadata
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def download_file(self, file_path: str) -> BinaryIO:
        """Download a file from storage"""
        try:
            return self.minio_client.get_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=file_path
            )
        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_file(self, file_path: str) -> None:
        """Delete a file from storage"""
        try:
            self.minio_client.remove_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=file_path
            )
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def list_files(
        self,
        prefix: Optional[str] = None,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """List files in storage"""
        try:
            objects = self.minio_client.list_objects(
                bucket_name=settings.MINIO_BUCKET,
                prefix=prefix,
                recursive=recursive
            )
            return [
                {
                    "name": obj.object_name.split("/")[-1],
                    "path": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified
                }
                for obj in objects
            ]
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
