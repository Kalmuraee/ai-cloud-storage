"""
Test storage repository
"""
import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.storage.repository import StorageRepository
from app.modules.storage.models import File, FileMetadata, FileStatus, ShareStatus
from app.modules.auth.models import User
from app.core.exceptions import ValidationError, DatabaseError

@pytest.fixture
def storage_repo(db: AsyncSession):
    return StorageRepository(db)

@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email=f"test_{datetime.now().timestamp()}@example.com",
        username=f"testuser_{datetime.now().timestamp()}",
        hashed_password="testpass",
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_file(db: AsyncSession, test_user: User) -> File:
    """Create a test file."""
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
        created_at=datetime.now()
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file

@pytest.mark.asyncio
async def test_create_file(storage_repo: StorageRepository, db: AsyncSession):
    """Test creating a file."""
    file_data = {
        "filename": "test.txt",
        "original_filename": "test.txt",
        "path": "/test/test.txt",
        "size": 12,
        "content_type": "text/plain",
        "bucket": "test-bucket",
        "owner_id": 1,
        "status": FileStatus.PROCESSED,
        "version": 1,
        "is_latest": True,
        "created_at": datetime.now()
    }
    
    file = await storage_repo.create_file(FileCreate(**file_data))
    assert file.filename == file_data["filename"]
    assert file.status == FileStatus.PROCESSED

@pytest.mark.asyncio
async def test_get_file_by_path(storage_repo: StorageRepository, test_file: File):
    """Test getting a file by path."""
    file = await storage_repo.get_file_by_path(test_file.path, test_file.owner_id)
    assert file is not None
    assert file.id == test_file.id
    assert file.status == FileStatus.PROCESSED

@pytest.mark.asyncio
async def test_list_files_by_user(storage_repo: StorageRepository, test_file: File):
    """Test listing files for a user."""
    files, total = await storage_repo.list_files_by_user(
        owner_id=test_file.owner_id,
        prefix=None,
        recursive=True,
        limit=100,
        offset=0
    )
    assert len(files) > 0
    assert total > 0
    assert all(f.status == FileStatus.PROCESSED for f in files)
    assert any(f.id == test_file.id for f in files)

@pytest.mark.asyncio
async def test_get_duplicate_files_by_user(storage_repo: StorageRepository, test_file: File):
    """Test getting duplicate files for a user."""
    # Create a duplicate file
    duplicate = File(
        filename="test_dup.txt",
        original_filename="test_dup.txt",
        path="/test/test_dup.txt",
        size=12,
        content_type="text/plain",
        bucket="test-bucket",
        owner_id=test_file.owner_id,
        status=FileStatus.PROCESSED,
        version=1,
        is_latest=True,
        created_at=datetime.now(),
        checksum=test_file.checksum  # Same checksum makes it a duplicate
    )
    storage_repo.db.add(duplicate)
    await storage_repo.db.commit()
    
    duplicates = await storage_repo.get_duplicate_files_by_user(test_file.owner_id)
    assert len(duplicates) > 0
    assert all(d.status == FileStatus.PROCESSED for d in duplicates)

@pytest.mark.asyncio
async def test_get_shared_items(storage_repo: StorageRepository, test_file: File):
    """Test getting shared items."""
    # Create a shared item
    shared_item_data = SharedItem(
        file_id=test_file.id,
        owner_id=test_file.owner_id,
        shared_with_id=2,
        status=ShareStatus.ACCEPTED
    )
    shared_item = await storage_repo.create_shared_item(shared_item_data)
    
    shared_items = await storage_repo.get_shared_items(test_file.owner_id)
    assert len(shared_items) > 0
    assert any(s.id == shared_item.id for s in shared_items)
    assert all(s.status == ShareStatus.ACCEPTED for s in shared_items)

@pytest.mark.asyncio
async def test_get_shared_items_by_file(storage_repo: StorageRepository, test_file: File):
    """Test getting shared items for a specific file."""
    # Create test users first
    user1 = await storage_repo.db.execute(
        "INSERT INTO users (email, hashed_password) VALUES ('user1@test.com', 'hash') RETURNING id"
    )
    user2 = await storage_repo.db.execute(
        "INSERT INTO users (email, hashed_password) VALUES ('user2@test.com', 'hash') RETURNING id"
    )
    user1_id = await user1.scalar()
    user2_id = await user2.scalar()
    
    # Create shared items
    shared_item_data1 = SharedItem(
        file_id=test_file.id,
        owner_id=test_file.owner_id,
        shared_with_id=user1_id,
        status=ShareStatus.ACCEPTED
    )
    shared_item1 = await storage_repo.create_shared_item(shared_item_data1)
    
    shared_item_data2 = SharedItem(
        file_id=test_file.id,
        owner_id=test_file.owner_id,
        shared_with_id=user2_id,
        status=ShareStatus.DECLINED
    )
    shared_item2 = await storage_repo.create_shared_item(shared_item_data2)
    
    shared_items = await storage_repo.get_shared_items_by_file(test_file.id)
    assert len(shared_items) == 2
    statuses = {s.status for s in shared_items}
    assert ShareStatus.ACCEPTED in statuses
    assert ShareStatus.DECLINED in statuses

@pytest.mark.asyncio
async def test_delete_shared_item(storage_repo: StorageRepository, test_file: File):
    """Test deleting a shared item."""
    # Create a shared item
    shared_item_data = SharedItem(
        file_id=test_file.id,
        owner_id=test_file.owner_id,
        shared_with_id=2,
        status=ShareStatus.ACCEPTED
    )
    shared_item = await storage_repo.create_shared_item(shared_item_data)
    
    # Delete the shared item
    await storage_repo.delete_shared_item(shared_item.id)
    
    # Verify deletion
    shared_items = await storage_repo.get_shared_items(test_file.owner_id)
    assert all(s.id != shared_item.id for s in shared_items)

@pytest.mark.asyncio
async def test_update_file_status(storage_repo: StorageRepository, test_file: File):
    """Test updating file status."""
    await storage_repo.update_file_status(test_file.id, FileStatus.PROCESSED)
    updated_file = await storage_repo.get_file_by_id(test_file.id)
    assert updated_file.status == FileStatus.PROCESSED

@pytest.mark.asyncio
async def test_delete_file(storage_repo: StorageRepository, test_file: File):
    """Test deleting a file."""
    await storage_repo.delete_file(test_file.id)
    deleted_file = await storage_repo.get_file_by_id(test_file.id)
    assert deleted_file is None
