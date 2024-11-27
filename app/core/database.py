"""
Database configuration module
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import MetaData, text

from app.core.config import settings
from app.core.logging import logger

# Create a metadata object with naming conventions for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)

# Create declarative base
Base = declarative_base(metadata=metadata)

class DatabaseManager:
    """Database connection manager with retry mechanism."""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker = None
        self._retry_count = 0
        self._max_retries = 5
        self._retry_delay = 1  # seconds
    
    async def connect(self) -> None:
        """Establish database connection with retry mechanism."""
        while self._retry_count < self._max_retries:
            try:
                if self.engine:
                    await self.engine.dispose()
                
                self.engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=settings.DB_ECHO,
                    future=True,
                    pool_size=settings.DB_POOL_SIZE,
                    max_overflow=settings.DB_MAX_OVERFLOW,
                    pool_pre_ping=True,  # Enable connection health checks
                    pool_recycle=3600,  # Recycle connections every hour
                    connect_args={
                        "command_timeout": 10,  # 10 second timeout for commands
                        "server_settings": {
                            "statement_timeout": "10000",  # 10 seconds
                            "idle_in_transaction_session_timeout": "30000"  # 30 seconds
                        }
                    }
                )
                
                # Test the connection
                async with self.engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                
                self.async_session_maker = sessionmaker(
                    self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False
                )
                
                logger.info("Database connection established successfully")
                return
            
            except OperationalError as e:
                self._retry_count += 1
                if self._retry_count >= self._max_retries:
                    logger.error(f"Failed to connect to database after {self._max_retries} attempts: {str(e)}")
                    raise
                
                logger.warning(
                    f"Database connection attempt {self._retry_count} failed. "
                    f"Retrying in {self._retry_delay} seconds..."
                )
                await asyncio.sleep(self._retry_delay)
                self._retry_delay *= 2  # Exponential backoff
    
    async def disconnect(self) -> None:
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.async_session_maker = None
            logger.info("Database connection closed")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic rollback on error."""
        if not self.async_session_maker:
            await self.connect()
            
        session: AsyncSession = self.async_session_maker()
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error occurred: {str(e)}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error occurred: {str(e)}")
            raise
        finally:
            await session.close()

# Create global database manager instance
db_manager = DatabaseManager()

async def init_models() -> None:
    """Initialize database models."""
    try:
        if not db_manager.engine:
            await db_manager.connect()
            
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database models initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database models: {str(e)}")
        raise

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database dependency injection."""
    async with db_manager.session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Error in database session: {str(e)}")
            raise
