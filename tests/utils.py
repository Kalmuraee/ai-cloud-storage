"""
Test utilities for AI Cloud Storage system.
Provides helper functions for test file management, authentication, and error handling.
"""
import os
import tempfile
import logging
import contextlib
from typing import List, Optional, Dict, Any, Generator
from pathlib import Path
import httpx
import asyncio
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.exceptions import StorageError

logger = logging.getLogger(__name__)

def create_test_file(size_mb: float, prefix: str = "test", suffix: str = ".txt") -> str:
    """
    Create a test file with specified size in MB.
    
    Args:
        size_mb: Size of the file in megabytes
        prefix: Prefix for the temporary file name
        suffix: Suffix (extension) for the temporary file
        
    Returns:
        str: Path to the created test file
        
    Raises:
        StorageError: If file creation fails
    """
    try:
        with tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, delete=False) as temp_file:
            # Write random bytes to achieve desired file size
            bytes_to_write = int(size_mb * 1024 * 1024)
            temp_file.write(os.urandom(bytes_to_write))
            return temp_file.name
    except Exception as e:
        logger.error(f"Failed to create test file: {str(e)}")
        raise StorageError(f"Failed to create test file: {str(e)}")

def cleanup_test_files(*files: str) -> None:
    """
    Clean up test files safely.
    
    Args:
        *files: Variable number of file paths to clean up
    """
    for file_path in files:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup test file {file_path}: {str(e)}")

@contextlib.contextmanager
def temporary_file(size_mb: float, prefix: str = "test", suffix: str = ".txt") -> Generator[str, None, None]:
    """
    Context manager for temporary test file handling.
    
    Args:
        size_mb: Size of the file in megabytes
        prefix: Prefix for the temporary file name
        suffix: Suffix (extension) for the temporary file
        
    Yields:
        str: Path to the temporary file
    """
    temp_file_path = None
    try:
        temp_file_path = create_test_file(size_mb, prefix, suffix)
        yield temp_file_path
    finally:
        if temp_file_path:
            cleanup_test_files(temp_file_path)

async def check_response_status(
    response: httpx.Response,
    expected_status: int = status.HTTP_200_OK
) -> None:
    """
    Check if response status matches expected status.
    
    Args:
        response: HTTP response to check
        expected_status: Expected HTTP status code
        
    Raises:
        HTTPException: If status code doesn't match expected status
    """
    if response.status_code != expected_status:
        error_detail = response.json().get("detail", "Unknown error")
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Expected status {expected_status}, got {response.status_code}: {error_detail}"
        )

async def upload_test_files(
    client: httpx.AsyncClient,
    file_sizes: List[float],
    token: str,
    concurrent: bool = False
) -> List[Dict[str, Any]]:
    """
    Upload multiple test files, either sequentially or concurrently.
    
    Args:
        client: Async HTTP client
        file_sizes: List of file sizes in MB
        token: Authentication token
        concurrent: If True, upload files concurrently
        
    Returns:
        List[Dict[str, Any]]: List of upload responses
        
    Raises:
        StorageError: If any upload fails
    """
    headers = {"Authorization": f"Bearer {token}"}
    upload_responses = []

    async def upload_single_file(size_mb: float) -> Dict[str, Any]:
        with temporary_file(size_mb) as temp_file:
            files = {"file": open(temp_file, "rb")}
            response = await client.post(
                f"{settings.API_V1_STR}/storage/upload",
                files=files,
                headers=headers
            )
            await check_response_status(response, status.HTTP_201_CREATED)
            return response.json()

    try:
        if concurrent:
            tasks = [upload_single_file(size) for size in file_sizes]
            upload_responses = await asyncio.gather(*tasks)
        else:
            for size in file_sizes:
                response = await upload_single_file(size)
                upload_responses.append(response)
    except Exception as e:
        logger.error(f"Failed to upload test files: {str(e)}")
        raise StorageError(f"Failed to upload test files: {str(e)}")

    return upload_responses

def get_test_file_path(filename: str) -> str:
    """
    Get absolute path to a test file in the test data directory.
    
    Args:
        filename: Name of the test file
        
    Returns:
        str: Absolute path to the test file
    """
    test_data_dir = Path(__file__).parent / "test_data"
    return str(test_data_dir / filename)

async def verify_file_cleanup(file_ids: List[str], client: httpx.AsyncClient, token: str) -> None:
    """
    Verify that files have been properly cleaned up.
    
    Args:
        file_ids: List of file IDs to verify
        client: Async HTTP client
        token: Authentication token
        
    Raises:
        AssertionError: If any file still exists
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    for file_id in file_ids:
        response = await client.get(
            f"{settings.API_V1_STR}/storage/files/{file_id}",
            headers=headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND, f"File {file_id} was not properly cleaned up"
