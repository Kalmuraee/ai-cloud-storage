"""
Storage schemas module
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FileBase(BaseModel):
    """Base file schema"""
    filename: str
    content_type: str
    size: int
    path: str

class FileCreate(FileBase):
    """Schema for file creation"""
    pass

class FileResponse(FileBase):
    """Schema for file response"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class FolderBase(BaseModel):
    """Base folder schema"""
    name: str

class FolderCreate(FolderBase):
    """Schema for folder creation"""
    parent_id: Optional[int] = None

class FolderResponse(FolderBase):
    """Schema for folder response"""
    id: int
    owner_id: int
    path: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class FileUploadResponse(BaseModel):
    """Response model for file upload with deduplication info"""
    file: FileResponse
    is_duplicate: bool = Field(description="Whether the file was deduplicated")

class DuplicateFilesResponse(BaseModel):
    """Response model for duplicate files listing"""
    content_hash: str = Field(description="SHA-256 hash of the file content")
    files: List[FileResponse] = Field(description="List of files with identical content")

    class Config:
        schema_extra = {
            "example": {
                "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "files": [
                    {
                        "id": 1,
                        "filename": "document1.pdf",
                        "path": "user1/documents/document1.pdf",
                        "size": 1024,
                        "content_type": "application/pdf",
                        "owner_id": 1,
                        "created_at": "2024-01-01T12:00:00Z"
                    },
                    {
                        "id": 2,
                        "filename": "document2.pdf",
                        "path": "user2/documents/document2.pdf",
                        "size": 1024,
                        "content_type": "application/pdf",
                        "owner_id": 2,
                        "created_at": "2024-01-02T12:00:00Z"
                    }
                ]
            }
        }

class MoveItemRequest(BaseModel):
    """Schema for moving files/folders"""
    destination_folder_id: Optional[int] = Field(None, description="Target folder ID (None for root)")

class ShareItemRequest(BaseModel):
    """Schema for sharing items"""
    email: Optional[str] = Field(None, description="Email of the user to share with")
    permissions: List[str] = Field(..., description="List of permissions to grant")
    expires_at: Optional[datetime] = Field(None, description="Share expiration date")

class SharedItemResponse(BaseModel):
    """Schema for shared item response"""
    id: int
    file_id: Optional[int]
    folder_id: Optional[int]
    shared_by: int
    shared_with: Optional[int]
    share_link: Optional[str]
    permissions: str
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class FileVersionResponse(BaseModel):
    """Schema for file version response"""
    id: int
    version: int
    size: int
    created_at: datetime
    created_by: int
    comment: Optional[str]

    class Config:
        from_attributes = True

class SearchResponse(BaseModel):
    """Schema for search results"""
    type: str
    id: int
    name: str
    path: str
    owner_id: int
    created_at: datetime
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

class NotificationBase(BaseModel):
    """Base notification schema"""
    id: int
    type: str
    message: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    """Schema for notification update"""
    read: bool = Field(..., description="Mark notification as read/unread")

class UserSettingsUpdate(BaseModel):
    """Schema for user settings update"""
    settings: Dict[str, Any] = Field(..., description="User settings key-value pairs")

class TagBase(BaseModel):
    """Base tag schema"""
    name: str = Field(..., description="Tag name", min_length=1, max_length=50)

class TagResponse(TagBase):
    """Schema for tag response"""
    id: int
    file_id: int
    created_at: datetime
    created_by: int

    class Config:
        from_attributes = True

class MetadataUpdate(BaseModel):
    """Schema for metadata update"""
    metadata: Dict[str, Any] = Field(..., description="Metadata key-value pairs")

class FileListResponse(BaseModel):
    """Response model for file list"""
    files: List[FileResponse] = Field(description="List of files")

    class Config:
        schema_extra = {
            "example": {
                "files": [
                    {
                        "id": 1,
                        "filename": "document.pdf",
                        "path": "user/documents/document.pdf",
                        "size": 1024,
                        "content_type": "application/pdf",
                        "owner_id": 1,
                        "created_at": "2024-01-01T12:00:00Z"
                    }
                ]
            }
        }

class FileMetadataResponse(BaseModel):
    """Response model for file metadata"""
    id: int
    filename: str
    path: str
    size: int
    content_type: str
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    metadata: Dict[str, Any] = Field(default_factory=dict, description="File metadata")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "filename": "document.pdf",
                "path": "user/documents/document.pdf",
                "size": 1024,
                "content_type": "application/pdf",
                "owner_id": 1,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-02T12:00:00Z",
                "metadata": {
                    "description": "Important document",
                    "tags": ["important", "document"],
                    "version": "1.0"
                }
            }
        }
