"""
Authentication dependencies
"""
from typing import Annotated, AsyncGenerator
from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.exceptions import (
    InvalidCredentialsError,
    PermissionError
)
from app.modules.auth.service import AuthService
from app.modules.auth.repository import AuthRepository
from app.modules.auth.models import User

logger = get_logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_auth_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> AsyncGenerator[AuthRepository, None]:
    """
    Get auth repository instance
    
    Args:
        db: Database session
        
    Returns:
        AuthRepository: Repository instance for auth operations
    """
    yield AuthRepository(db)

async def get_auth_service(
    repo: Annotated[AuthRepository, Depends(get_auth_repository)]
) -> AsyncGenerator[AuthService, None]:
    """
    Get auth service instance
    
    Args:
        repo: Auth repository instance
        
    Returns:
        AuthService: Service instance for auth operations
    """
    yield AuthService(repo)

async def get_current_user(
    token: Annotated[str, Security(oauth2_scheme)],
    service: Annotated[AuthService, Depends(get_auth_service)]
) -> User:
    """
    Get current user from token
    
    Args:
        token: JWT access token
        service: Auth service instance
        
    Returns:
        User: Current authenticated user
        
    Raises:
        InvalidCredentialsError: If token is invalid or user not found
    """
    try:
        user = await service.get_current_user(token)
        if not user:
            raise InvalidCredentialsError("Could not validate credentials")
        return user
    except Exception as e:
        logger.error(f"Failed to get current user: {str(e)}")
        raise InvalidCredentialsError("Could not validate credentials")

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get current active user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        PermissionError: If user is inactive
    """
    if not current_user.is_active:
        raise PermissionError("Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Get current admin user
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Current admin user
        
    Raises:
        PermissionError: If user is not an admin
    """
    if not current_user.is_superuser:
        raise PermissionError("The user doesn't have enough privileges")
    return current_user
