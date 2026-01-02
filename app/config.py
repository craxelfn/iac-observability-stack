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


# Global settings instance
settings = Settings()
