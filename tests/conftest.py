"""Test configuration and fixtures."""
import os
import pytest
import logging
import asyncio
from typing import AsyncGenerator, Generator
import httpx
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from fastapi.testclient import TestClient
from minio import Minio
from passlib.context import CryptContext

from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.modules.auth.security import create_access_token
from app.modules.auth.models import User, Token

from tests.logging_config import setup_test_logging

# Set up logging for tests
setup_test_logging()
logger = logging.getLogger(__name__)

# Create test database URL with test user
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/ai_cloud_storage_test"

logger.info(f"Using test database URL: {TEST_DATABASE_URL}")

# Create password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create async engine for tests
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

# Create async session factory
TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database on each testing session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create a new session for the test
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            # Clean up at the end of the session
            await session.close()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="session")
def test_user():
    """Create a test user for authentication."""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "is_active": True
    }

@pytest.fixture(scope="session")
async def test_user_token(test_user, db: AsyncSession) -> str:
    """Create a JWT token for the test user and store it in the database."""
    try:
        # Create the test user in the database if it doesn't exist
        user = User(
            id=test_user["id"],
            email=test_user["email"],
            username=test_user["username"],
            hashed_password=pwd_context.hash("testpassword"),
            is_active=test_user["is_active"]
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Create JWT token with long expiration for tests
        expires_delta = timedelta(days=365)  # 1 year expiration for tests
        expires_at = datetime.utcnow() + expires_delta
        token_data = {
            "sub": str(user.id),
            "exp": int(expires_at.timestamp())
        }
        access_token = create_access_token(token_data, expires_delta)

        # Store token in database
        token = Token(
            token=access_token,
            token_type="bearer",
            user_id=user.id,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(token)
        await db.commit()

        return access_token
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create test user token: {str(e)}")
        raise

@pytest.fixture(scope="session")
def client() -> Generator:
    """Create a test client using the test database."""
    async def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            await db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create an async test client."""
    async def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            await db.close()

    app.dependency_overrides[get_db] = override_get_db
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
def minio_client() -> Minio:
    """Create a MinIO client for testing."""
    try:
        return Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
    except Exception as e:
        logger.error(f"Failed to create MinIO client: {str(e)}")
        raise

@pytest.fixture(autouse=True)
async def cleanup_test_data(db: AsyncSession):
    """Clean up test data after each test."""
    yield
    try:
        # Ensure any existing transaction is rolled back
        await db.rollback()
        
        # Delete data in correct order to handle foreign key constraints
        await db.execute(text("DELETE FROM shared_items WHERE owner_id != 1"))
        await db.execute(text("DELETE FROM file_metadata WHERE file_id IN (SELECT id FROM files WHERE owner_id != 1)"))
        await db.execute(text("DELETE FROM file_versions WHERE file_id IN (SELECT id FROM files WHERE owner_id != 1)"))
        await db.execute(text("DELETE FROM files WHERE owner_id != 1"))
        await db.execute(text("DELETE FROM user_roles WHERE user_id != 1"))
        await db.execute(text("DELETE FROM tokens WHERE user_id != 1"))
        await db.execute(text("DELETE FROM users WHERE id != 1"))
        await db.execute(text("DELETE FROM roles WHERE id != 1"))
        
        # Reset sequences to handle the preserved test user
        await db.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
        await db.execute(text("SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles))"))
        
        await db.commit()
    except Exception as e:
        logger.error(f"Error cleaning up test data: {str(e)}")
        await db.rollback()
