"""
Integration tests for AI processor routes
"""
import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_process_file(client, auth_headers, test_file):
    """Test file processing endpoint."""
    process_data = {
        "file_id": str(test_file.id),
        "task_type": "text_classification",
        "options": {
            "model": "bert-base-uncased",
            "labels": ["positive", "negative", "neutral"]
        }
    }
    
    response = await client.post(
        "/api/v1/ai/process",
        headers=auth_headers,
        json=process_data
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"

async def test_get_processing_status(client, auth_headers, test_processing_task):
    """Test get processing status endpoint."""
    response = await client.get(
        f"/api/v1/ai/status/{test_processing_task.id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_processing_task.id)
    assert data["status"] == test_processing_task.status
    assert data["file_id"] == str(test_processing_task.file_id)

async def test_get_processing_result(client, auth_headers, test_processing_task):
    """Test get processing result endpoint."""
    # Update task status to completed
    test_processing_task.status = "completed"
    test_processing_task.result = {
        "classification": "positive",
        "confidence": 0.95
    }
    
    response = await client.get(
        f"/api/v1/ai/result/{test_processing_task.id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["task_id"] == str(test_processing_task.id)
    assert "result" in data
    assert data["result"]["classification"] == "positive"

async def test_list_processing_tasks(client, auth_headers, test_processing_task):
    """Test list processing tasks endpoint."""
    response = await client.get(
        "/api/v1/ai/tasks",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(task["id"] == str(test_processing_task.id) for task in data)

async def test_cancel_processing_task(client, auth_headers, test_processing_task):
    """Test cancel processing task endpoint."""
    response = await client.post(
        f"/api/v1/ai/cancel/{test_processing_task.id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_processing_task.id)
    assert data["status"] == "cancelled"

async def test_retry_failed_task(client, auth_headers, test_processing_task):
    """Test retry failed task endpoint."""
    # Set task status to failed
    test_processing_task.status = "failed"
    
    response = await client.post(
        f"/api/v1/ai/retry/{test_processing_task.id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["id"] == str(test_processing_task.id)
    assert data["status"] == "pending"

async def test_get_supported_models(client, auth_headers):
    """Test get supported models endpoint."""
    response = await client.get(
        "/api/v1/ai/models",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(isinstance(model, dict) for model in data)
    assert all("name" in model and "task_types" in model for model in data)

async def test_unauthorized_access(client, test_processing_task):
    """Test unauthorized access to AI processor endpoints."""
    endpoints = [
        ("POST", "/api/v1/ai/process"),
        ("GET", f"/api/v1/ai/status/{test_processing_task.id}"),
        ("GET", f"/api/v1/ai/result/{test_processing_task.id}"),
        ("GET", "/api/v1/ai/tasks"),
        ("POST", f"/api/v1/ai/cancel/{test_processing_task.id}"),
        ("POST", f"/api/v1/ai/retry/{test_processing_task.id}"),
        ("GET", "/api/v1/ai/models")
    ]
    
    for method, endpoint in endpoints:
        response = await client.request(method, endpoint)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_invalid_task_id(client, auth_headers):
    """Test accessing endpoints with invalid task ID."""
    invalid_id = "00000000-0000-0000-0000-000000000000"
    endpoints = [
        f"/api/v1/ai/status/{invalid_id}",
        f"/api/v1/ai/result/{invalid_id}",
        f"/api/v1/ai/cancel/{invalid_id}",
        f"/api/v1/ai/retry/{invalid_id}"
    ]
    
    for endpoint in endpoints:
        response = await client.get(
            endpoint,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
