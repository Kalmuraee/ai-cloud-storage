"""
Test storage service
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi import UploadFile
from io import BytesIO
from datetime import datetime

from app.modules.storage.service import StorageService
from app.modules.storage.models import File, FileMetadata, FileStatus
from app.modules.storage.repository import StorageRepository
from app.core.minio import MinioClient
from app.modules.storage.schemas import FileCreate, FileMetadataCreate

@pytest.fixture
def mock_repo():
    repo = AsyncMock(spec=StorageRepository)
    repo.create_file.return_value = File(
        id=1,
        filename="test.txt",
        original_filename="test.txt",
        path="/test/test.txt",
        size=12,
        content_type="text/plain",
        bucket="test-bucket",
        owner_id=1,
        status=FileStatus.PROCESSED,
        version=1,
        is_latest=True,
        created_at=datetime.now(),
        updated_at=None
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
def mock_file():
    return File(
        id=1,
        filename="test.txt",
        original_filename="test.txt",
        path="/test/test.txt",
        size=12,
        content_type="text/plain",
        bucket="test-bucket",
        owner_id=1,
        status=FileStatus.PROCESSED,
        version=1,
        is_latest=True,
        created_at=datetime.now(),
        updated_at=None
    )

@pytest.fixture
def storage_service(mock_repo, mock_minio):
    return StorageService(repo=mock_repo, minio_client=mock_minio)

@pytest.mark.asyncio
async def test_upload_file(storage_service, mock_file):
    # Create test file
    content = b"test content"
    file = AsyncMock(spec=UploadFile)
    file.filename = "test.txt"
    file.content_type = "text/plain"
    file.read.return_value = content
    
    # Mock duplicate file
    storage_service.repo.get_duplicate_files.return_value = [mock_file]
    storage_service.repo.create_file.return_value = mock_file
    
    # Upload file
    result = await storage_service.upload_file(
        file=file,
        owner_id=1,
        folder_id=None,
        check_duplicates=True
    )
    
    assert result.file.filename == "test.txt"
    assert result.file.path == "/test/test.txt"
    assert result.is_duplicate

@pytest.mark.asyncio
async def test_download_file(storage_service, mock_file):
    file_path = "/test/test.txt"
    user_id = 1
    
    # Mock file exists
    storage_service.repo.get_file_by_path.return_value = mock_file
    storage_service.minio_client.get_object.return_value = AsyncMock(presigned_url="http://test-url")
    
    result = await storage_service.download_file(file_path=file_path, user_id=user_id)
    assert result.presigned_url == "http://test-url"

@pytest.mark.asyncio
async def test_delete_file(storage_service, mock_file):
    file_id = 1
    user_id = 1
    
    # Mock file exists
    storage_service.repo.get_file_by_id.return_value = mock_file
    
    # Call delete_file with keyword arguments
    await storage_service.delete_file(file_id=file_id, user_id=user_id)
    
    # Verify correct calls were made
    storage_service.repo.get_file_by_id.assert_called_once_with(file_id)
    storage_service.minio_client.remove_object.assert_called_once_with(
        bucket_name=mock_file.bucket, 
        object_name=mock_file.path
    )
    storage_service.repo.delete_file.assert_called_once_with(file_id)

@pytest.mark.asyncio
async def test_list_files(storage_service):
    user_id = 1
    files = [
        File(
            id=1,
            filename="test1.txt",
            original_filename="test1.txt",
            path="/test/test1.txt",
            size=12,
            content_type="text/plain",
            bucket="test-bucket",
            owner_id=user_id,
            status=FileStatus.PROCESSED,
            version=1,
            is_latest=True,
            created_at=datetime.now(),
            updated_at=None
        ),
        File(
            id=2,
            filename="test2.txt",
            original_filename="test2.txt",
            path="/test/test2.txt",
            size=15,
            content_type="text/plain",
            bucket="test-bucket",
            owner_id=user_id,
            status=FileStatus.PROCESSED,
            version=1,
            is_latest=True,
            created_at=datetime.now(),
            updated_at=None
        )
    ]
    
    # Mock repository response
    storage_service.repo.list_files_by_user.return_value = (files, 2)
    
    result, total = await storage_service.list_files(user_id=user_id)
    assert len(result) == 2
    assert total == 2
    assert result[0].filename == "test1.txt"
    assert result[1].filename == "test2.txt"
