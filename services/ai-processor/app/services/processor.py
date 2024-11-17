import io
from typing import List, Optional

from fastapi import HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
from minio import Minio

from app.core.config import settings
from app.schemas.processing import DocumentChunk
from app.services.embedding import embedding_service
from app.services.weaviate_client import weaviate_service


class DocumentProcessor:
    def __init__(self):
        self.minio_client = Minio(
            f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_USE_SSL,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    async def process_document(self, bucket_name: str, object_name: str) -> List[DocumentChunk]:
        """Process a document from MinIO storage."""
        try:
            # Get object from MinIO
            obj = self.minio_client.get_object(bucket_name, object_name)
            file_data = obj.read()
            
            # Determine file type and extract text
            file_extension = object_name.lower().split('.')[-1]
            text = await self._extract_text(file_data, file_extension)
            
            # Split text into chunks
            chunks = await self._split_text(text)
            
            # Generate embeddings for chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await embedding_service.generate_embeddings(chunk_texts)
            
            # Add embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                # Store in Weaviate
                await weaviate_service.store_document_chunk(chunk)
            
            return chunks

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {str(e)}"
            )

    async def _extract_text(self, file_data: bytes, file_extension: str) -> str:
        """Extract text from a file based on its type."""
        try:
            if file_extension == 'pdf':
                # Create a temporary file-like object
                file_obj = io.BytesIO(file_data)
                loader = PyPDFLoader(file_obj)
                pages = loader.load()
                return '\n'.join(page.page_content for page in pages)
            
            elif file_extension in ['txt', 'md', 'json']:
                return file_data.decode('utf-8')
            
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file_extension}"
                )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract text: {str(e)}"
            )

    async def _split_text(self, text: str) -> List[DocumentChunk]:
        """Split text into chunks."""
        try:
            texts = self.text_splitter.split_text(text)
            return [
                DocumentChunk(
                    content=chunk_text,
                    metadata={
                        "chunk_index": i,
                    }
                )
                for i, chunk_text in enumerate(texts)
            ]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to split text: {str(e)}"
            )


document_processor = DocumentProcessor()