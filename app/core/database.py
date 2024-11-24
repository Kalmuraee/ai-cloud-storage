"""
Database configuration module
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import MetaData

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

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

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args={"server_settings": {"ssl": "false"}}
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_models():
    """Initialize database models"""
    # Import all models to ensure they are registered
    from app import models
    
    try:
        async with engine.begin() as conn:
            # Drop all tables in testing environment
            if settings.TESTING:
                await conn.run_sync(Base.metadata.drop_all)
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
            # Test connection
            await conn.execute("SELECT 1")
            
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

async def get_db() -> AsyncSession:
    """Get database session"""
    async with async_session() as session:
        try:
            # Test the connection
            await session.execute("SELECT 1")
            yield session
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()
