from typing import List, Optional
from pydantic import BaseModel


class ProcessingRequest(BaseModel):
    bucket_name: str
    object_name: str


class ProcessingStatus(BaseModel):
    status: str
    message: Optional[str] = None


class DocumentChunk(BaseModel):
    content: str
    metadata: dict
    embedding: Optional[List[float]] = None


class SearchQuery(BaseModel):
    query: str
    limit: int = 10


class SearchResult(BaseModel):
    content: str
    metadata: dict
    score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]