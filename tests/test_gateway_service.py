"""Tests for the gateway service."""
import pytest
from httpx import AsyncClient
import time

pytestmark = pytest.mark.asyncio

async def test_gateway_health_check(gateway_client: AsyncClient):
    """Test gateway health check endpoint."""
    response = await gateway_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    
    # Check service statuses
    services = data["services"]
    expected_services = ["auth", "storage", "ai", "search"]
    for service in expected_services:
        assert service in services
        assert "status" in services[service]

async def test_rate_limiting(gateway_client: AsyncClient, test_user_token: str):
    """Test rate limiting functionality."""
    # Make multiple requests in quick succession
    requests = 150  # More than our limit
    responses = []
    
    for _ in range(requests):
        response = await gateway_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        responses.append(response.status_code)
        if response.status_code == 429:  # Too Many Requests
            break
    
    # Verify that rate limiting kicked in
    assert 429 in responses, "Rate limiting should trigger after too many requests"

async def test_service_routing(gateway_client: AsyncClient, test_user_token: str):
    """Test routing requests to different services."""
    # Test auth service routing
    auth_response = await gateway_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert auth_response.status_code == 200
    
    # Test storage service routing
    storage_response = await gateway_client.get(
        "/api/storage/buckets",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert storage_response.status_code in [200, 404]  # 404 if no buckets exist
    
    # Test invalid service routing
    invalid_response = await gateway_client.get(
        "/api/invalid_service/endpoint",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert invalid_response.status_code == 404

async def test_authentication_middleware(gateway_client: AsyncClient):
    """Test authentication middleware for protected routes."""
    # Test without token
    no_token_response = await gateway_client.get("/api/storage/buckets")
    assert no_token_response.status_code == 401
    
    # Test with invalid token
    invalid_token_response = await gateway_client.get(
        "/api/storage/buckets",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert invalid_token_response.status_code == 401
    
    # Test with malformed authorization header
    malformed_auth_response = await gateway_client.get(
        "/api/storage/buckets",
        headers={"Authorization": "Invalid Format"}
    )
    assert malformed_auth_response.status_code == 401

async def test_cors_headers(gateway_client: AsyncClient):
    """Test CORS headers in responses."""
    response = await gateway_client.options(
        "/api/auth/login",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers

async def test_request_timeout(gateway_client: AsyncClient, test_user_token: str):
    """Test request timeout handling."""
    # Simulate a slow endpoint
    response = await gateway_client.get(
        "/api/storage/large_file",
        headers={"Authorization": f"Bearer {test_user_token}"},
        timeout=1.0
    )
    assert response.status_code in [404, 408, 503]  # 404 if endpoint doesn't exist

async def test_error_handling(gateway_client: AsyncClient, test_user_token: str):
    """Test error handling for various scenarios."""
    # Test 404 handling
    not_found = await gateway_client.get(
        "/api/auth/nonexistent",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert not_found.status_code == 404
    
    # Test method not allowed
    method_not_allowed = await gateway_client.put(
        "/api/auth/login",  # Login only accepts POST
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={}
    )
    assert method_not_allowed.status_code == 405

async def test_public_routes(gateway_client: AsyncClient):
    """Test access to public routes."""
    public_routes = [
        "/api/auth/login",
        "/api/auth/register",
        "/health"
    ]
    
    for route in public_routes:
        response = await gateway_client.get(route)
        assert response.status_code != 401, f"Route {route} should be public"

async def test_service_unavailable(gateway_client: AsyncClient, test_user_token: str):
    """Test handling of unavailable services."""
    # Assuming the search service is not running
    response = await gateway_client.get(
        "/api/search/query",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code in [404, 503]  # Either not found or service unavailable
