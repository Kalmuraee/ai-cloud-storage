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

class TextClassifier:
    def __init__(self):
        self.models = {}
        
    def classify(self, text: str, model_name: str = None) -> dict:
        """Classify text using specified model"""
        if model_name not in self.models:
            self.models[model_name] = pipeline(
                "text-classification",
                model=model_name,
                device="cpu"
            )
        
        result = self.models[model_name](text)[0]
        return {
            "label": result["label"],
            "confidence": result["score"]
        }

class TextEmbedder:
    def __init__(self):
        self.models = {}
        
    def embed(self, text: str, model_name: str = None) -> list:
        """Generate embeddings using specified model"""
        if model_name not in self.models:
            self.models[model_name] = SentenceTransformer(model_name)
        
        return self.models[model_name].encode(text)

# Initialize AI models
text_embedder = TextEmbedder()
text_classifier = TextClassifier()

def init_ai_processor_module() -> APIRouter:
    """Initialize AI processor module."""
    if not getattr(settings, 'AI_PROCESSOR_MODULE_ENABLED', True):
        return router
        
    # Import handlers here to avoid circular imports
    from .routes import router as ai_router
    
    # Include routes
    router.include_router(ai_router)
    
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
