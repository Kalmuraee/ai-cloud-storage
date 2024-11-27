"""
Test suite for live API endpoints
"""
import pytest
import httpx
import os
import json
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test data
TEST_USER = {
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Test User",
    "username": "testuser"
}

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    # First try to register the user
    with httpx.Client(base_url=BASE_URL) as client:
        try:
            register_response = client.post(f"{API_PREFIX}/auth/register", json=TEST_USER)
            print(f"Register response: {register_response.status_code}")
            print(f"Register content: {register_response.text}")
        except httpx.HTTPError as e:
            print(f"Register error: {str(e)}")
            pass  # User might already exist

        # Login to get token
        login_response = client.post(
            f"{API_PREFIX}/auth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "username": TEST_USER["email"],  # Use email for login
                "password": TEST_USER["password"],
                "grant_type": "password"
            }
        )
        print(f"Login response: {login_response.status_code}")
        print(f"Login content: {login_response.text}")

        assert login_response.status_code == 200
        return login_response.json()["access_token"]

def test_health_check():
    """Test health check endpoint"""
    with httpx.Client(base_url=BASE_URL) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

def test_auth_endpoints(auth_token):
    """Test authentication endpoints"""
    with httpx.Client(base_url=BASE_URL) as client:
        # Test registration with new user
        new_user = {
            "email": "newuser@example.com",
            "password": "NewUser123!@#",
            "username": "newuser",
            "full_name": "New User"
        }
        response = client.post(f"{API_PREFIX}/auth/register", json=new_user)
        assert response.status_code in [200, 400]  # 400 if user exists

        # Test login with new user
        response = client.post(
            f"{API_PREFIX}/auth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "username": new_user["email"],
                "password": new_user["password"],
                "grant_type": "password"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

        # Test get current user info
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get(f"{API_PREFIX}/auth/me", headers=headers)
        assert response.status_code == 200
        assert "email" in response.json()

def test_storage_operations(auth_token):
    """Test storage operations"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    with httpx.Client(base_url=BASE_URL) as client:
        # Test file upload
        files = {
            "file": ("test.txt", b"Hello, World!", "text/plain")
        }
        response = client.post(
            f"{API_PREFIX}/storage/upload",
            headers=headers,
            files=files
        )
        assert response.status_code == 200
        file_id = response.json()["id"]

        # Test file download
        response = client.get(
            f"{API_PREFIX}/storage/download/{file_id}",
            headers=headers
        )
        assert response.status_code == 200
        assert response.content == b"Hello, World!"

        # Test file deletion
        response = client.delete(
            f"{API_PREFIX}/storage/delete/{file_id}",
            headers=headers
        )
        assert response.status_code == 200

def test_folder_operations(auth_token):
    """Test folder operations"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    with httpx.Client(base_url=BASE_URL) as client:
        # Test folder creation
        folder_data = {"name": "test_folder"}
        response = client.post(
            f"{API_PREFIX}/storage/folder",
            headers=headers,
            json=folder_data
        )
        assert response.status_code == 200
        folder_id = response.json()["id"]

        # Test folder listing
        response = client.get(
            f"{API_PREFIX}/storage/folder/{folder_id}",
            headers=headers
        )
        assert response.status_code == 200

        # Test folder deletion
        response = client.delete(
            f"{API_PREFIX}/storage/folder/{folder_id}",
            headers=headers
        )
        assert response.status_code == 200

def test_error_cases(auth_token):
    """Test error cases"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    with httpx.Client(base_url=BASE_URL) as client:
        # Test invalid file upload
        response = client.post(
            f"{API_PREFIX}/storage/upload",
            headers=headers
        )
        assert response.status_code == 422  # Validation error

        # Test invalid folder creation
        response = client.post(
            f"{API_PREFIX}/storage/folder",
            headers=headers,
            json={}
        )
        assert response.status_code == 422  # Validation error

        # Test invalid file download
        response = client.get(
            f"{API_PREFIX}/storage/download/999999",
            headers=headers
        )
        assert response.status_code == 404  # Not found

        # Test invalid folder access
        response = client.get(
            f"{API_PREFIX}/storage/folder/999999",
            headers=headers
        )
        assert response.status_code == 404  # Not found

if __name__ == "__main__":
    pytest.main(["-v", __file__])
