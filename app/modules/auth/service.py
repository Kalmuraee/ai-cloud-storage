"""
Authentication service implementation
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.exceptions import (
    InvalidCredentialsError,
    TokenError,
    ValidationError,
    ConflictError
)
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    UserCreate,
    UserUpdate,
    UserInDB,
    Token,
    TokenCreate
)
from app.modules.auth.models import User

settings = Settings()
logger = get_logger(__name__)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)

class AuthService:
    """Authentication service with repository pattern"""
    
    def __init__(self, repository: AuthRepository):
        """Initialize auth service with repository"""
        self.repository = repository
        self.pwd_context = pwd_context
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Get password hash"""
        try:
            return self.pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing failed: {str(e)}")
            raise ValidationError("Failed to hash password")
    
    async def authenticate_user(self, username: str, password: str) -> Token:
        """
        Authenticate user and return access token
        
        Args:
            username: Username or email
            password: User's password
            
        Returns:
            Token: Access token information
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        # Try to find user by email or username
        user = await self.repository.get_user_by_email(username)
        if not user:
            user = await self.repository.get_user_by_username(username)
        
        if not user or not self.verify_password(password, user.hashed_password):
            logger.warning(f"Invalid credentials for user: {username}")
            raise InvalidCredentialsError()
        
        # Create access token
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email
        }
        
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expires_at = datetime.utcnow() + expires_delta
        access_token = self._create_access_token(token_data, expires_delta)
        
        # Store token in database
        token_create = TokenCreate(
            token=access_token,
            token_type="bearer",
            user_id=user.id,
            expires_at=expires_at
        )
        await self.repository.create_token(token_create)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=expires_at
        )
    
    def _create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            expires_delta if expires_delta
            else timedelta(minutes=self.access_token_expire_minutes)
        )
        to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
        try:
            return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        except Exception as e:
            logger.error(f"Failed to create access token: {str(e)}")
            raise TokenError("Failed to create access token")
    
    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """
        Create a new user
        
        Args:
            user_data: User creation data
            
        Returns:
            UserInDB: Created user information
            
        Raises:
            ValidationError: If user data is invalid
            ConflictError: If username or email already exists
        """
        # Check if username or email already exists
        if await self.repository.get_user_by_email(user_data.email):
            raise ConflictError(f"Email {user_data.email} already registered")
        
        if await self.repository.get_user_by_username(user_data.username):
            raise ConflictError(f"Username {user_data.username} already taken")
        
        # Hash password
        hashed_password = self.get_password_hash(user_data.password)
        
        # Create user
        user = await self.repository.create_user(user_data, hashed_password)
        return UserInDB.model_validate(user)
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserInDB:
        """
        Update user information
        
        Args:
            user_id: ID of user to update
            user_data: User update data
            
        Returns:
            UserInDB: Updated user information
            
        Raises:
            ValidationError: If update data is invalid
            ConflictError: If new email or username already exists
        """
        update_data = user_data.model_dump(exclude_unset=True)
        
        # If email is being updated, check it's not taken
        if "email" in update_data:
            existing_user = await self.repository.get_user_by_email(update_data["email"])
            if existing_user and existing_user.id != user_id:
                raise ConflictError(f"Email {update_data['email']} already registered")
        
        # If password is being updated, hash it
        if "password" in update_data:
            update_data["hashed_password"] = self.get_password_hash(update_data.pop("password"))
        
        # Update user
        user = await self.repository.update_user(user_id, user_data)
        return UserInDB.model_validate(user)
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from token
        
        Args:
            token: JWT access token
            
        Returns:
            Optional[User]: User if token is valid
            
        Raises:
            TokenError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = int(payload.get("sub"))
            if user_id is None:
                raise TokenError()
        except JWTError as e:
            logger.error(f"JWT decode failed: {str(e)}")
            raise TokenError()
        
        # Verify token is still valid in database
        db_token = await self.repository.get_valid_token(token)
        if not db_token:
            raise TokenError("Token has been revoked")
        
        user = await self.repository.get_user_by_id(user_id)
        if user is None:
            raise TokenError()
        
        return user
    
    async def revoke_token(self, token: str) -> None:
        """
        Revoke an access token
        
        Args:
            token: Token to revoke
            
        Raises:
            TokenError: If token is invalid
        """
        await self.repository.revoke_token(token)
