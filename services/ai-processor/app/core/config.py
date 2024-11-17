from typing import Any, Dict, Optional

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Cloud Storage - AI Processor Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # MinIO settings
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_HOST: str = "minio"
    MINIO_PORT: int = 9000
    MINIO_USE_SSL: bool = False
    
    # Weaviate settings
    WEAVIATE_URL: str = "http://weaviate:8080"
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    
    # HuggingFace settings
    HUGGINGFACE_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    @validator("WEAVIATE_URL", pre=True)
    def validate_weaviate_url(cls, v: Optional[str]) -> str:
        if not v:
            return "http://weaviate:8080"
        return v

    @validator("KAFKA_BOOTSTRAP_SERVERS", pre=True)
    def validate_kafka_bootstrap_servers(cls, v: Optional[str]) -> str:
        if not v:
            return "kafka:29092"
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()