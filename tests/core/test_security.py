"""
Tests for security utilities.
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.config import settings
from app.core.exceptions import TokenError

def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)

def test_access_token_creation():
    """Test JWT access token creation and validation."""
    user_id = "test_user"
    token = create_access_token(user_id)
    
    # Decode and verify token
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    
    # Test with custom expiration
    custom_expire = timedelta(hours=2)
    token = create_access_token(user_id, expires_delta=custom_expire)
    payload = decode_token(token)
    
    # Verify expiration is approximately 2 hours from now
    exp_time = datetime.utcfromtimestamp(payload["exp"])
    now = datetime.utcnow()
    assert abs((exp_time - now - custom_expire).total_seconds()) < 5

def test_refresh_token_creation():
    """Test JWT refresh token creation and validation."""
    user_id = "test_user"
    token = create_refresh_token(user_id)
    
    # Decode and verify token
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    
    # Test with custom expiration
    custom_expire = timedelta(days=7)
    token = create_refresh_token(user_id, expires_delta=custom_expire)
    payload = decode_token(token)
    
    # Verify expiration is approximately 7 days from now
    exp_time = datetime.utcfromtimestamp(payload["exp"])
    now = datetime.utcnow()
    assert abs((exp_time - now - custom_expire).total_seconds()) < 5

def test_token_validation_errors():
    """Test token validation error cases."""
    # Test invalid token format
    with pytest.raises(TokenError):
        decode_token("invalid_token")
    
    # Test expired token
    user_id = "test_user"
    expired_delta = timedelta(seconds=-1)
    expired_token = create_access_token(user_id, expires_delta=expired_delta)
    with pytest.raises(TokenError):
        decode_token(expired_token)
    
    # Test token with invalid signature
    valid_token = create_access_token(user_id)
    tampered_token = valid_token[:-5] + "12345"  # Tamper with signature
    with pytest.raises(TokenError):
        decode_token(tampered_token)
