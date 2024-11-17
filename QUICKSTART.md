# Quick Start Guide

This guide will help you set up and run the AI Cloud Storage platform for development.

## Prerequisites

1. Docker and Docker Compose
2. Python 3.9+
3. Poetry (Python package manager)
4. Node.js 18+
5. npm

## Services Overview

The platform consists of several services:
- Storage Service (FastAPI)
- AI Processor Service (FastAPI)
- Frontend (Next.js)
- MinIO (Object Storage)
- Weaviate (Vector Database)
- Kafka (Message Broker)
- PostgreSQL (Metadata Storage)

## Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-cloud-storage
```

2. Set up environment variables:
```bash
# Create .env file in the root directory
cp .env.example .env

# Add your HuggingFace API key
echo "HUGGINGFACE_API_KEY=your-api-key" >> .env
```

3. Start the infrastructure services:
```bash
docker-compose up -d minio weaviate kafka zookeeper postgres
```

4. Set up the Storage Service:
```bash
cd services/storage
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

5. Set up the AI Processor Service:
```bash
cd services/ai-processor
poetry install
poetry run uvicorn app.main:app --reload --port 8001
```

6. Set up the Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Accessing Services

- Frontend: http://localhost:3000
- Storage Service API: http://localhost:8000
- AI Processor Service API: http://localhost:8001
- MinIO Console: http://localhost:9001
- Weaviate Console: http://localhost:8080

## API Documentation

- Storage Service Swagger UI: http://localhost:8000/docs
- Storage Service ReDoc: http://localhost:8000/redoc
- AI Processor Service Swagger UI: http://localhost:8001/docs
- AI Processor Service ReDoc: http://localhost:8001/redoc

## Development Workflow

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:
```bash
git add .
git commit -m "feat: your feature description"
```

3. Push your changes and create a pull request:
```bash
git push origin feature/your-feature-name
```

## Running Tests

Each service has its own test suite:

```bash
# Storage Service
cd services/storage
poetry run pytest

# AI Processor Service
cd services/ai-processor
poetry run pytest

# Frontend
cd frontend
npm test
```

## Common Issues

1. If services can't connect to each other, make sure all containers are running:
```bash
docker-compose ps
```

2. If MinIO is not accessible, check its logs:
```bash
docker-compose logs minio
```

3. For Kafka connection issues, ensure the broker is ready:
```bash
docker-compose logs kafka
```

## Next Steps

1. Review the API documentation
2. Check the project structure
3. Read through the code documentation
4. Start with small features or bug fixes

For more detailed information, check the following documentation:
- [Project Overview](README.md)
- [Architecture Documentation](docs/architecture.md)
- [API Documentation](docs/api.md)
- [Contributing Guidelines](docs/contributing.md)