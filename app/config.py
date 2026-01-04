import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Application settings loaded from environment variables."""
    
    # Application settings
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "masterproject-api")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    
    # AWS Settings
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # X-Ray settings
    XRAY_DAEMON_ADDRESS: str = os.getenv("XRAY_DAEMON_ADDRESS", "127.0.0.1:2000")
    XRAY_TRACING_ENABLED: bool = os.getenv("XRAY_TRACING_ENABLED", "true").lower() == "true"
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")  # json or text
    
    # Database settings (Phase 3)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "masterprojectdb")
    DB_USER: str = os.getenv("DB_USER", "dbadmin")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_ENABLED: bool = os.getenv("DB_ENABLED", "false").lower() == "true"
    
    # Redis cache settings (Phase 3)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_SSL: bool = os.getenv("REDIS_SSL", "false").lower() == "true"
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "false").lower() == "true"


# Global settings instance
settings = Settings()
