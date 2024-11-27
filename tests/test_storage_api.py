"""Test suite for storage API endpoints."""

import pytest
import requests
from pathlib import Path
from typing import Dict, Generator

from tests.config import (
    TEST_HOST,
    TEST_USER,
    TEST_USERNAME,
    TEST_PASSWORD,
    SAMPLE_TEXT,
    SAMPLE_IMAGE,
    AUTH_TOKEN,
    STORAGE_UPLOAD,
    STORAGE_DOWNLOAD,
    STORAGE_LIST,
    STORAGE_DUPLICATES,
    STORAGE_METADATA,
)

@pytest.fixture(scope="session")
def test_user() -> None:
    """Create test user if it doesn't exist."""
    response = requests.post(
        f"{TEST_HOST}/api/v1/auth/register",
        json={
            "email": TEST_USER,
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD,
            "full_name": "Test User"
        }
    )
    # Print response content for debugging
    print(f"Register response: {response.status_code} - {response.content}")
    # If user already exists, that's fine
    assert response.status_code in [201, 409]

@pytest.fixture
def auth_token(test_user) -> str:
    """Get authentication token for test user."""
    response = requests.post(
        f"{TEST_HOST}{AUTH_TOKEN}",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    # Print response content for debugging
    print(f"Login response: {response.status_code} - {response.content}")
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token: str) -> Dict[str, str]:
    """Get headers with authentication token."""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def text_file_path(auth_headers: Dict[str, str]) -> str:
    """Get path of uploaded text file."""
    return test_upload_text_file(auth_headers)

def test_upload_text_file(auth_headers: Dict[str, str]):
    """Test uploading a text file."""
    with open(SAMPLE_TEXT, "rb") as f:
        files = {"file": (SAMPLE_TEXT.name, f)}
        response = requests.post(
            f"{TEST_HOST}{STORAGE_UPLOAD}",
            headers=auth_headers,
            files=files,
            data={"check_duplicates": "true", "process_file": "true"}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert "file" in data
    assert data["file"]["filename"] == SAMPLE_TEXT.name
    assert not data["is_duplicate"]
    
    # Store file path for other tests
    return data["file"]["path"]

def test_upload_image_file(auth_headers: Dict[str, str]):
    """Test uploading an image file."""
    with open(SAMPLE_IMAGE, "rb") as f:
        files = {"file": (SAMPLE_IMAGE.name, f)}
        response = requests.post(
            f"{TEST_HOST}{STORAGE_UPLOAD}",
            headers=auth_headers,
            files=files,
            data={"check_duplicates": "true", "process_file": "true"}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert "file" in data
    assert data["file"]["filename"] == SAMPLE_IMAGE.name
    assert not data["is_duplicate"]
    
    # Store file path for other tests
    return data["file"]["path"]

def test_duplicate_upload(auth_headers: Dict[str, str], text_file_path: str):
    """Test uploading a duplicate file."""
    with open(SAMPLE_TEXT, "rb") as f:
        files = {"file": (SAMPLE_TEXT.name, f)}
        response = requests.post(
            f"{TEST_HOST}{STORAGE_UPLOAD}",
            headers=auth_headers,
            files=files,
            data={"check_duplicates": "true", "process_file": "true"}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["is_duplicate"]
    assert data["file"]["path"] == text_file_path

def test_list_files(auth_headers: Dict[str, str]):
    """Test listing files."""
    response = requests.get(
        f"{TEST_HOST}{STORAGE_LIST}",
        headers=auth_headers,
        params={"recursive": "true"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert len(data["files"]) >= 2  # At least our uploaded files
    
    # Verify file attributes
    for file in data["files"]:
        assert "id" in file
        assert "filename" in file
        assert "path" in file
        assert "size" in file
        assert "content_type" in file
        assert "created_at" in file

def test_get_file_metadata(auth_headers: Dict[str, str], text_file_path: str):
    """Test getting file metadata."""
    response = requests.get(
        f"{TEST_HOST}{STORAGE_METADATA}/{text_file_path}/metadata",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == SAMPLE_TEXT.name
    assert data["path"] == text_file_path
    assert "size" in data
    assert "content_type" in data
    assert "created_at" in data
    assert "storage_metadata" in data

def test_download_file(auth_headers: Dict[str, str], text_file_path: str):
    """Test downloading a file."""
    response = requests.get(
        f"{TEST_HOST}{STORAGE_DOWNLOAD}/{text_file_path}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    content = response.content.decode()
    with open(SAMPLE_TEXT, "r") as f:
        original_content = f.read()
    assert content == original_content

def test_get_duplicates(auth_headers: Dict[str, str]):
    """Test getting duplicate files."""
    response = requests.get(
        f"{TEST_HOST}{STORAGE_DUPLICATES}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # We should have at least one group of duplicates
    assert len(data) >= 1
    duplicate_group = data[0]
    assert "content_hash" in duplicate_group
    assert "files" in duplicate_group
    assert len(duplicate_group["files"]) >= 2

def test_delete_file(auth_headers: Dict[str, str], text_file_path: str):
    """Test deleting a file."""
    response = requests.delete(
        f"{TEST_HOST}{STORAGE_DOWNLOAD}/{text_file_path}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify file is deleted
    response = requests.get(
        f"{TEST_HOST}{STORAGE_METADATA}/{text_file_path}/metadata",
        headers=auth_headers
    )
    assert response.status_code == 404

def test_error_cases(auth_headers: Dict[str, str]):
    """Test various error cases."""
    
    # Test uploading empty file
    with open(SAMPLE_TEXT, "rb") as f:
        files = {"file": ("empty.txt", b"")}
        response = requests.post(
            f"{TEST_HOST}{STORAGE_UPLOAD}",
            headers=auth_headers,
            files=files
        )
    assert response.status_code == 400
    
    # Test downloading non-existent file
    response = requests.get(
        f"{TEST_HOST}{STORAGE_DOWNLOAD}/non_existent.txt",
        headers=auth_headers
    )
    assert response.status_code == 404
    
    # Test getting metadata for non-existent file
    response = requests.get(
        f"{TEST_HOST}{STORAGE_METADATA}/non_existent.txt/metadata",
        headers=auth_headers
    )
    assert response.status_code == 404
    
    # Test deleting non-existent file
    response = requests.delete(
        f"{TEST_HOST}{STORAGE_DOWNLOAD}/non_existent.txt",
        headers=auth_headers
    )
    assert response.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
