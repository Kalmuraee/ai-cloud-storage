# Storage Service

FastAPI-based storage service for the AI Cloud Storage platform.

## Features

- S3-compatible storage using MinIO
- RESTful API with OpenAPI documentation
- File upload and download
- Bucket management
- Async operations

## API Documentation

The API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

1. Install dependencies:
```bash
poetry install
```

2. Run the development server:
```bash
poetry run uvicorn app.main:app --reload
```

## API Endpoints

### Buckets

- `GET /api/v1/buckets` - List all buckets
- `POST /api/v1/buckets` - Create a new bucket
- `DELETE /api/v1/buckets/{bucket_name}` - Delete a bucket

### Objects

- `GET /api/v1/buckets/{bucket_name}/objects` - List objects in bucket
- `POST /api/v1/buckets/{bucket_name}/objects` - Upload a file
- `GET /api/v1/buckets/{bucket_name}/objects/{object_name}` - Download a file
- `DELETE /api/v1/buckets/{bucket_name}/objects/{object_name}` - Delete a file

## Environment Variables

- `MINIO_HOST` - MinIO server host (default: "minio")
- `MINIO_PORT` - MinIO server port (default: 9000)
- `MINIO_ROOT_USER` - MinIO access key (default: "minioadmin")
- `MINIO_ROOT_PASSWORD` - MinIO secret key (default: "minioadmin")
- `MINIO_USE_SSL` - Use SSL for MinIO connection (default: false)

## Testing

Run tests with:
```bash
poetry run pytest
```