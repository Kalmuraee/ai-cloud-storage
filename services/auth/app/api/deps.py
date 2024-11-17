from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import validate_token
from app.models.user import User
from app.schemas.token import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)
def get_current_active_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

def get_current_superuser(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The user is not a superuser")
    return current_user

def has_permission(
    required_permissions: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    user_permissions = db.query(Permission).join(Role.permissions).join(User.roles).filter(User.id == current_user.id).all()
    user_permission_names = [p.name for p in user_permissions]
    for required_permission in required_permissions:
        if required_permission not in user_permission_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User is missing the '{required_permission}' permission",
            )
    return current_user
def get_current_active_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

def get_current_superuser(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The user is not a superuser")
    return current_user

def has_permission(
    required_permissions: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    user_permissions = db.query(Permission).join(Role.permissions).join(User.roles).filter(User.id == current_user.id).all()
    user_permission_names = [p.name for p in user_permissions]
    for required_permission in required_permissions:
        if required_permission not in user_permission_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User is missing the '{required_permission}' permission",
            )
    return current_user
def get_current_active_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

def get_current_superuser(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The user is not a superuser")
    return current_user

def has_permission(
    required_permissions: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    user_permissions = db.query(Permission).join(Role.permissions).join(User.roles).filter(User.id == current_user.id).all()
    user_permission_names = [p.name for p in user_permissions]
    for required_permission in required_permissions:
        if required_permission not in user_permission_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User is missing the '{required_permission}' permission",
            )
    return current_user

def get_db() -> Generator:
    """
    Get database session.
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2),
) -> User:
    """
    Get current user from JWT token.
    """
    try:
        payload = validate_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    return user

def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return current_user