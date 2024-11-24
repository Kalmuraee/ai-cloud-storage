# AI Cloud Storage

An AI-powered cloud storage service built with FastAPI using a modular monolith architecture.

## Architecture

This project follows a modular monolith architecture, which provides a balance between the simplicity of a monolith and the maintainability of microservices. The codebase is organized into distinct modules, each with its own clear boundaries and responsibilities.

### Core Modules

1. **Storage Module** (`app/modules/storage`)
   - File storage and retrieval
   - File metadata management
   - Storage optimization

2. **AI Processor Module** (`app/modules/ai_processor`)
   - File content analysis
   - AI-powered search
   - Content classification
   - Text extraction and processing

3. **Auth Module** (`app/modules/auth`)
   - User authentication
   - Authorization
   - Token management

### Shared Components

- **Core** (`app/core`)
  - Configuration
  - Logging
  - Database connections
  - Cache management
  - Common utilities

### Project Structure

```
ai-cloud-storage/
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── cache.py
│   ├── modules/
│   │   ├── storage/
│   │   │   ├── models.py
│   │   │   ├── service.py
│   │   │   └── routes.py
│   │   ├── ai_processor/
│   │   │   ├── models.py
│   │   │   ├── service.py
│   │   │   └── routes.py
│   │   └── auth/
│   │       ├── models.py
│   │       ├── service.py
│   │       └── routes.py
│   └── main.py
├── tests/
├── alembic/
├── requirements.txt
└── docker-compose.yml
```

## Features

- File upload and download
- AI-powered file search
- Content analysis and classification
- User authentication and authorization
- File metadata management
- Caching and performance optimization

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **Cache**: Redis
- **Storage**: MinIO
- **AI/ML**: LangChain, Transformers
- **Authentication**: JWT

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-cloud-storage.git
   cd ai-cloud-storage
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Start the services:
   ```bash
   docker-compose up -d  # Starts PostgreSQL, Redis, and MinIO
   ```

6. Run migrations:
   ```bash
   alembic upgrade head
   ```

7. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at http://localhost:8000/api/docs

## Development

- **Code Style**: Black + isort
- **Testing**: pytest
- **Documentation**: OpenAPI (Swagger)

## License

This project is licensed under the MIT License - see the LICENSE file for details.