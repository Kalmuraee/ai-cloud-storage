"""Tests for auth security utilities."""
import pytest
from datetime import datetime, timedelta
import jwt
from typing import Dict, Any

from app.modules.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)
from app.core.config import settings

def test_password_hashing_and_verification():
    """Test password hashing and verification functionality."""
    # Test successful password verification
    password = "test_password123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    
    # Test failed password verification
    assert not verify_password("wrong_password", hashed)
    assert not verify_password(password + "extra", hashed)
    
    # Test hash uniqueness
    hashed2 = get_password_hash(password)
    assert hashed != hashed2  # Each hash should be unique due to salt

def test_access_token_creation():
    """Test JWT access token creation."""
    # Test token creation with default expiration
    data = {"sub": "test@example.com", "role": "user"}
    token = create_access_token(data)
    
    # Decode and verify token
    payload = decode_access_token(token)
    assert payload["sub"] == data["sub"]
    assert payload["role"] == data["role"]
    assert "exp" in payload
    
    # Verify expiration is set correctly
    exp_time = datetime.utcfromtimestamp(payload["exp"])
    now = datetime.utcnow()
    expected_exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    assert abs((exp_time - expected_exp).total_seconds()) < 5

def test_access_token_with_custom_expiration():
    """Test JWT access token creation with custom expiration."""
    data = {"sub": "test@example.com"}
    custom_expire = timedelta(hours=2)
    token = create_access_token(data, expires_delta=custom_expire)
    
    # Decode and verify token
    payload = decode_access_token(token)
    assert payload["sub"] == data["sub"]
    
    # Verify custom expiration is set correctly
    exp_time = datetime.utcfromtimestamp(payload["exp"])
    now = datetime.utcnow()
    assert abs((exp_time - now - custom_expire).total_seconds()) < 5

def test_token_decoding_errors():
    """Test error cases for token decoding."""
    # Test invalid token format
    with pytest.raises(ValueError) as exc_info:
        decode_access_token("invalid_token")
    assert "Invalid token" in str(exc_info.value)
    
    # Test expired token
    data = {"sub": "test@example.com"}
    expired_delta = timedelta(seconds=-1)
    expired_token = create_access_token(data, expires_delta=expired_delta)
    with pytest.raises(ValueError) as exc_info:
        decode_access_token(expired_token)
    assert "Invalid token" in str(exc_info.value)
    
    # Test token with invalid signature
    valid_token = create_access_token(data)
    tampered_token = valid_token[:-5] + "12345"
    with pytest.raises(ValueError) as exc_info:
        decode_access_token(tampered_token)
    assert "Invalid token" in str(exc_info.value)

def test_token_data_integrity():
    """Test that token preserves all data fields."""
    test_data: Dict[str, Any] = {
        "sub": "test@example.com",
        "role": "admin",
        "permissions": ["read", "write"],
        "user_id": 123,
        "is_active": True,
        "metadata": {
            "last_login": "2024-01-01",
            "created_at": "2023-01-01"
        }
    }
    
    token = create_access_token(test_data)
    decoded = decode_access_token(token)
    
    # Remove expiration from comparison since it's added during token creation
    del decoded["exp"]
    
    # Verify all original data is preserved
    assert decoded == test_data
