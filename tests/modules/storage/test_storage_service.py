"""
Test storage service
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from fastapi import UploadFile
from io import BytesIO

from app.modules.storage.service import StorageService
from app.modules.storage.repository import StorageRepository
from app.modules.storage.models import File, FileMetadata, FileStatus, ShareStatus
from app.modules.auth.models import User
from app.core.minio import MinioClient
from app.core.exceptions import ValidationError, DatabaseError, FileNotFoundError

@pytest_asyncio.fixture
async def test_user() -> User:
    """Create a test user."""
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        hashed_password="testpass",
        is_active=True
    )

@pytest.fixture
def mock_repo(test_user):
    repo = AsyncMock(spec=StorageRepository)
    repo.create_file.return_value = File(
        id=1,
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
    return repo

@pytest.fixture
def mock_minio():
    client = AsyncMock(spec=MinioClient)
    client.upload_file.return_value = "/test/test.txt"
    client.get_presigned_get_url.return_value = "http://test-url"
    client.get_presigned_put_url.return_value = "http://test-upload-url"
    client.stat_object.return_value = MagicMock(size=12)
    return client

@pytest.fixture
def storage_service(mock_repo, mock_minio):
    return StorageService(repo=mock_repo, minio_client=mock_minio)

@pytest.mark.asyncio
async def test_upload_file(storage_service, mock_repo, test_user):
    """Test file upload."""
    # Create test file
    content = b"test content"
    file = AsyncMock(spec=UploadFile)
    file.filename = "test.txt"
    file.content_type = "text/plain"
    file.read.return_value = content
    
    # Mock duplicate file check
    mock_repo.get_duplicate_files.return_value = []
    
    # Upload file
    result = await storage_service.upload_file(
        file=file,
        owner_id=test_user.id,
        folder_id=None,
        check_duplicates=True
    )
    
    assert result.file.filename == "test.txt"
    assert result.file.status == FileStatus.PROCESSED
    assert not result.is_duplicate

@pytest.mark.asyncio
async def test_upload_duplicate_file(storage_service, mock_repo, test_user):
    """Test uploading a duplicate file."""
    # Create test file
    content = b"test content"
    file = AsyncMock(spec=UploadFile)
    file.filename = "test.txt"
    file.content_type = "text/plain"
    file.read.return_value = content
    
    # Mock existing file
    existing_file = File(
        id=1,
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
    
    # Mock duplicate file check
    mock_repo.get_duplicate_files.return_value = [existing_file]
    
    # Upload file
    result = await storage_service.upload_file(
        file=file,
        owner_id=test_user.id,
        folder_id=None,
        check_duplicates=True
    )
    
    assert result.file.filename == "test.txt"
    assert result.file.status == FileStatus.PROCESSED
    assert result.is_duplicate

@pytest.mark.asyncio
async def test_list_files(storage_service, mock_repo, test_user):
    """Test listing files."""
    files = [
        File(
            id=1,
            filename="test1.txt",
            original_filename="test1.txt",
            path="/test/test1.txt",
            size=12,
            content_type="text/plain",
            bucket="test-bucket",
            owner_id=test_user.id,
            status=FileStatus.PROCESSED,
            version=1,
            is_latest=True,
            created_at=datetime.now()
        ),
        File(
            id=2,
            filename="test2.txt",
            original_filename="test2.txt",
            path="/test/test2.txt",
            size=15,
            content_type="text/plain",
            bucket="test-bucket",
            owner_id=test_user.id,
            status=FileStatus.PROCESSED,
            version=1,
            is_latest=True,
            created_at=datetime.now()
        )
    ]
    
    # Mock repository response
    mock_repo.list_files_by_user.return_value = (files, 2)
    
    result, total = await storage_service.list_files(user_id=test_user.id)
    assert len(result) == 2
    assert total == 2
    assert all(f.status == FileStatus.PROCESSED for f in result)

@pytest.mark.asyncio
async def test_get_shared_items(storage_service, mock_repo, test_user):
    """Test getting shared items."""
    shared_items = [
        {
            "id": 1,
            "file_id": 1,
            "owner_id": test_user.id,
            "shared_with_id": 2,
            "status": ShareStatus.ACCEPTED,
            "created_at": datetime.now()
        },
        {
            "id": 2,
            "file_id": 1,
            "owner_id": test_user.id,
            "shared_with_id": 3,
            "status": ShareStatus.DECLINED,
            "created_at": datetime.now()
        }
    ]
    
    # Mock repository response
    mock_repo.get_shared_items.return_value = shared_items
    
    result = await storage_service.get_shared_items(user_id=test_user.id)
    assert len(result) == 2
    statuses = {s["status"] for s in result}
    assert ShareStatus.ACCEPTED in statuses
    assert ShareStatus.DECLINED in statuses

@pytest.mark.asyncio
async def test_update_file_status(storage_service, mock_repo, test_user):
    """Test updating file status."""
    file_id = 1
    new_status = FileStatus.PROCESSED
    
    await storage_service.update_file_status(file_id, new_status)
    mock_repo.update_file_status.assert_called_once_with(file_id, new_status)

@pytest.mark.asyncio
async def test_delete_file(storage_service, mock_repo, mock_minio, test_user):
    """Test deleting a file."""
    file = File(
        id=1,
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
    
    # Mock repository response
    mock_repo.get_file_by_id.return_value = file
    
    await storage_service.delete_file(file_id=1, user_id=test_user.id)

    # Verify file was deleted
    mock_repo.delete_file.assert_called_once_with(file_id=1)
    mock_minio.remove_object.assert_called_once_with("test-bucket", "/test/test.txt")
