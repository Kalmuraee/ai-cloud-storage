# AI Cloud Storage API Documentation

## API Overview

The AI Cloud Storage API is organized into three main modules, each providing specific functionality through RESTful endpoints.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints (except authentication endpoints) require a valid JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

### Auth Module (`/auth`)

#### Authentication Endpoints

```http
POST /auth/login
POST /auth/register
POST /auth/refresh
POST /auth/logout
GET /auth/me
```

##### Login
```http
POST /auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secure_password"
}
```

Response:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

### Storage Module (`/storage`)

#### File Operations

```http
POST /storage/files/upload
GET /storage/files/{file_id}
GET /storage/files/list
PUT /storage/files/{file_id}
DELETE /storage/files/{file_id}
```

##### Upload File
```http
POST /storage/files/upload
Content-Type: multipart/form-data

file: <file>
metadata: {
    "description": "Example file",
    "tags": ["document", "important"]
}
```

Response:
```json
{
    "file_id": "123e4567-e89b-12d3-a456-426614174000",
    "filename": "example.pdf",
    "size": 1024,
    "content_type": "application/pdf",
    "metadata": {
        "description": "Example file",
        "tags": ["document", "important"]
    },
    "created_at": "2024-01-01T12:00:00Z"
}
```

### AI Processor Module (`/ai`)

#### Content Processing

```http
POST /ai/analyze
POST /ai/extract
POST /ai/search
GET /ai/tasks/{task_id}
```

##### Analyze Content
```http
POST /ai/analyze
Content-Type: application/json

{
    "file_id": "123e4567-e89b-12d3-a456-426614174000",
    "analysis_type": "text_classification"
}
```

Response:
```json
{
    "task_id": "789e4567-e89b-12d3-a456-426614174000",
    "status": "processing",
    "created_at": "2024-01-01T12:00:00Z"
}
```

## Error Handling

### Error Response Format

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable error message",
        "details": {
            "field": "Additional error details"
        }
    }
}
```

### Common Error Codes

- `UNAUTHORIZED`: Authentication failed or token expired
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid request data
- `INTERNAL_ERROR`: Server error

## Rate Limiting

- Default: 100 requests per minute
- Burst: 20 requests
- Headers:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Pagination

For list endpoints, use query parameters:

```
?page=1&per_page=20
```

Response includes pagination metadata:

```json
{
    "items": [...],
    "pagination": {
        "total": 100,
        "page": 1,
        "per_page": 20,
        "pages": 5
    }
}
```

## Versioning

- Current version: v1
- Version is specified in URL path
- Breaking changes will increment version number

## WebSocket Support

### Real-time Updates

```
ws://localhost:8000/api/v1/ws
```

Events:
- `file.uploaded`
- `file.processed`
- `task.completed`

## Development Tools

### API Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI Schema: `/openapi.json`

### Health Check

```http
GET /health
```

Response:
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-01-01T12:00:00Z"
}
