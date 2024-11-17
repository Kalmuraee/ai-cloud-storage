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
            # Text files
            if file_extension in ['txt', 'md', 'json', 'csv', 'yaml', 'yml']:
                return file_data.decode('utf-8')
            
            # PDF files
            elif file_extension == 'pdf':
                try:
                    # Try normal PDF extraction first
                    file_obj = io.BytesIO(file_data)
                    loader = PyPDFLoader(file_obj)
                    pages = loader.load()
                    text = '\n'.join(page.page_content for page in pages)
                    
                    # If no text was extracted, try OCR
                    if not text.strip():
                        from app.services.ocr import ocr_service
                        text = await ocr_service.extract_text_from_pdf_with_ocr(file_data)
                    return text
                except Exception as e:
                    # Fallback to OCR if normal extraction fails
                    from app.services.ocr import ocr_service
                    return await ocr_service.extract_text_from_pdf_with_ocr(file_data)
            
            # Office documents
            elif file_extension in ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']:
                # Convert to PDF first using LibreOffice
                temp_dir = tempfile.mkdtemp()
                input_path = os.path.join(temp_dir, f"input.{file_extension}")
                output_path = os.path.join(temp_dir, "output.pdf")
                
                try:
                    with open(input_path, 'wb') as f:
                        f.write(file_data)
                    
                    # Convert to PDF
                    subprocess.run([
                        'soffice',
                        '--headless',
                        '--convert-to',
                        'pdf',
                        '--outdir',
                        temp_dir,
                        input_path
                    ], check=True)
                    
                    # Read the PDF and extract text
                    with open(output_path, 'rb') as f:
                        pdf_data = f.read()
                    return await self._extract_text(pdf_data, 'pdf')
                finally:
                    shutil.rmtree(temp_dir)
            
            # Image files
            elif file_extension in ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif']:
                from app.services.ocr import ocr_service
                return await ocr_service.extract_text_from_image(file_data)
            
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