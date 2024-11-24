"""
Configuration settings for the AI Cloud Storage service.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Cloud Storage"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered cloud storage service"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    TESTING: bool = False
    
    # Module Settings
    STORAGE_MODULE_ENABLED: bool = True
    AI_PROCESSOR_MODULE_ENABLED: bool = True
    
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "aicloud"
    POSTGRES_PASSWORD: str = "aicloud"
    POSTGRES_DB: str = "aicloud"
    DB_POOL_SIZE: int = 32
    DB_MAX_OVERFLOW: int = 64
    DB_ECHO: bool = False
    
    @property
    def DATABASE_URL(self) -> str:
        """Get database URL as string"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}?sslmode=disable"
    
    # MinIO Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_REGION: str = "us-east-1"
    MINIO_BUCKET_NAME: str = "aicloud-storage"
    
    # Security
    JWT_SECRET_KEY: str = "d5e087a4f1c8e6b3a2d9c0b7e4f8a1d3"  # Replace with a secure key in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"
    )
    
    @field_validator("CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Convert CORS origins to list"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

settings = Settings()
