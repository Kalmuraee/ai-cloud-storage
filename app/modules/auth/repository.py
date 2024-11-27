"""
Authentication module repository
"""
from datetime import datetime
from typing import Optional, List, Union
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import json

from app.core.exceptions import NotFoundException, DatabaseError
from app.modules.auth.models import User, Role, Token
from app.modules.auth.schemas import UserCreate, UserUpdate, RoleCreate, TokenCreate

class AuthRepository:
    """Repository for authentication-related database operations"""
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with roles loaded"""
        try:
            query = select(User).options(selectinload(User.roles)).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            if user is None:
                raise NotFoundException(f"User with ID {user_id} not found")
            return user
        except NotFoundException as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error fetching user by ID: {str(e)}")

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email with roles loaded"""
        try:
            query = select(User).options(selectinload(User.roles)).where(User.email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            if user is None:
                raise NotFoundException(f"User with email {email} not found")
            return user
        except NotFoundException as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error fetching user by email: {str(e)}")

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username with roles loaded"""
        try:
            query = select(User).options(selectinload(User.roles)).where(User.username == username)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            if user is None:
                raise NotFoundException(f"User with username {username} not found")
            return user
        except NotFoundException as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"Error fetching user by username: {str(e)}")

    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """Create a new user"""
        try:
            user = User(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                is_active=user_data.is_active,
                is_superuser=user_data.is_superuser,
                roles=[]  # Initialize with empty roles list
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            # Explicitly load roles
            await self.db.refresh(user, attribute_names=['roles'])
            return user
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error creating user: {str(e)}")

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user details"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise NotFoundException(f"User with ID {user_id} not found")

            update_data = user_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(user, key, value)

            await self.db.commit()
            await self.db.refresh(user)
            return user
        except NotFoundException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error updating user: {str(e)}")

    async def create_token(self, token_data: TokenCreate) -> Token:
        """Create a new token"""
        try:
            token = Token(**token_data.model_dump())
            self.db.add(token)
            await self.db.commit()
            await self.db.refresh(token)
            return token
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error creating token: {str(e)}")

    async def revoke_token(self, token: str) -> None:
        """Revoke a token"""
        try:
            query = update(Token).where(Token.token == token).values(is_revoked=True)
            await self.db.execute(query)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error revoking token: {str(e)}")

    async def get_valid_token(self, token: str) -> Optional[Token]:
        """Get a valid (non-revoked, non-expired) token"""
        try:
            query = select(Token).where(
                and_(
                    Token.token == token,
                    Token.is_revoked == False,
                    Token.expires_at > datetime.utcnow()
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"Error fetching token: {str(e)}")

    async def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role"""
        try:
            # Convert permissions list to JSON string
            data = role_data.model_dump()
            data['permissions'] = json.dumps(data['permissions'])
            role = Role(**data)
            self.db.add(role)
            await self.db.commit()
            await self.db.refresh(role)
            return role
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error creating role: {str(e)}")

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name"""
        try:
            query = select(Role).where(Role.name == name)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"Error fetching role by name: {str(e)}")

    async def assign_role_to_user(self, user_id: int, role_id: int) -> None:
        """Assign a role to a user"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise NotFoundException(f"User with ID {user_id} not found")

            role = await self.db.get(Role, role_id)
            if not role:
                raise NotFoundException(f"Role with ID {role_id} not found")

            user.roles.append(role)
            await self.db.commit()
        except NotFoundException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"Error assigning role to user: {str(e)}")
