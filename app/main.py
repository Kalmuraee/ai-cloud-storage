"""
Main application module
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.core.database import init_models
from app.core.health import router as health_router
from app.modules.auth.routes import router as auth_router
from app.modules.storage.routes import router as storage_router
from app.modules.ai_processor.routes import router as ai_router

settings = Settings()

def create_app() -> FastAPI:
    """Create FastAPI application"""
    # Create FastAPI app
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_tags=[
            {
                "name": "auth",
                "description": "Authentication and user management operations"
            },
            {
                "name": "storage",
                "description": "File storage and management operations"
            },
            {
                "name": "ai",
                "description": "AI processing and analysis operations"
            }
        ],
        contact={
            "name": "AI Cloud Storage Support",
            "email": "support@example.com"
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(storage_router, prefix="/api/v1/storage", tags=["storage"])
    app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])
    
    @app.on_event("startup")
    async def startup_event():
        """Startup event handler"""
        # Initialize database models
        await init_models()

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "version": settings.VERSION}

    return app

# Create the application instance
app = create_app()
