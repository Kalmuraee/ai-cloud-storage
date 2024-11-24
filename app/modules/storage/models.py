"""
Storage module models
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean, JSON, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class FileStatus(str, Enum):
    """File status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class ItemType(str, Enum):
    """Storage item type enumeration"""
    FILE = "file"
    FOLDER = "folder"

class SharePermission(str, Enum):
    """Share permission enumeration"""
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"

class ShareStatus(str, Enum):
    """Share status enumeration"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

# Association table for folder-file relationships
folder_files = Table(
    'folder_files',
    Base.metadata,
    Column('folder_id', Integer, ForeignKey('folders.id'), primary_key=True),
    Column('file_id', Integer, ForeignKey('files.id'), primary_key=True)
)

# Association table for folder-subfolder relationships
folder_subfolders = Table(
    'folder_subfolders',
    Base.metadata,
    Column('parent_id', Integer, ForeignKey('folders.id'), primary_key=True),
    Column('child_id', Integer, ForeignKey('folders.id'), primary_key=True)
)

class Folder(Base):
    """Folder model for organizing files and subfolders"""
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_root = Column(Boolean, default=False)
    path = Column(String(500), nullable=False)  # Full path from root
    
    # Relationships
    owner = relationship("User", back_populates="folders")
    files = relationship("File", secondary=folder_files, back_populates="folders")
    parent = relationship(
        "Folder",
        secondary=folder_subfolders,
        primaryjoin=id==folder_subfolders.c.child_id,
        secondaryjoin=id==folder_subfolders.c.parent_id,
        backref="subfolders"
    )
    shared_items = relationship("SharedItem", back_populates="folder", cascade="all, delete-orphan")
    collaborators = relationship("FolderCollaborator", back_populates="folder", cascade="all, delete-orphan")

class File(Base):
    """File model for storing file metadata"""
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    bucket = Column(String(100), nullable=False)
    path = Column(String(500), nullable=False)
    status = Column(SQLEnum(FileStatus), default=FileStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True)
    
    # Relationships
    owner = relationship("User", back_populates="files")
    file_metadata = relationship("FileMetadata", back_populates="file", uselist=False)
    folders = relationship("Folder", secondary=folder_files, back_populates="files")
    versions = relationship("FileVersion", back_populates="file")
    shared_items = relationship("SharedItem", back_populates="file", cascade="all, delete-orphan")
    tags = relationship("FileTag", back_populates="file")

class FileVersion(Base):
    """File version model for version control"""
    __tablename__ = "file_versions"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    version = Column(Integer, nullable=False)
    size = Column(Integer, nullable=False)
    path = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="versions")
    creator = relationship("User")

class SharedItem(Base):
    """Model for shared files and folders"""
    __tablename__ = "shared_items"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    shared_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    share_link = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    file = relationship("File", back_populates="shared_items")
    folder = relationship("Folder", back_populates="shared_items")
    owner = relationship("User", foreign_keys=[shared_by])

class FolderCollaborator(Base):
    """Model for folder collaborators"""
    __tablename__ = "folder_collaborators"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    email = Column(String(255), nullable=False)
    permissions = Column(SQLEnum(SharePermission), nullable=False)
    status = Column(SQLEnum(ShareStatus), default=ShareStatus.PENDING)
    invitation_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    folder = relationship("Folder", back_populates="collaborators")
    user = relationship("User", foreign_keys=[user_id])

class FileTag(Base):
    """Model for file tags"""
    __tablename__ = "file_tags"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    file = relationship("File", back_populates="tags")
    creator = relationship("User")

class FileMetadata(Base):
    """File metadata model for storing AI-processed information"""
    __tablename__ = "file_metadata"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), unique=True, nullable=False)
    content_hash = Column(String(64), nullable=True)
    content_summary = Column(Text, nullable=True)
    content_type_detected = Column(String(100), nullable=True)
    language_detected = Column(String(10), nullable=True)
    tags = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    file = relationship("File", back_populates="file_metadata")
