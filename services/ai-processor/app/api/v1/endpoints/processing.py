from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas.processing import (
    ProcessingRequest,
    ProcessingStatus,
    SearchQuery,
    SearchResponse,
    SearchResult,
)
from app.services.processor import document_processor
from app.services.embedding import embedding_service
from app.services.weaviate_client import weaviate_service

router = APIRouter()


@router.post("/process", response_model=ProcessingStatus, summary="Process a document")
async def process_document(request: ProcessingRequest):
    """
    Process a document from storage.
    
    - Extracts text from the document
    - Splits into chunks
    - Generates embeddings
    - Stores in vector database
    """
    try:
        chunks = await document_processor.process_document(
            request.bucket_name,
            request.object_name
        )
        return ProcessingStatus(
            status="success",
            message=f"Successfully processed {len(chunks)} chunks"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse, summary="Semantic search")
async def semantic_search(query: SearchQuery):
    """
    Perform semantic search across processed documents.
    
    - Generates embedding for the query
    - Searches vector database for similar content
    - Returns ranked results
    """
    try:
        # Generate embedding for query
        query_embedding = await embedding_service.generate_embedding(query.query)
        
        # Search in Weaviate
        results = await weaviate_service.semantic_search(
            query_vector=query_embedding,
            limit=query.limit
        )
        
        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{bucket_name}/objects/{object_name}", status_code=204, summary="Delete processed document")
async def delete_processed_document(bucket_name: str, object_name: str):
    """
    Delete a processed document from the vector database.
    """
    try:
        await weaviate_service.delete_document(bucket_name, object_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))