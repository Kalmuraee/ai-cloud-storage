"""
Integration tests for folder management routes
"""
import pytest
from fastapi import status
from httpx import AsyncClient
from uuid import UUID

pytestmark = pytest.mark.asyncio

async def test_create_folder(async_client, auth_headers):
    """Test folder creation endpoint."""
    folder_data = {
        "name": "Test Folder",
        "description": "Test folder description",
        "parent_id": None
    }
    
    response = await async_client.post(
        "/api/v1/storage/folders",
        headers=auth_headers,
        json=folder_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == folder_data["name"]
    assert data["description"] == folder_data["description"]
    assert "id" in data
    assert "created_at" in data
    return data

async def test_list_folders(async_client, auth_headers):
    """Test list folders endpoint."""
    # Create a test folder first
    folder = await test_create_folder(async_client, auth_headers)
    
    response = await async_client.get(
        "/api/v1/storage/folders",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(f["id"] == folder["id"] for f in data)

async def test_get_folder_details(async_client, auth_headers):
    """Test get folder details endpoint."""
    # Create a test folder first
    folder = await test_create_folder(async_client, auth_headers)
    
    response = await async_client.get(
        f"/api/v1/storage/folders/{folder['id']}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == folder["id"]
    assert data["name"] == folder["name"]
    assert data["description"] == folder["description"]

async def test_update_folder(async_client, auth_headers):
    """Test update folder endpoint."""
    # Create a test folder first
    folder = await test_create_folder(async_client, auth_headers)
    
    update_data = {
        "name": "Updated Folder Name",
        "description": "Updated folder description"
    }
    
    response = await async_client.put(
        f"/api/v1/storage/folders/{folder['id']}",
        headers=auth_headers,
        json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == folder["id"]
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]

async def test_delete_folder(async_client, auth_headers):
    """Test folder deletion endpoint."""
    # Create a test folder first
    folder = await test_create_folder(async_client, auth_headers)
    
    response = await async_client.delete(
        f"/api/v1/storage/folders/{folder['id']}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify folder is deleted
    response = await async_client.get(
        f"/api/v1/storage/folders/{folder['id']}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_move_folder(async_client, auth_headers):
    """Test move folder endpoint."""
    # Create two test folders
    source_folder = await test_create_folder(async_client, auth_headers)
    target_folder = await test_create_folder(async_client, auth_headers)
    
    move_data = {
        "item_id": source_folder["id"],
        "target_folder_id": target_folder["id"],
        "item_type": "folder"
    }
    
    response = await async_client.post(
        "/api/v1/storage/move",
        headers=auth_headers,
        json=move_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["parent_id"] == target_folder["id"]

async def test_nested_folder_creation(async_client, auth_headers):
    """Test creating nested folders."""
    # Create parent folder
    parent_folder = await test_create_folder(async_client, auth_headers)
    
    # Create child folder
    child_folder_data = {
        "name": "Child Folder",
        "description": "Child folder description",
        "parent_id": parent_folder["id"]
    }
    
    response = await async_client.post(
        "/api/v1/storage/folders",
        headers=auth_headers,
        json=child_folder_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["parent_id"] == parent_folder["id"]

async def test_folder_validation(async_client, auth_headers):
    """Test folder validation."""
    # Test with invalid folder name
    invalid_folder_data = {
        "name": "",  # Empty name
        "description": "Test description"
    }
    
    response = await async_client.post(
        "/api/v1/storage/folders",
        headers=auth_headers,
        json=invalid_folder_data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_folder_not_found(async_client, auth_headers):
    """Test accessing non-existent folder."""
    non_existent_id = str(UUID(int=0))
    response = await async_client.get(
        f"/api/v1/storage/folders/{non_existent_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_unauthorized_folder_access(async_client):
    """Test unauthorized access to folder endpoints."""
    folder_data = {
        "name": "Test Folder",
        "description": "Test description"
    }
    
    response = await async_client.post(
        "/api/v1/storage/folders",
        json=folder_data
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
