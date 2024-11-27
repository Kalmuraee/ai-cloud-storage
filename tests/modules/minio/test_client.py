"""
Test module for MinIO client
"""
import io
import pytest
from unittest.mock import AsyncMock, Mock, patch
from minio.error import S3Error

from app.core.exceptions import StorageError
from app.modules.minio.client import MinioClient

@pytest.fixture
async def minio_client():
    with patch('minio.Minio') as mock_minio:
        # Mock bucket existence check
        mock_minio.return_value.bucket_exists.return_value = True
        
        client = MinioClient()
        client.client = mock_minio.return_value
        yield client

@pytest.mark.asyncio
async def test_put_object_success(minio_client):
    # Setup test data
    data = io.BytesIO(b"test data")
    length = len(data.getvalue())
    
    # Test object upload
    await minio_client.put_object(
        bucket_name="test-bucket",
        object_name="test.txt",
        data=data,
        length=length,
        content_type="text/plain"
    )
    
    # Verify MinIO client was called correctly
    minio_client.client.put_object.assert_called_once_with(
        "test-bucket",
        "test.txt",
        data,
        length,
        content_type="text/plain"
    )

@pytest.mark.asyncio
async def test_put_object_failure(minio_client):
    # Mock S3Error
    minio_client.client.put_object.side_effect = S3Error(
        code="TestError",
        message="Test error",
        resource="test.txt",
        request_id=None,
        host_id=None,
        response=None
    )
    
    # Test error handling
    with pytest.raises(StorageError):
        await minio_client.put_object(
            bucket_name="test-bucket",
            object_name="test.txt",
            data=io.BytesIO(b"test data"),
            length=9,
            content_type="text/plain"
        )

@pytest.mark.asyncio
async def test_get_object_success(minio_client):
    # Mock successful object retrieval
    mock_data = io.BytesIO(b"test data")
    minio_client.client.get_object.return_value = mock_data
    
    # Test object download
    result = await minio_client.get_object(
        bucket_name="test-bucket",
        object_name="test.txt"
    )
    
    assert result == mock_data
    minio_client.client.get_object.assert_called_once_with(
        "test-bucket",
        "test.txt"
    )

@pytest.mark.asyncio
async def test_get_object_failure(minio_client):
    # Mock S3Error
    minio_client.client.get_object.side_effect = S3Error(
        code="TestError",
        message="Test error",
        resource="test.txt",
        request_id=None,
        host_id=None,
        response=None
    )
    
    # Test error handling
    with pytest.raises(StorageError):
        await minio_client.get_object(
            bucket_name="test-bucket",
            object_name="test.txt"
        )

@pytest.mark.asyncio
async def test_remove_object_success(minio_client):
    # Test object removal
    await minio_client.remove_object(
        bucket_name="test-bucket",
        object_name="test.txt"
    )
    
    minio_client.client.remove_object.assert_called_once_with(
        "test-bucket",
        "test.txt"
    )

@pytest.mark.asyncio
async def test_remove_object_failure(minio_client):
    # Mock S3Error
    minio_client.client.remove_object.side_effect = S3Error(
        code="TestError",
        message="Test error",
        resource="test.txt",
        request_id=None,
        host_id=None,
        response=None
    )
    
    # Test error handling
    with pytest.raises(StorageError):
        await minio_client.remove_object(
            bucket_name="test-bucket",
            object_name="test.txt"
        )

@pytest.mark.asyncio
async def test_stat_object_success(minio_client):
    # Mock object stats
    mock_stats = Mock(size=100)
    minio_client.client.stat_object.return_value = mock_stats
    
    # Test stats retrieval
    result = await minio_client.stat_object(
        bucket_name="test-bucket",
        object_name="test.txt"
    )
    
    assert result == mock_stats
    minio_client.client.stat_object.assert_called_once_with(
        "test-bucket",
        "test.txt"
    )

@pytest.mark.asyncio
async def test_stat_object_failure(minio_client):
    # Mock S3Error
    minio_client.client.stat_object.side_effect = S3Error(
        code="TestError",
        message="Test error",
        resource="test.txt",
        request_id=None,
        host_id=None,
        response=None
    )
    
    # Test error handling
    with pytest.raises(StorageError):
        await minio_client.stat_object(
            bucket_name="test-bucket",
            object_name="test.txt"
        )
