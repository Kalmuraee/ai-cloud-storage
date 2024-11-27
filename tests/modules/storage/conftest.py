"""
Test fixtures for storage repository tests.
"""
import uuid
import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.storage.repository import StorageRepository
from app.modules.storage.models import File, FileStatus
from app.core.database import get_db
from app.modules.auth.models import User

@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user for testing."""
    unique_id = str(uuid.uuid4())
    user = User(
        email=f"test_{unique_id}@example.com",
        username=f"test_user_{unique_id}",
        hashed_password="test_hash",
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def storage_repo(db: AsyncSession) -> StorageRepository:
    """Create a storage repository instance for testing."""
    return StorageRepository(db)

@pytest_asyncio.fixture
async def test_file(storage_repo: StorageRepository, test_user: User, db: AsyncSession) -> File:
    """Create a test file for testing."""
    file = File(
        filename="test.txt",
        original_filename="test.txt",
        path="/test/test.txt",
        size=12,
        content_type="text/plain",
        bucket="test-bucket",
        owner_id=test_user.id,
        status=FileStatus.PROCESSED,
        version=1,
        is_latest=True,
        created_at=datetime.now(),
        checksum="test_checksum"
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file
