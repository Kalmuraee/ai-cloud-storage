"""
Authentication service implementation
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import Settings
from app.core.logging import get_logger
from app.modules.auth.models import User, Token

settings = Settings()
logger = get_logger(__name__)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)

class AuthService:
    """Authentication service"""
    
    def __init__(self):
        """Initialize auth service"""
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
            raise ValueError("Failed to hash password")
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        db: AsyncSession
    ) -> Optional[User]:
        """Authenticate user"""
        try:
            # Try to find user by email or username
            result = await db.execute(
                select(User).where(
                    (User.email == email) | (User.username == email)
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User not found: {email}")
                return None
            
            if not self.verify_password(password, user.hashed_password):
                logger.warning(f"Invalid password for user: {email}")
                return None
            
            return user
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create access token"""
        try:
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(
                    minutes=self.access_token_expire_minutes
                )
            
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(
                to_encode,
                self.secret_key,
                algorithm=self.algorithm
            )
            
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {str(e)}")
            raise
    
    async def get_current_user(
        self,
        token: str,
        db: AsyncSession
    ) -> Optional[User]:
        """Get current user from token"""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            user_id: str = payload.get("sub")
            
            if user_id is None:
                return None
            
            # Get user
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            return user
        except JWTError:
            return None
        except Exception as e:
            logger.error(f"Failed to get current user: {str(e)}")
            raise
    
    async def create_user(
        self,
        email: str,
        password: str,
        db: AsyncSession
    ) -> User:
        """Create new user"""
        try:
            # Check if user exists
            result = await db.execute(
                select(User).where(User.email == email)
            )
            if result.scalar_one_or_none():
                raise ValueError("Email already registered")
            
            # Generate username from email
            username = email.split('@')[0]
            base_username = username
            counter = 1
            
            # Check if username exists and generate a unique one
            while True:
                result = await db.execute(
                    select(User).where(User.username == username)
                )
                if not result.scalar_one_or_none():
                    break
                username = f"{base_username}{counter}"
                counter += 1
            
            # Hash password
            try:
                hashed_password = self.get_password_hash(password)
            except ValueError as e:
                logger.error(f"Password hashing failed: {str(e)}")
                raise ValueError("Failed to process password")
            
            # Create user
            user = User(
                email=email,
                username=username,
                hashed_password=hashed_password,
                full_name=username,  # Default to username, can be updated later
                is_active=True,
                is_superuser=False
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"User created successfully: {email}")
            return user
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            raise
    
    async def create_token(
        self,
        user: User,
        db: AsyncSession
    ) -> Token:
        """Create token for user"""
        try:
            # Create token
            token = Token(
                user_id=user.id,
                access_token=self.create_access_token({"sub": str(user.id)})
            )
            db.add(token)
            await db.commit()
            await db.refresh(token)
            
            return token
        except Exception as e:
            logger.error(f"Failed to create token: {str(e)}")
            raise
    
    async def revoke_token(
        self,
        token: str,
        db: AsyncSession
    ) -> None:
        """Revoke token"""
        try:
            # Get token
            result = await db.execute(
                select(Token).where(Token.access_token == token)
            )
            db_token = result.scalar_one_or_none()
            
            if db_token:
                db_token.revoked = True
                db_token.revoked_at = datetime.utcnow()
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to revoke token: {str(e)}")
            raise
