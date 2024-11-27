"""
Authentication module schemas using Pydantic models
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
import re

class RoleBase(BaseModel):
    """Base schema for Role"""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    permissions: List[str] = Field(default_factory=list)

class RoleCreate(RoleBase):
    """Schema for creating a new role"""
    pass

class RoleUpdate(RoleBase):
    """Schema for updating a role"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)

class RoleInDB(RoleBase):
    """Schema for role in database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

class UserBase(BaseModel):
    """Base schema for User"""
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    is_superuser: bool = False

    @field_validator('username')
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError('Username must be alphanumeric')
        return v

class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="User's password")

    @field_validator('password')
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    """Schema for user in database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    roles: List[RoleInDB] = []

class Token(BaseModel):
    """Schema for authentication token"""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

class TokenCreate(BaseModel):
    """Schema for creating a new token"""
    token: str = Field(..., min_length=32)
    token_type: str
    user_id: int
    expires_at: datetime

class TokenInDB(TokenCreate):
    """Schema for token in database"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    is_revoked: bool = False
