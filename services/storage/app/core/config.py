from typing import Any, Dict, Optional

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Cloud Storage - Storage Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_HOST: str = "minio"
    MINIO_PORT: int = 9000
    MINIO_USE_SSL: bool = False
    
    @validator("MINIO_HOST", pre=True)
    def validate_minio_host(cls, v: Optional[str]) -> str:
        if not v:
            return "minio"
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()