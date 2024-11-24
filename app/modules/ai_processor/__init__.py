"""
AI Processor Module
"""
from fastapi import APIRouter
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from app.core.config import settings

# Create router for AI processor module
router = APIRouter(prefix="/ai", tags=["AI Processing"])

# Default model names if not in settings
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_CLASSIFICATION_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

# Initialize AI models with fallbacks
text_embedder = SentenceTransformer(
    getattr(settings, 'DEFAULT_EMBEDDING_MODEL', DEFAULT_EMBEDDING_MODEL)
)
text_classifier = pipeline(
    "text-classification", 
    model=getattr(settings, 'DEFAULT_CLASSIFICATION_MODEL', DEFAULT_CLASSIFICATION_MODEL), 
    device="cpu"
)

def init_ai_processor_module() -> APIRouter:
    """Initialize AI processor module."""
    if not getattr(settings, 'AI_PROCESSOR_MODULE_ENABLED', True):
        return router
        
    # Import handlers here to avoid circular imports
    from .routes import router as ai_router
    
    # Include routes
    router.include_router(ai_router)
    
    # Initialize models and processors
    global text_embedder, text_classifier
    
    return router

# Export dependencies and services
from .dependencies import get_ai_service
from .service import AIProcessorService

# Export model instances
__all__ = [
    "text_embedder",
    "text_classifier",
    "AIProcessorService",
    "get_ai_service",
]
