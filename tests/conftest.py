"""
Test configuration and fixtures for modular AI cloud storage
"""
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from minio import Minio
import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import Base, get_db
from app.modules.auth.models import User
from app.modules.storage.models import File, FileMetadata
from app.modules.ai_processor.models import ProcessingTask, ProcessingResult
from app.main import create_app

settings = Settings()

# Test database
TEST_POSTGRES_URL = os.getenv("TEST_POSTGRES_URL", "postgresql+asyncpg://test:test@localhost:5432/test_aicloud")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_POSTGRES_URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.fixture
def app(db_session) -> FastAPI:
    """Create a test FastAPI application."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    return app

@pytest.fixture
def client(app) -> TestClient:
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def minio_client():
    """Create a test MinIO client."""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_SECURE
    )

@pytest_asyncio.fixture
async def redis_client():
    """Create a test Redis client."""
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True
    )
    yield client
    await client.close()

@pytest.fixture
def test_user_data() -> Dict[str, str]:
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "Test123!@#",
        "full_name": "Test User"
    }

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_data: dict) -> User:
    """Create a test user."""
    from app.modules.auth.service import AuthService
    
    auth_service = AuthService()
    user = await auth_service.create_user(
        email=test_user_data["email"],
        password=test_user_data["password"],
        db=db_session
    )
    return user

@pytest.fixture
def test_file_data() -> Dict[str, Any]:
    """Test file data."""
    return {
        "filename": "test.txt",
        "content_type": "text/plain",
        "size": 100,
        "metadata": {"test": "metadata"}
    }

@pytest_asyncio.fixture
async def test_file(db_session: AsyncSession, test_user: User, test_file_data: dict) -> File:
    """Create a test file."""
    file = File(
        filename=test_file_data["filename"],
        content_type=test_file_data["content_type"],
        size=test_file_data["size"],
        user_id=test_user.id
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)
    return file

@pytest_asyncio.fixture
async def test_processing_task(db_session: AsyncSession, test_file: File) -> ProcessingTask:
    """Create a test processing task."""
    task = ProcessingTask(
        file_id=test_file.id,
        task_type="text_classification",
        status="pending"
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task

@pytest.fixture
def auth_headers(test_user: User) -> Dict[str, str]:
    """Generate authentication headers."""
    from app.modules.auth.service import create_access_token
    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}
