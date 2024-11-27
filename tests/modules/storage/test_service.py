"""
Test module for storage service
"""
import os
import pytest
import hashlib
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import AsyncGenerator

from app.core.config import settings
from app.core.exceptions import ValidationError, StorageError, NotFoundException
from app.modules.storage.models import File, FileStatus, ShareStatus
from app.modules.storage.schemas import FileCreate, FileUploadResponse
from app.modules.storage.service import StorageService
from app.modules.storage.repository import StorageRepository
from app.modules.minio.client import MinioClient

@pytest.fixture
async def storage_repo() -> AsyncGenerator[StorageRepository, None]:
    repo = AsyncMock(spec=StorageRepository)
    yield repo

@pytest.fixture
async def minio_client() -> AsyncGenerator[MinioClient, None]:
    client = AsyncMock(spec=MinioClient)
    yield client

@pytest.fixture
async def storage_service(storage_repo: StorageRepository, minio_client: MinioClient) -> StorageService:
    return StorageService(storage_repo, minio_client)

@pytest.mark.asyncio
async def test_compute_file_hash(storage_service: StorageService, tmp_path):
    # Create a test file with known content
    test_file = tmp_path / "test.txt"
    content = b"test content"
    test_file.write_bytes(content)
    
    # Compute expected hash
    expected_hash = hashlib.sha256(content).hexdigest()
    
    # Test hash computation
    computed_hash = await storage_service.compute_file_hash(str(test_file))
    assert computed_hash == expected_hash

@pytest.mark.asyncio
async def test_upload_file_success(storage_service: StorageService, storage_repo: StorageRepository, minio_client: MinioClient, tmp_path):
    # Setup test data
    test_file = tmp_path / "test.txt"
    content = b"test content"
    test_file.write_bytes(content)
    
    file_data = FileCreate(
        name="test.txt",
        size=len(content),
        mime_type="text/plain",
        owner_id=1,
        folder_id=None,
        status=FileStatus.PROCESSED
    )
    
    # Mock repository responses
    storage_repo.get_duplicate_files.return_value = []
    storage_repo.create_file.return_value = File(
        id=1,
        name="test.txt",
        size=len(content),
        mime_type="text/plain",
        owner_id=1,
        status=FileStatus.PROCESSED,
        created_at=datetime.now()
    )
    
    # Mock MinIO client responses
    minio_client.stat_object.return_value = Mock(size=len(content))
    
    # Test file upload
    response = await storage_service.upload_file(
        file_path=str(test_file),
        name="test.txt",
        mime_type="text/plain",
        owner_id=1
    )
    
    assert isinstance(response, FileUploadResponse)
    assert response.file.name == "test.txt"
    assert response.file.size == len(content)
    assert response.file.status == FileStatus.PROCESSED

@pytest.mark.asyncio
async def test_upload_file_with_duplicate(storage_service: StorageService, storage_repo: StorageRepository, tmp_path):
    # Setup test data
    test_file = tmp_path / "test.txt"
    content = b"test content"
    test_file.write_bytes(content)
    
    existing_file = File(
        id=1,
        name="existing.txt",
        size=len(content),
        mime_type="text/plain",
        owner_id=2,
        status=FileStatus.PROCESSED,
        created_at=datetime.now()
    )
    
    # Mock repository responses
    storage_repo.get_duplicate_files.return_value = [existing_file]
    storage_repo.create_file.return_value = File(
        id=2,
        name="test.txt",
        size=len(content),
        mime_type="text/plain",
        owner_id=1,
        status=FileStatus.PROCESSED,
        created_at=datetime.now(),
        duplicate_of=1
    )
    
    # Test file upload with deduplication
    response = await storage_service.upload_file(
        file_path=str(test_file),
        name="test.txt",
        mime_type="text/plain",
        owner_id=1,
        check_duplicates=True
    )
    
    assert isinstance(response, FileUploadResponse)
    assert response.file.duplicate_of == 1
    assert response.is_duplicate is True

@pytest.mark.asyncio
async def test_upload_file_validation_error(storage_service: StorageService):
    with pytest.raises(ValidationError):
        await storage_service.upload_file(
            file_path="nonexistent.txt",
            name="test.txt",
            mime_type="text/plain",
            owner_id=None
        )

@pytest.mark.asyncio
async def test_download_file_success(storage_service: StorageService, storage_repo: StorageRepository, minio_client: MinioClient):
    # Mock file data
    test_file = File(
        id=1,
        name="test.txt",
        size=100,
        mime_type="text/plain",
        owner_id=1,
        status=FileStatus.PROCESSED,
        created_at=datetime.now()
    )
    
    # Mock repository responses
    storage_repo.get_file_by_path.return_value = test_file
    
    # Mock MinIO client responses
    minio_client.get_object.return_value = AsyncMock()
    
    # Test file download
    result = await storage_service.download_file(
        file_path="test.txt",
        user_id=1
    )
    
    assert result is not None
    storage_repo.get_file_by_path.assert_called_once_with("test.txt", 1)
    minio_client.get_object.assert_called_once()

@pytest.mark.asyncio
async def test_download_file_not_found(storage_service: StorageService, storage_repo: StorageRepository):
    storage_repo.get_file_by_path.side_effect = NotFoundException("File not found")
    
    with pytest.raises(NotFoundException):
        await storage_service.download_file(
            file_path="nonexistent.txt",
            user_id=1
        )

@pytest.mark.asyncio
async def test_download_file_permission_error(storage_service: StorageService, storage_repo: StorageRepository):
    # Mock file owned by different user
    test_file = File(
        id=1,
        name="test.txt",
        size=100,
        mime_type="text/plain",
        owner_id=2,  # Different owner
        status=FileStatus.PROCESSED,
        created_at=datetime.now()
    )
    
    storage_repo.get_file_by_path.return_value = test_file
    storage_repo.get_shared_items_for_user.return_value = []  # No sharing permissions
    
    with pytest.raises(PermissionError):
        await storage_service.download_file(
            file_path="test.txt",
            user_id=1
        )
