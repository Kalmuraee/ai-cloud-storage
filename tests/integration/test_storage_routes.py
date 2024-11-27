"""
Integration tests for storage routes
"""
import io
import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_upload_file(async_client, auth_headers, test_file_data):
    """Test file upload endpoint."""
    files = {
        "file": (
            test_file_data["filename"],
            io.BytesIO(b"test content"),
            test_file_data["content_type"]
        )
    }
    metadata = test_file_data["metadata"]
    
    response = await async_client.post(
        "/api/v1/storage/upload",
        headers=auth_headers,
        files=files,
        data={"metadata": str(metadata)}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["filename"] == test_file_data["filename"]
    assert data["content_type"] == test_file_data["content_type"]
    assert "id" in data
    assert "user_id" in data

async def test_list_files(async_client, auth_headers, test_file):
    """Test list files endpoint."""
    response = await async_client.get(
        "/api/v1/storage/files",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(file["id"] == str(test_file.id) for file in data)

async def test_get_file(async_client, auth_headers, test_file):
    """Test get file endpoint."""
    response = await async_client.get(
        f"/api/v1/storage/files/{test_file.id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_file.id)
    assert data["filename"] == test_file.filename

async def test_download_file(async_client, auth_headers, test_file, minio_client):
    """Test file download endpoint."""
    # Ensure file exists in MinIO
    bucket_name = "test-bucket"
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
    
    minio_client.put_object(
        bucket_name,
        str(test_file.id),
        io.BytesIO(b"test content"),
        length=len(b"test content")
    )
    
    response = await async_client.get(
        f"/api/v1/storage/download/{test_file.id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.content == b"test content"

async def test_update_file_metadata(async_client, auth_headers, test_file):
    """Test update file metadata endpoint."""
    new_metadata = {"updated": "metadata"}
    response = await async_client.put(
        f"/api/v1/storage/files/{test_file.id}/metadata",
        headers=auth_headers,
        json=new_metadata
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["metadata"] == new_metadata

async def test_delete_file(async_client, auth_headers, test_file):
    """Test file deletion endpoint."""
    response = await async_client.delete(
        f"/api/v1/storage/files/{test_file.id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify file is deleted
    response = await async_client.get(
        f"/api/v1/storage/files/{test_file.id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_search_files(async_client, auth_headers, test_file):
    """Test file search endpoint."""
    response = await async_client.get(
        "/api/v1/storage/search",
        headers=auth_headers,
        params={"query": test_file.filename}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(file["id"] == str(test_file.id) for file in data)

async def test_get_duplicates(async_client, auth_headers, test_file):
    """Test get duplicates endpoint."""
    # Upload a duplicate file
    files = {
        "file": (
            test_file.filename,
            io.BytesIO(b"test content"),
            test_file.content_type
        )
    }
    metadata = {"test": "metadata"}
    
    response = await async_client.post(
        "/api/v1/storage/upload",
        headers=auth_headers,
        files=files,
        data={"metadata": str(metadata)}
    )
    assert response.status_code == status.HTTP_201_CREATED
    
    # Get duplicates
    response = await async_client.get(
        "/api/v1/storage/duplicates",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Each item should have original and duplicates
    first_group = data[0]
    assert "original" in first_group
    assert "duplicates" in first_group
    assert isinstance(first_group["duplicates"], list)
    assert len(first_group["duplicates"]) > 0

async def test_no_duplicates(async_client, auth_headers):
    """Test get duplicates endpoint with no duplicates."""
    response = await async_client.get(
        "/api/v1/storage/duplicates",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

async def test_unauthorized_access(async_client, test_file):
    """Test unauthorized access to storage endpoints."""
    endpoints = [
        ("GET", f"/api/v1/storage/files"),
        ("GET", f"/api/v1/storage/files/{test_file.id}"),
        ("GET", f"/api/v1/storage/download/{test_file.id}"),
        ("PUT", f"/api/v1/storage/files/{test_file.id}/metadata"),
        ("DELETE", f"/api/v1/storage/files/{test_file.id}"),
        ("GET", "/api/v1/storage/search"),
        ("GET", "/api/v1/storage/duplicates")
    ]
    
    for method, endpoint in endpoints:
        response = await async_client.request(method, endpoint)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
