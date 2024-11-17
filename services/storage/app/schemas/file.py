from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class FileVersion(BaseModel):
    version_id: str
    size: int
    last_modified: datetime
    etag: str

class FileMetadata(BaseModel):
    content_type: str
    size: int
    last_modified: datetime
    versions: List[FileVersion]
    shared_with: List[str]
    tags: List[str]
    is_folder: bool
    parent_folder: Optional[str] = None

class FileShare(BaseModel):
    object_name: str
    shared_with: str
    permissions: str  # 'read' or 'write'
    expiry: Optional[datetime] = None

class FileTag(BaseModel):
    object_name: str
    tag: str