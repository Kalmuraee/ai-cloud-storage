"""
Test auth service
"""
import pytest
from datetime import timedelta
from unittest.mock import Mock
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.service import AuthService
from app.modules.auth.models import User, Token

@pytest.fixture
def auth_service():
    return AuthService()

@pytest.fixture
def mock_db():
    db = Mock(spec=AsyncSession)
    db.commit = Mock()
    db.refresh = Mock()
    return db

@pytest.fixture
def test_user():
    return User(
        id="test-user-id",
        email="test@example.com",
        hashed_password="hashed_password"
    )

@pytest.mark.asyncio
async def test_verify_password(auth_service):
    # Test with correct password
    hashed = auth_service.get_password_hash("testpass123")
    assert auth_service.verify_password("testpass123", hashed)
    
    # Test with incorrect password
    assert not auth_service.verify_password("wrongpass", hashed)

@pytest.mark.asyncio
async def test_authenticate_user(auth_service, mock_db, test_user):
    # Mock database query
    mock_db.execute = Mock()
    mock_db.execute.return_value.scalar_one_or_none = Mock(return_value=test_user)
    
    # Test with correct password
    test_user.hashed_password = auth_service.get_password_hash("testpass123")
    user = await auth_service.authenticate_user(
        email="test@example.com",
        password="testpass123",
        db=mock_db
    )
    assert user is not None
    assert user.email == "test@example.com"
    
    # Test with incorrect password
    user = await auth_service.authenticate_user(
        email="test@example.com",
        password="wrongpass",
        db=mock_db
    )
    assert user is None

@pytest.mark.asyncio
async def test_create_access_token(auth_service):
    # Create token
    token = auth_service.create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(minutes=15)
    )
    assert token is not None
    
    # Verify token can be decoded
    payload = auth_service.decode_token(token)
    assert payload["sub"] == "test@example.com"

@pytest.mark.asyncio
async def test_get_current_user(auth_service, mock_db, test_user):
    # Create token
    token = auth_service.create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # Mock database query
    mock_db.execute = Mock()
    mock_db.execute.return_value.scalar_one_or_none = Mock(return_value=test_user)
    
    # Get current user
    user = await auth_service.get_current_user(token, mock_db)
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email

@pytest.mark.asyncio
async def test_create_user(auth_service, mock_db):
    # Mock database query for duplicate check
    mock_db.execute = Mock()
    mock_db.execute.return_value.scalar_one_or_none = Mock(return_value=None)
    
    # Create user
    user = await auth_service.create_user(
        email="new@example.com",
        password="testpass123",
        db=mock_db
    )
    
    assert user is not None
    assert user.email == "new@example.com"
    assert auth_service.verify_password("testpass123", user.hashed_password)
