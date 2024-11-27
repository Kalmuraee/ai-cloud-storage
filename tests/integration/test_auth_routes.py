"""
Integration tests for auth routes
"""
import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_register_user(client, test_user_data):
    """Test user registration endpoint."""
    response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert "id" in data
    assert "password" not in data

async def test_login_user(client, test_user, test_user_data):
    """Test user login endpoint."""
    response = await client.post("/api/v1/auth/login", data={
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

async def test_get_current_user(client, test_user, auth_headers):
    """Test get current user endpoint."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == str(test_user.id)

async def test_update_user(client, test_user, auth_headers):
    """Test update user endpoint."""
    update_data = {
        "full_name": "Updated Name",
        "email": test_user.email
    }
    response = await client.put(
        "/api/v1/auth/me",
        headers=auth_headers,
        json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == update_data["full_name"]

async def test_invalid_login(client):
    """Test login with invalid credentials."""
    response = client.post("/api/v1/auth/login", data={
        "username": "invalid@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_protected_route_without_token(client):
    """Test accessing protected route without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_protected_route_with_invalid_token(client):
    """Test accessing protected route with invalid token."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_refresh_token(client, auth_headers):
    """Test token refresh endpoint."""
    response = await client.post(
        "/api/v1/auth/refresh",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
