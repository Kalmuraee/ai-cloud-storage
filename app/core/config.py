"""
Configuration settings for the AI Cloud Storage service.
"""
from typing import Any, Dict, List, Optional, Union, Set
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Project Information
    PROJECT_NAME: str = "AI Cloud Storage"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: str = "AI-powered cloud storage service"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    TESTING: bool = False
    STORAGE_MODULE_ENABLED: bool = True
    
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_cloud_storage"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key"  # Change in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # MinIO Configuration
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "ai-cloud-storage"
    MINIO_REGION: str = "us-east-1"  # Added back
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: Set[str] = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}
    
    # AI Processing
    MODEL_TIMEOUT: int = 30  # seconds
    MAX_PROCESSING_RETRIES: int = 3
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Rate Limiting
    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # AI Models
    DEFAULT_CLASSIFICATION_MODEL: str = "distilbert-base-uncased"
    DEFAULT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )
    
    @field_validator("CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Convert CORS origins to list"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

settings = Settings()

def get_settings() -> Settings:
    """Get settings instance"""
    return settings
