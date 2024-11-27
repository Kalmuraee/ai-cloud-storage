"""Performance tests for AI Cloud Storage system."""
import pytest
import asyncio
import time
from typing import List
import httpx
from fastapi import status

from app.core.config import settings
from tests.utils import (
    create_test_file,
    cleanup_test_files,
    upload_test_files,
    check_response_status
)

@pytest.mark.asyncio
async def test_concurrent_file_uploads(
    async_client: httpx.AsyncClient,
    test_user_token: str
):
    """Test concurrent file upload performance."""
    file_sizes = [1.0, 2.0, 5.0]  # MB
    
    start_time = time.time()
    responses = await upload_test_files(
        async_client,
        file_sizes,
        test_user_token,
        concurrent=True
    )
    end_time = time.time()
    
    assert len(responses) == len(file_sizes)
    total_time = end_time - start_time
    avg_time = total_time / len(file_sizes)
    
    # Log performance metrics
    print(f"\nConcurrent upload performance:")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per file: {avg_time:.2f}s")
    
    # Verify all uploads were successful
    for response in responses:
        assert "file_id" in response

@pytest.mark.asyncio
async def test_large_file_upload_performance(
    async_client: httpx.AsyncClient,
    test_user_token: str
):
    """Test large file upload performance."""
    file_size = 50.0  # MB
    
    start_time = time.time()
    responses = await upload_test_files(
        async_client,
        [file_size],
        test_user_token
    )
    end_time = time.time()
    
    assert len(responses) == 1
    upload_time = end_time - start_time
    upload_speed = file_size / upload_time  # MB/s
    
    # Log performance metrics
    print(f"\nLarge file upload performance:")
    print(f"File size: {file_size}MB")
    print(f"Upload time: {upload_time:.2f}s")
    print(f"Upload speed: {upload_speed:.2f}MB/s")
    
    # Verify upload was successful
    assert "file_id" in responses[0]

@pytest.mark.asyncio
async def test_api_response_times(
    async_client: httpx.AsyncClient,
    test_user_token: str
):
    """Test API endpoint response times."""
    endpoints = [
        "/api/v1/storage/list",
        "/api/v1/storage/stats",
        "/api/v1/ai/models"
    ]
    
    print("\nAPI Response Times:")
    for endpoint in endpoints:
        start_time = time.time()
        response = await async_client.get(
            endpoint,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        end_time = time.time()
        
        await check_response_status(response)
        response_time = end_time - start_time
        print(f"{endpoint}: {response_time:.3f}s")
        
        # Basic performance assertions
        assert response_time < 1.0, f"Response time for {endpoint} exceeded 1 second"

@pytest.mark.asyncio
async def test_search_performance(
    async_client: httpx.AsyncClient,
    test_user_token: str
):
    """Test search functionality performance."""
    # Upload test files for searching
    file_sizes = [1.0] * 5  # 5 files of 1MB each
    responses = await upload_test_files(
        async_client,
        file_sizes,
        test_user_token,
        concurrent=True
    )
    
    # Perform search operations
    search_terms = ["test", "document", "file", "data"]
    print("\nSearch Performance:")
    
    for term in search_terms:
        start_time = time.time()
        response = await async_client.get(
            f"/api/v1/storage/search?query={term}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        end_time = time.time()
        
        await check_response_status(response)
        search_time = end_time - start_time
        results = response.json()
        
        print(f"Search term '{term}':")
        print(f"  Time: {search_time:.3f}s")
        print(f"  Results: {len(results)}")
        
        # Performance assertions
        assert search_time < 2.0  # Search should complete within 2 seconds
        assert isinstance(results, list)
