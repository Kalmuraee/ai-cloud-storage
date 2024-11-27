"""
Authentication module routes.

This module provides endpoints for user authentication and management, including:
- User registration
- Login/Logout
- Token management
- User profile management
"""
from typing import Annotated, Dict
from fastapi import APIRouter, Depends, Security, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger
from app.modules.auth.service import AuthService
from app.modules.auth.repository import AuthRepository
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    UserCreate,
    UserUpdate,
    UserInDB,
    Token,
    TokenCreate
)

router = APIRouter()

@router.post(
    "/register",
    response_model=UserInDB,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "User successfully created",
            "model": UserInDB
        },
        409: {
            "description": "Username or email already exists"
        },
        422: {
            "description": "Validation error in request body"
        }
    }
)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserInDB:
    """
    Register a new user in the system.
    
    Creates a new user account with the provided information. The password
    will be automatically hashed before storage.
    
    Args:
        user_data: User registration data including username, email, and password
        db: Database session dependency
    
    Returns:
        UserInDB: Created user information (excluding password)
    
    Raises:
        HTTPException(409): If username or email already exists
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails
    """
    repo = AuthRepository(db)
    service = AuthService(repo)
    return await service.create_user(user_data)

@router.post(
    "/token",
    response_model=Token,
    responses={
        200: {
            "description": "Successfully authenticated",
            "model": Token
        },
        401: {
            "description": "Invalid credentials"
        },
        422: {
            "description": "Validation error in request body"
        }
    }
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """
    Authenticate user and create access token.
    
    Validates user credentials and returns JWT access and refresh tokens
    if authentication is successful.
    
    Args:
        form_data: OAuth2 password request form containing username and password
        db: Database session dependency
    
    Returns:
        Token: Access and refresh tokens
    
    Raises:
        HTTPException(401): If credentials are invalid
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails
    """
    repo = AuthRepository(db)
    service = AuthService(repo)
    return await service.authenticate_user(form_data.username, form_data.password)

@router.post(
    "/logout",
    response_model=Dict[str, str],
    responses={
        200: {
            "description": "Successfully logged out",
            "content": {
                "application/json": {
                    "example": {"message": "Successfully logged out"}
                }
            }
        },
        401: {
            "description": "Invalid or expired token"
        }
    }
)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    token: Annotated[str, Security(OAuth2PasswordBearer(tokenUrl="token"))],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Dict[str, str]:
    """
    Logout user and invalidate current token.
    
    Adds the current token to a blacklist to prevent its further use.
    
    Args:
        current_user: Current authenticated user (from token)
        token: Current access token
        db: Database session dependency
    
    Returns:
        dict: Success message
    
    Raises:
        HTTPException(401): If token is invalid or expired
        HTTPException(500): If database operation fails
    """
    repo = AuthRepository(db)
    service = AuthService(repo)
    await service.logout(current_user.id, token)
    return {"message": "Successfully logged out"}

@router.get(
    "/me",
    response_model=UserInDB,
    responses={
        200: {
            "description": "Current user information",
            "model": UserInDB
        },
        401: {
            "description": "Not authenticated"
        }
    }
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
) -> UserInDB:
    """
    Get current authenticated user's information.
    
    Returns the profile information of the currently authenticated user.
    
    Args:
        current_user: Current authenticated user (from token)
    
    Returns:
        UserInDB: Current user's information
    
    Raises:
        HTTPException(401): If not authenticated
    """
    return UserInDB.model_validate(current_user)

@router.patch(
    "/me",
    response_model=UserInDB,
    responses={
        200: {
            "description": "User information updated",
            "model": UserInDB
        },
        401: {
            "description": "Not authenticated"
        },
        409: {
            "description": "Username or email already exists"
        },
        422: {
            "description": "Validation error in request body"
        }
    }
)
async def update_current_user(
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserInDB:
    """
    Update current user's information.
    
    Updates the profile information of the currently authenticated user.
    Only provided fields will be updated.
    
    Args:
        user_data: User update data (partial)
        current_user: Current authenticated user (from token)
        db: Database session dependency
    
    Returns:
        UserInDB: Updated user information
    
    Raises:
        HTTPException(401): If not authenticated
        HTTPException(409): If new username or email already exists
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails
    """
    repo = AuthRepository(db)
    service = AuthService(repo)
    return await service.update_user(current_user.id, user_data)
