# AI Cloud Storage Documentation

Welcome to the AI Cloud Storage documentation! This comprehensive guide will help you understand, set up, and use our advanced AI-powered cloud storage system.

## Quick Start

### Prerequisites

1. **System Requirements**
   - Python 3.11+
   - Docker and Docker Compose
   - 16GB+ RAM recommended
   - 4+ CPU cores recommended

2. **Required Software**
   - Git
   - Docker Desktop
   - Python virtual environment

### Setup Steps

1. **Clone the Repository**
```bash
git clone https://github.com/your-org/ai-cloud-storage.git
cd ai-cloud-storage
```

2. **Set Up Environment**
```bash
# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your settings
# Required variables:
# - DATABASE_URL
# - REDIS_URL
# - JWT_SECRET_KEY
# - MINIO_ROOT_USER
# - MINIO_ROOT_PASSWORD
```

4. **Start Services**
```bash
# Development mode
docker-compose -f docker-compose.dev.yml up -d

# Production mode
docker-compose up -d
```

5. **Access the System**
- API: http://localhost:8000/docs
- MinIO Console: http://localhost:9001
- Frontend: http://localhost:3000

## Project Structure

```
ai-cloud-storage/
├── app/                  # Main application code
│   ├── core/            # Core functionality
│   │   ├── config.py    # Configuration
│   │   ├── database.py  # Database setup
│   │   └── logging.py   # Logging setup
│   └── modules/         # Feature modules
│       ├── auth/        # Authentication
│       ├── storage/     # Storage operations
│       └── ai_processor/# AI processing
├── frontend/            # React frontend
├── tests/              # Test suite
└── docs/               # Documentation
```

## Architecture Overview

AI Cloud Storage follows a modular monolith architecture with three main modules:

1. **Auth Module** (`app/modules/auth`)
   - User management
   - Authentication
   - Authorization
   - Role-based access control

2. **Storage Module** (`app/modules/storage`)
   - File operations
   - Metadata management
   - MinIO integration
   - File versioning

3. **AI Processor Module** (`app/modules/ai_processor`)
   - Content analysis
   - Text extraction
   - Image processing
   - Semantic search

## Development Guide

1. **Database Migrations**
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

2. **Running Tests**
```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_file.py
```

3. **Code Style**
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8
```

## API Documentation

- **Auth API**: Authentication and user management
  - POST `/api/v1/auth/login`
  - POST `/api/v1/auth/register`
  - POST `/api/v1/auth/refresh`

- **Storage API**: File operations
  - POST `/api/v1/files/upload`
  - GET `/api/v1/files/{file_id}`
  - GET `/api/v1/files/search`

- **AI API**: AI processing
  - POST `/api/v1/ai/analyze`
  - POST `/api/v1/ai/extract`
  - GET `/api/v1/ai/search`

For detailed API documentation, visit `/docs` or `/redoc` when the server is running.

## Configuration

Key configuration options in `.env`:

```ini
# Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname

# Redis Cache
REDIS_URL=redis://:password@localhost:6379/0

# MinIO Storage
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Support

If you need help:
1. Check the [FAQ](./support/faq.md)
2. Search [existing issues](https://github.com/your-org/ai-cloud-storage/issues)
3. Create a new issue

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
