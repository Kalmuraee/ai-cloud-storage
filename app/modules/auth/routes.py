"""
Authentication module routes
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.logging import get_logger
from app.modules.auth.service import AuthService
from app.modules.auth.models import User

router = APIRouter()
logger = get_logger(__name__)
auth_service = AuthService()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None = None

    class Config:
        from_attributes = True

async def get_current_user(
    token: str = Security(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from token"""
    user = await auth_service.get_current_user(token, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register new user"""
    try:
        user = await auth_service.create_user(
            user_data.email,
            user_data.password,
            db
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to register user: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login user and get access token"""
    try:
        # Log the login attempt
        logger.info(f"Login attempt for user: {form_data.username}")
        
        # Authenticate user
        user = await auth_service.authenticate_user(
            form_data.username,
            form_data.password,
            db
        )
        
        if not user:
            logger.warning(f"Authentication failed for user: {form_data.username}")
            raise HTTPException(
                status_code=401,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id)}
        )
        
        logger.info(f"Login successful for user: {form_data.username}")
        return Token(access_token=access_token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed for user {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Security(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and revoke token"""
    try:
        await auth_service.revoke_token(token, db)
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Failed to logout user: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user info"""
    return current_user
