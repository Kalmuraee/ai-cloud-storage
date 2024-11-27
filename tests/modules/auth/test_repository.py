"""Tests for authentication repository."""
import pytest
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError, NotFoundException, ValidationError
from app.modules.auth.models import User, Role, Token
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import UserCreate, UserUpdate, RoleCreate, TokenCreate

@pytest_asyncio.fixture
async def auth_repo(db: AsyncSession) -> AsyncGenerator[AuthRepository, None]:
    """Fixture for auth repository."""
    yield AuthRepository(db)

@pytest.mark.asyncio
async def test_user_creation(auth_repo: AuthRepository):
    """Test user creation."""
    user_data = UserCreate(
        email="test2@example.com",  # Changed to avoid conflict
        username="testuser2",       # Changed to avoid conflict
        password="TestPass123",     # Not used directly
        full_name="Test User 2",    # Changed to avoid conflict
        is_active=True,
        is_superuser=False
    )
    
    # Create user
    user = await auth_repo.create_user(user_data, "hashed_password")
    assert user.email == user_data.email
    assert user.username == user_data.username
    assert user.hashed_password == "hashed_password"
    assert user.full_name == user_data.full_name
    assert user.is_active == user_data.is_active
    assert user.is_superuser == user_data.is_superuser
    assert len(user.roles) == 0

@pytest.mark.asyncio
async def test_get_user_methods(auth_repo: AuthRepository):
    """Test methods for retrieving users."""
    # Create a test user first
    user_data = UserCreate(
        email="find@example.com",
        username="finduser",
        password="TestPass123",
        full_name="Find User"
    )
    created_user = await auth_repo.create_user(user_data, "hashed_password")
    
    # Test get by ID
    user = await auth_repo.get_user_by_id(created_user.id)
    assert user is not None
    assert user.id == created_user.id
    
    # Test get by email
    user = await auth_repo.get_user_by_email(user_data.email)
    assert user is not None
    assert user.email == user_data.email
    
    # Test get by username
    user = await auth_repo.get_user_by_username(user_data.username)
    assert user is not None
    assert user.username == user_data.username
    
    # Test get non-existent user
    with pytest.raises(NotFoundException):
        await auth_repo.get_user_by_id(9999)
    with pytest.raises(NotFoundException):
        await auth_repo.get_user_by_email("nonexistent@example.com")
    with pytest.raises(NotFoundException):
        await auth_repo.get_user_by_username("nonexistent")

@pytest.mark.asyncio
async def test_user_update(auth_repo: AuthRepository):
    """Test user update functionality."""
    # Create a test user first
    user_data = UserCreate(
        email="update@example.com",
        username="updateuser",
        password="TestPass123",
        full_name="Update User"
    )
    user = await auth_repo.create_user(user_data, "hashed_password")
    
    # Update user
    update_data = UserUpdate(
        full_name="Updated Name",
        is_active=False
    )
    updated_user = await auth_repo.update_user(user.id, update_data)
    
    assert updated_user.full_name == "Updated Name"
    assert updated_user.is_active is False
    assert updated_user.email == user_data.email  # Unchanged
    
    # Test updating non-existent user
    with pytest.raises(NotFoundException):
        await auth_repo.update_user(9999, update_data)

@pytest.mark.asyncio
async def test_token_operations(auth_repo: AuthRepository):
    """Test token creation, validation, and revocation."""
    # Create a test user first
    user_data = UserCreate(
        email="token@example.com",
        username="tokenuser",
        password="TestPass123",
        full_name="Token User"
    )
    user = await auth_repo.create_user(user_data, "hashed_password")
    
    # Create token
    token_data = TokenCreate(
        token="test_token_123_very_long_token_that_meets_min_length",  # At least 32 chars
        token_type="bearer",
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    token = await auth_repo.create_token(token_data)
    
    assert token.token == token_data.token
    assert token.user_id == user.id
    assert not token.is_revoked
    
    # Validate token
    valid_token = await auth_repo.get_valid_token(token_data.token)
    assert valid_token is not None
    assert valid_token.token == token_data.token
    
    # Revoke token
    await auth_repo.revoke_token(token_data.token)
    valid_token = await auth_repo.get_valid_token(token_data.token)
    assert valid_token is None
    
    # Test expired token
    expired_token_data = TokenCreate(
        token="expired_token_123_very_long_token_that_meets_min_length",  # At least 32 chars
        token_type="bearer",
        user_id=user.id,
        expires_at=datetime.utcnow() - timedelta(minutes=1)
    )
    await auth_repo.create_token(expired_token_data)
    valid_token = await auth_repo.get_valid_token(expired_token_data.token)
    assert valid_token is None

@pytest.mark.asyncio
async def test_role_operations(auth_repo: AuthRepository):
    """Test role creation, retrieval, and assignment."""
    # Create a test user first
    user_data = UserCreate(
        email="role@example.com",
        username="roleuser",
        password="TestPass123",
        full_name="Role User"
    )
    user = await auth_repo.create_user(user_data, "hashed_password")
    
    # Create role
    role_data = RoleCreate(
        name="test_role",
        description="Test role",
        permissions=["read", "write"]
    )
    role = await auth_repo.create_role(role_data)
    
    assert role.name == role_data.name
    assert role.description == role_data.description
    assert role.permissions == '["read", "write"]'  # Stored as JSON string
    
    # Get role by name
    found_role = await auth_repo.get_role_by_name(role_data.name)
    assert found_role is not None
    assert found_role.id == role.id
    
    # Assign role to user
    await auth_repo.assign_role_to_user(user.id, role.id)
    
    # Verify role assignment
    updated_user = await auth_repo.get_user_by_id(user.id)
    assert updated_user is not None
    assert len(updated_user.roles) == 1
    assert updated_user.roles[0].id == role.id
    
    # Test assigning role to non-existent user
    with pytest.raises(NotFoundException):
        await auth_repo.assign_role_to_user(9999, role.id)
    
    # Test getting non-existent role
    nonexistent_role = await auth_repo.get_role_by_name("nonexistent")
    assert nonexistent_role is None

@pytest.mark.asyncio
async def test_database_error_handling(auth_repo: AuthRepository):
    """Test database error handling."""
    # Test with duplicate email
    user_data = UserCreate(
        email="test@example.com",  # Already exists from test_user fixture
        username="testuser123",
        password="TestPass123",
        full_name="Test User"
    )
    with pytest.raises(DatabaseError):
        await auth_repo.create_user(user_data, "hashed_password")

    # Test invalid token creation
    invalid_token = TokenCreate(
        token="a" * 32,  # Valid length but will fail in repository
        token_type="access",
        expires_at=datetime.utcnow(),
        user_id=999  # Non-existent user
    )
    with pytest.raises(DatabaseError):
        await auth_repo.create_token(invalid_token)

    # Test getting non-existent user
    with pytest.raises(NotFoundException):
        await auth_repo.get_user_by_id(999)  # Non-existent ID
