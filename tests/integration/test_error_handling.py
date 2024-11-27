"""
Integration tests for error handling in the AI Cloud Storage system.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from minio import S3Error
import httpx
from httpx import AsyncClient
import os
from jose import jwt

from app.core.exceptions import (
    StorageError,
    ProcessingError,
    AuthenticationError,
    ValidationError
)
from app.main import app
from app.core.minio import MinioClient
from app.modules.auth.dependencies import get_current_user
from tests.conftest import test_user, test_user_token
from tests.utils import create_test_file, cleanup_test_files

@pytest.mark.asyncio
async def test_minio_connection_failure(
    async_client: AsyncClient,
    test_user_token: str
):
    """Test system behavior when MinIO connection fails."""
    # Create a test file
    test_file = create_test_file(size_mb=1)

    # Mock MinIO client to simulate connection failure
    mock_response = MagicMock()
    mock_response.status = 503
    mock_response.headers = {"x-amz-request-id": "test-request-id"}
    mock_response.getheader.return_value = "test-host-id"

    s3_error = S3Error(
        code="ServiceUnavailable",
        message="Connection failed",
        resource="test-resource",
        request_id="test-request-id",
        host_id="test-host-id",
        response=mock_response
    )

    with patch('app.core.minio.MinioClient.upload_file', side_effect=s3_error):
        with patch('app.modules.auth.dependencies.get_current_user', return_value=test_user):
            try:
                files = {"file": open(test_file, "rb")}
                headers = {"Authorization": f"Bearer {test_user_token}"}

                response = await async_client.post(
                    "/api/v1/storage/upload",
                    files=files,
                    headers=headers
                )

                assert response.status_code == 503
                assert "storage service unavailable" in response.json()["detail"].lower()
            finally:
                cleanup_test_files(test_file)

@pytest.mark.asyncio
async def test_database_connection_failure(
    async_client: AsyncClient,
    test_user_token: str
):
    """Test system behavior when database connection fails."""
    with patch('app.modules.auth.dependencies.get_current_user', return_value=test_user):
        with patch('app.core.database.get_db', side_effect=SQLAlchemyError("Database connection failed")):
            headers = {"Authorization": f"Bearer {test_user_token}"}
            response = await async_client.get(
                "/api/v1/storage/list",
                headers=headers
            )

            assert response.status_code == 503
            assert "database error" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_ai_model_timeout(
    async_client: AsyncClient,
    test_user_token: str
):
    """Test system behavior when AI model processing times out."""
    with patch('app.modules.auth.dependencies.get_current_user', return_value=test_user):
        with patch('app.modules.ai_processor.service.AIProcessorService.process_file') as mock_process:
            mock_process.side_effect = ProcessingError("Model processing timed out")

            headers = {"Authorization": f"Bearer {test_user_token}"}
            response = await async_client.post(
                "/api/v1/ai/process",
                json={"file_id": 1},
                headers=headers
            )

            assert response.status_code == 503
            assert "processing timed out" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_invalid_file_upload(
    async_client: AsyncClient,
    test_user_token: str
):
    """Test system behavior with invalid file uploads."""
    with patch('app.modules.auth.dependencies.get_current_user', return_value=test_user):
        # Test empty file
        empty_file = create_test_file(size_mb=0)
        
        try:
            files = {"file": open(empty_file, "rb")}
            headers = {"Authorization": f"Bearer {test_user_token}"}

            response = await async_client.post(
                "/api/v1/storage/upload",
                files=files,
                headers=headers
            )

            assert response.status_code == 400
            assert "invalid file" in response.json()["detail"].lower()
        finally:
            cleanup_test_files(empty_file)

@pytest.mark.asyncio
async def test_concurrent_folder_operations(
    async_client: AsyncClient,
    test_user_token: str
):
    """Test concurrent folder operations for race conditions."""
    with patch('app.modules.auth.dependencies.get_current_user', return_value=test_user):
        # Create a test folder
        headers = {"Authorization": f"Bearer {test_user_token}"}
        folder_name = "test_folder"

        # Create folder
        response = await async_client.post(
            "/api/v1/storage/folders/create",  
            json={"name": folder_name},
            headers=headers
        )
        assert response.status_code == 201

        # Try to create folder with same name
        response = await async_client.post(
            "/api/v1/storage/folders/create",
            json={"name": folder_name},
            headers=headers
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_invalid_ai_processing_params(
    async_client: AsyncClient,
    test_user_token: str
):
    """Test AI processing with invalid parameters."""
    with patch('app.modules.auth.dependencies.get_current_user', return_value=test_user):
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Test with non-existent file
        response = await async_client.post(
            "/api/v1/ai/process",
            json={"file_id": 9999},
            headers=headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        # Test with invalid model parameters
        response = await async_client.post(
            "/api/v1/ai/process",
            json={
                "file_id": 1,
                "model_params": {"invalid_param": "value"}
            },
            headers=headers
        )
        assert response.status_code == 400
        assert "invalid parameters" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_unauthorized_folder_access(
    async_client: AsyncClient
):
    """Test unauthorized access to folder operations."""
    # Try to create folder without auth
    response = await async_client.post(
        "/api/v1/storage/folders/create",
        json={"name": "test_folder"}
    )
    assert response.status_code == 401
    assert "not authenticated" in response.json()["detail"].lower()

    # Try with invalid token
    response = await async_client.post(
        "/api/v1/storage/folders/create",
        json={"name": "test_folder"},
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "invalid token" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_token_expiration(
    async_client: AsyncClient,
    test_user_token: str
):
    """Test system behavior with expired tokens."""
    # Mock token verification to simulate expiration
    with patch('app.modules.auth.dependencies.get_current_user') as mock_verify:
        mock_verify.side_effect = jwt.ExpiredSignatureError("Token has expired")
        
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = await async_client.get(
            "/api/v1/storage/list",
            headers=headers
        )
        
        assert response.status_code == 401
        assert "could not validate credentials" in response.json()["detail"].lower()
