"""
Storage schemas module
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, FilePath
import re

from app.modules.storage.models import FileStatus, SharePermission, ShareStatus, ItemType

class FileBase(BaseModel):
    """Base file schema"""
    filename: str = Field(..., min_length=1, max_length=255, description="Name of the file")
    content_type: str = Field(..., pattern=r"^[\w-]+/[\w-]+$", description="MIME type of the file")
    size: int = Field(..., gt=0, description="Size of the file in bytes")
    path: str = Field(..., min_length=1, max_length=500, description="File path relative to bucket")

    @field_validator('filename')
    def validate_filename(cls, v: str) -> str:
        """Validate filename"""
        if not re.match(r'^[\w\-. ]+$', v):
            raise ValueError('Filename contains invalid characters')
        return v

    @field_validator('path')
    def validate_path(cls, v: str) -> str:
        """Validate file path"""
        if not re.match(r'^[\w\-./]+$', v):
            raise ValueError('Path contains invalid characters')
        if '..' in v:
            raise ValueError('Path traversal not allowed')
        return v

class FileCreate(FileBase):
    """Schema for file creation"""
    bucket: str = Field(..., min_length=1, max_length=100, description="Storage bucket name")
    original_filename: str = Field(..., min_length=1, max_length=255)
    owner_id: int = Field(..., gt=0)
    folder_id: Optional[int] = Field(None, gt=0)

class FileUpdate(BaseModel):
    """Schema for file update"""
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[FileStatus] = None
    folder_id: Optional[int] = Field(None, gt=0)

    @field_validator('filename')
    def validate_filename(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[\w\-. ]+$', v):
            raise ValueError('Filename contains invalid characters')
        return v

class FileInDB(FileBase):
    """Schema for file in database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    bucket: str
    status: FileStatus
    owner_id: int
    version: int
    is_latest: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class FileResponse(BaseModel):
    """Response model for file operations"""
    model_config = ConfigDict(from_attributes=True)

    file: FileInDB
    presigned_url: Optional[str] = Field(None, description="Presigned URL for direct download/upload")
    metadata: Optional[Dict[str, Any]] = None

class FileListResponse(BaseModel):
    """Response model for file listing"""
    model_config = ConfigDict(from_attributes=True)
    files: List[FileInDB] = Field(..., description="List of files")

class FolderBase(BaseModel):
    """Base folder schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Folder name")
    path: str = Field(..., min_length=1, max_length=500, description="Folder path from root")

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        if not re.match(r'^[\w\-. ]+$', v):
            raise ValueError('Folder name contains invalid characters')
        return v

    @field_validator('path')
    def validate_path(cls, v: str) -> str:
        if not re.match(r'^[\w\-./]+$', v):
            raise ValueError('Path contains invalid characters')
        if '..' in v:
            raise ValueError('Path traversal not allowed')
        return v

class FolderCreate(FolderBase):
    """Schema for folder creation"""
    owner_id: int = Field(..., gt=0)
    parent_id: Optional[int] = Field(None, gt=0)
    is_root: bool = False

class FolderUpdate(BaseModel):
    """Schema for folder update"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[int] = Field(None, gt=0)

    @field_validator('name')
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[\w\-. ]+$', v):
            raise ValueError('Folder name contains invalid characters')
        return v

class FolderInDB(FolderBase):
    """Schema for folder in database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    is_root: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class FileUploadResponse(BaseModel):
    """Response model for file upload with deduplication info"""
    model_config = ConfigDict(from_attributes=True)

    file: FileInDB
    is_duplicate: bool = Field(False, description="Whether the file was deduplicated")
    duplicate_of: Optional[int] = Field(None, description="ID of the original file if duplicated")

class DuplicateFilesResponse(BaseModel):
    """Response model for duplicate files listing"""
    model_config = ConfigDict(from_attributes=True)

    content_hash: str = Field(..., pattern=r'^[a-fA-F0-9]{64}$', description="SHA-256 hash of the file content")
    files: List[FileInDB] = Field(..., description="List of files with identical content")

class ShareItemRequest(BaseModel):
    """Schema for sharing items"""
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    permissions: SharePermission
    expires_at: Optional[datetime] = Field(None)
    message: Optional[str] = Field(None, max_length=500)

    @field_validator('expires_at')
    def validate_expiry(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v < datetime.now():
            raise ValueError('Expiry date must be in the future')
        return v

class SharedItemInDB(BaseModel):
    """Schema for shared item in database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_id: Optional[int]
    folder_id: Optional[int]
    shared_by: int
    shared_with: Optional[int]
    share_link: Optional[str]
    permissions: SharePermission
    status: ShareStatus
    expires_at: Optional[datetime]
    created_at: datetime

class FileVersionCreate(BaseModel):
    """Schema for creating file version"""
    file_id: int = Field(..., gt=0)
    version: int = Field(..., gt=0)
    size: int = Field(..., gt=0)
    path: str = Field(..., min_length=1, max_length=500)
    created_by: int = Field(..., gt=0)
    comment: Optional[str] = Field(None, max_length=1000)

class FileVersionInDB(FileVersionCreate):
    """Schema for file version in database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

class SearchResponse(BaseModel):
    """Schema for search results"""
    model_config = ConfigDict(from_attributes=True)

    type: ItemType
    id: int
    name: str
    path: str
    owner_id: int
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    relevance_score: Optional[float] = Field(None, ge=0, le=1)

class FileMetadataCreate(BaseModel):
    """Schema for creating file metadata"""
    file_id: int = Field(..., gt=0)
    content_hash: Optional[str] = Field(None, pattern=r'^[a-fA-F0-9]{64}$')
    content_summary: Optional[str] = None
    content_type_detected: Optional[str] = None
    language_detected: Optional[str] = Field(None, max_length=10)
    tags: Optional[List[str]] = None
    embedding: Optional[str] = None

class FileMetadataInDB(FileMetadataCreate):
    """Schema for file metadata in database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class FileMetadataResponse(BaseModel):
    """Response model for file metadata"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    path: str
    size: int
    content_type: str
    status: FileStatus
    created_at: datetime
    storage_metadata: Optional[Dict[str, Any]] = None

class FileMetadata(BaseModel):
    """Schema for file metadata"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    file_id: int
    content_hash: Optional[str] = Field(None, pattern=r'^[a-fA-F0-9]{64}$')
    content_summary: Optional[str] = None
    content_type_detected: Optional[str] = None
    language_detected: Optional[str] = Field(None, max_length=10)
    tags: Optional[List[str]] = None
    embedding: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class MetadataUpdate(BaseModel):
    """Schema for updating file metadata"""
    model_config = ConfigDict(from_attributes=True)
    content_type: Optional[str] = Field(None, pattern=r"^[\w-]+/[\w-]+$", description="MIME type of the file")
    tags: Optional[List[str]] = Field(None, description="List of tags associated with the file")
    custom_metadata: Optional[Dict[str, Any]] = Field(None, description="Custom metadata key-value pairs")
