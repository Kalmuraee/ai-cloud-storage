"""
Test storage service
"""
import pytest
from fastapi import UploadFile
from io import BytesIO

from app.modules.storage.service import StorageService
from app.modules.storage.models import File, FileMetadata

@pytest.fixture
def storage_service():
    return StorageService()

@pytest.mark.asyncio
async def test_upload_file(storage_service):
    # Create test file
    content = b"test content"
    file = BytesIO(content)
    filename = "test.txt"
    
    # Upload file
    result = await storage_service.upload_file(
        file=file,
        filename=filename,
        metadata={"test": "metadata"}
    )
    
    assert result["filename"].endswith(filename)
    assert "path" in result
    assert result["metadata"]["test"] == "metadata"

@pytest.mark.asyncio
async def test_download_file(storage_service):
    # Upload test file first
    content = b"test content"
    file = BytesIO(content)
    filename = "test_download.txt"
    
    upload_result = await storage_service.upload_file(
        file=file,
        filename=filename
    )
    
    # Download file
    downloaded = await storage_service.download_file(upload_result["path"])
    assert downloaded.read() == content

@pytest.mark.asyncio
async def test_delete_file(storage_service):
    # Upload test file first
    content = b"test content"
    file = BytesIO(content)
    filename = "test_delete.txt"
    
    upload_result = await storage_service.upload_file(
        file=file,
        filename=filename
    )
    
    # Delete file
    await storage_service.delete_file(upload_result["path"])
    
    # Verify file is deleted
    with pytest.raises(Exception):
        await storage_service.download_file(upload_result["path"])

@pytest.mark.asyncio
async def test_list_files(storage_service):
    # Upload test files
    content = b"test content"
    file = BytesIO(content)
    
    await storage_service.upload_file(file=file, filename="test1.txt")
    await storage_service.upload_file(file=file, filename="test2.txt")
    
    # List files
    files = await storage_service.list_files()
    assert len(files) >= 2
