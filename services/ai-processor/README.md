# AI Processor Service

FastAPI-based AI processing service for the AI Cloud Storage platform.

## Features

- Document text extraction
- Text chunking and embedding generation
- Vector storage in Weaviate
- Semantic search capabilities
- Asynchronous processing with Kafka
- RESTful API with OpenAPI documentation

## API Documentation

The API documentation is available at:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Development

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables:
```bash
export HUGGINGFACE_API_KEY=your-api-key
export MINIO_HOST=localhost
export WEAVIATE_URL=http://localhost:8080
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

3. Run the development server:
```bash
poetry run uvicorn app.main:app --reload --port 8001
```

## API Endpoints

### Processing

- `POST /api/v1/processing/process` - Process a document
  ```json
  {
    "bucket_name": "my-bucket",
    "object_name": "document.pdf"
  }
  ```

- `POST /api/v1/processing/search` - Semantic search
  ```json
  {
    "query": "search query text",
    "limit": 10
  }
  ```

- `DELETE /api/v1/processing/{bucket_name}/objects/{object_name}` - Delete processed document

## Architecture

The service consists of several components:

1. Document Processor
   - Extracts text from various file formats
   - Splits text into manageable chunks
   - Coordinates processing pipeline

2. Embedding Service
   - Generates embeddings using Sentence Transformers
   - Supports batch processing
   - Configurable model selection

3. Vector Storage (Weaviate)
   - Stores document chunks and embeddings
   - Enables semantic search
   - Manages document metadata

4. Kafka Integration
   - Asynchronous document processing
   - Status updates and error handling
   - Scalable message processing

## Environment Variables

- `MINIO_HOST` - MinIO server host
- `MINIO_PORT` - MinIO server port
- `MINIO_ROOT_USER` - MinIO access key
- `MINIO_ROOT_PASSWORD` - MinIO secret key
- `MINIO_USE_SSL` - Use SSL for MinIO connection
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker addresses
- `WEAVIATE_URL` - Weaviate server URL
- `HUGGINGFACE_API_KEY` - HuggingFace API key
- `EMBEDDING_MODEL` - Model name for embeddings

## Testing

Run tests with:
```bash
poetry run pytest
```

## Docker

Build the container:
```bash
docker build -t ai-processor-service .
```

Run the container:
```bash
docker run -p 8001:8001 \
  -e MINIO_HOST=minio \
  -e WEAVIATE_URL=http://weaviate:8080 \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 \
  -e HUGGINGFACE_API_KEY=your-api-key \
  ai-processor-service
```