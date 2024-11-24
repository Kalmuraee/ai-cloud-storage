"""
Authentication Module
"""
from fastapi import APIRouter, Depends
from app.core.config import settings

# Create router for auth module
router = APIRouter(prefix="/auth", tags=["Authentication"])

def init_auth_module() -> APIRouter:
    """Initialize authentication module."""
    if not settings.AUTH_MODULE_ENABLED:
        return router
        
    # Import handlers here to avoid circular imports
    from .routes import router as auth_router
    from .dependencies import get_current_user, get_current_active_user
    
    # Include routes
    router.include_router(auth_router)
    
    return router

# Export dependencies
from .dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
)
