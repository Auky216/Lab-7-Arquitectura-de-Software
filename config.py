# config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # JWT
    jwt_secret: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 7 * 24 * 60 * 60  # 7 days
    
    # Services URLs
    search_service_url: str = "http://localhost:3001"
    ingestion_service_url: str = "http://localhost:3002"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Rate limiting
    rate_limit_calls: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Permite campos extra

settings = Settings()