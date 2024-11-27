"""
Integration tests for chat interface routes
"""
import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_create_chat_session(client, auth_headers):
    """Test creating a new chat session."""
    session_data = {
        "name": "Test Chat Session",
        "description": "Test chat session for file interactions",
        "context": {
            "file_ids": [],
            "folder_ids": []
        }
    }
    
    response = await client.post(
        "/api/v1/ai/chat/sessions",
        headers=auth_headers,
        json=session_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == session_data["name"]
    assert data["description"] == session_data["description"]
    assert "id" in data
    assert "created_at" in data
    return data

async def test_send_message(client, auth_headers):
    """Test sending a message in a chat session."""
    # Create a session first
    session = await test_create_chat_session(client, auth_headers)
    
    message_data = {
        "content": "What files do I have in my storage?",
        "type": "text"
    }
    
    response = await client.post(
        f"/api/v1/ai/chat/sessions/{session['id']}/messages",
        headers=auth_headers,
        json=message_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert "content" in data
    assert "created_at" in data
    assert data["session_id"] == session["id"]
    assert data["type"] == "text"
    return data

async def test_get_chat_history(client, auth_headers):
    """Test retrieving chat session history."""
    # Create a session and send a message
    session = await test_create_chat_session(client, auth_headers)
    message = await test_send_message(client, auth_headers)
    
    response = await client.get(
        f"/api/v1/ai/chat/sessions/{session['id']}/history",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(msg["id"] == message["id"] for msg in data)

async def test_send_file_context_message(client, auth_headers, test_file):
    """Test sending a message with file context."""
    session = await test_create_chat_session(client, auth_headers)
    
    message_data = {
        "content": "What is the content of this file?",
        "type": "text",
        "context": {
            "file_ids": [str(test_file.id)],
            "folder_ids": []
        }
    }
    
    response = await client.post(
        f"/api/v1/ai/chat/sessions/{session['id']}/messages",
        headers=auth_headers,
        json=message_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "context" in data
    assert str(test_file.id) in data["context"]["file_ids"]

async def test_invalid_session_id(client, auth_headers):
    """Test sending message to invalid session."""
    message_data = {
        "content": "Test message",
        "type": "text"
    }
    
    response = await client.post(
        "/api/v1/ai/chat/sessions/invalid-id/messages",
        headers=auth_headers,
        json=message_data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_empty_message(client, auth_headers):
    """Test sending empty message."""
    session = await test_create_chat_session(client, auth_headers)
    
    message_data = {
        "content": "",
        "type": "text"
    }
    
    response = await client.post(
        f"/api/v1/ai/chat/sessions/{session['id']}/messages",
        headers=auth_headers,
        json=message_data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_unauthorized_chat_access(client):
    """Test unauthorized access to chat endpoints."""
    session_data = {
        "name": "Test Session",
        "description": "Test description"
    }
    
    response = await client.post(
        "/api/v1/ai/chat/sessions",
        json=session_data
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_session_not_found(client, auth_headers):
    """Test accessing non-existent chat session."""
    response = await client.get(
        "/api/v1/ai/chat/sessions/non-existent-id/history",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_invalid_message_type(client, auth_headers):
    """Test sending message with invalid type."""
    session = await test_create_chat_session(client, auth_headers)
    
    message_data = {
        "content": "Test message",
        "type": "invalid_type"
    }
    
    response = await client.post(
        f"/api/v1/ai/chat/sessions/{session['id']}/messages",
        headers=auth_headers,
        json=message_data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
