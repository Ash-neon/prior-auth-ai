"""
Application Configuration
=========================

Pydantic settings for environment variable management.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "PriorAuth AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = Field(..., min_length=32)
    
    # API
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "priorauth"
    POSTGRES_USER: str = "priorauth_user"
    POSTGRES_PASSWORD: str = Field(..., min_length=8)
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # MinIO/S3
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "documents"
    MINIO_USE_SSL: bool = False
    
    # Anthropic API
    ANTHROPIC_API_KEY: str = Field(..., min_length=10)
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_MAX_TOKENS: int = 4096
    ANTHROPIC_TEMPERATURE: float = 0.3
    
    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    @property
    def CELERY_BROKER(self) -> str:
        """Get Celery broker URL."""
        return self.CELERY_BROKER_URL or self.REDIS_URL
    
    @property
    def CELERY_BACKEND(self) -> str:
        """Get Celery result backend URL."""
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()