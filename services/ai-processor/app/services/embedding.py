from typing import List

from sentence_transformers import SentenceTransformer
from fastapi import HTTPException

from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        try:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load embedding model: {str(e)}"
            )

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings for a given text."""
        try:
            # Generate embedding
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate embedding: {str(e)}"
            )

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            # Generate embeddings in batch
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate embeddings: {str(e)}"
            )


embedding_service = EmbeddingService()