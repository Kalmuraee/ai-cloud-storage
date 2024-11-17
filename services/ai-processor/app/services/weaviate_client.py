from typing import List, Optional

import weaviate
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.processing import DocumentChunk, SearchResult


class WeaviateService:
    def __init__(self):
        self.client = weaviate.Client(url=settings.WEAVIATE_URL)
        self._ensure_schema()

    def _ensure_schema(self):
        """Ensure the required schema exists in Weaviate."""
        try:
            # Check if schema exists
            current_schema = self.client.schema.get()
            if not any(c["class"] == "Document" for c in current_schema["classes"]):
                # Create schema for documents
                class_obj = {
                    "class": "Document",
                    "description": "A document chunk with its embedding",
                    "vectorizer": "none",  # We'll provide our own vectors
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "The text content of the document chunk",
                        },
                        {
                            "name": "bucket_name",
                            "dataType": ["string"],
                            "description": "The name of the bucket containing the original file",
                        },
                        {
                            "name": "object_name",
                            "dataType": ["string"],
                            "description": "The name of the original file",
                        },
                        {
                            "name": "chunk_index",
                            "dataType": ["int"],
                            "description": "Index of this chunk in the document",
                        },
                    ],
                }
                self.client.schema.create_class(class_obj)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize Weaviate schema: {str(e)}")

    async def store_document_chunk(self, chunk: DocumentChunk) -> str:
        """Store a document chunk with its embedding in Weaviate."""
        try:
            # Prepare the data object
            data_object = {
                "content": chunk.content,
                "bucket_name": chunk.metadata["bucket_name"],
                "object_name": chunk.metadata["object_name"],
                "chunk_index": chunk.metadata.get("chunk_index", 0),
            }

            # Store the object with its vector
            result = self.client.data_object.create(
                data_object=data_object,
                class_name="Document",
                vector=chunk.embedding,
            )

            return result

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store document chunk in Weaviate: {str(e)}"
            )

    async def semantic_search(
        self, query_vector: List[float], limit: int = 10
    ) -> List[SearchResult]:
        """Perform semantic search using a query vector."""
        try:
            result = (
                self.client.query
                .get("Document", ["content", "bucket_name", "object_name", "chunk_index"])
                .with_near_vector({
                    "vector": query_vector,
                    "certainty": 0.7
                })
                .with_limit(limit)
                .do()
            )

            # Extract and format results
            search_results = []
            for item in result["data"]["Get"]["Document"]:
                search_results.append(
                    SearchResult(
                        content=item["content"],
                        metadata={
                            "bucket_name": item["bucket_name"],
                            "object_name": item["object_name"],
                            "chunk_index": item["chunk_index"],
                        },
                        score=item.get("_additional", {}).get("certainty", 0.0),
                    )
                )

            return search_results

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to perform semantic search: {str(e)}"
            )

    async def delete_document(self, bucket_name: str, object_name: str) -> None:
        """Delete all chunks of a document."""
        try:
            where_filter = {
                "operator": "And",
                "operands": [
                    {
                        "path": ["bucket_name"],
                        "operator": "Equal",
                        "valueString": bucket_name
                    },
                    {
                        "path": ["object_name"],
                        "operator": "Equal",
                        "valueString": object_name
                    }
                ]
            }
            
            self.client.batch.delete_objects(
                class_name="Document",
                where=where_filter
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document from Weaviate: {str(e)}"
            )


weaviate_service = WeaviateService()