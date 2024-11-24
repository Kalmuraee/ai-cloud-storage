"""
Main application module
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.core.database import init_models
from app.modules.auth.routes import router as auth_router
from app.modules.storage.routes import router as storage_router
from app.modules.ai_processor.routes import router as ai_router

settings = Settings()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
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
