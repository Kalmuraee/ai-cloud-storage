"""
Authentication module models
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

# Many-to-many relationship table for user roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True)
)

class User(Base):
    """User model"""
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String(255), unique=True, index=True, nullable=False)
    username: str = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password: str = Column(String(255), nullable=False)
    full_name: str = Column(String(100))
    is_active: bool = Column(Boolean, default=True)
    is_superuser: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    files = relationship("File", back_populates="owner")
    folders = relationship("Folder", back_populates="owner")
    tokens = relationship("Token", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    shared_items_owned = relationship("SharedItem", foreign_keys="SharedItem.owner_id", back_populates="owner")
    shared_items_received = relationship("SharedItem", foreign_keys="SharedItem.shared_with_id", back_populates="shared_with")

class Role(Base):
    """Role model for user permissions"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    permissions = Column(Text)  # JSON array of permissions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")

class Token(Base):
    """Token model for storing refresh tokens"""
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, nullable=False)
    token_type = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_revoked = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="tokens")
