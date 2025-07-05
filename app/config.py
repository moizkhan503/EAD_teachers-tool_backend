"""
Application configuration settings.
"""
import os
from typing import Dict, List, Any, Union, Optional
from pydantic import Field, AnyHttpUrl, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Curriculum Planning API"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0" if os.getenv("DOCKER_MODE", "").lower() == "true" else "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Qdrant Settings
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333" if os.getenv("DOCKER_MODE") else "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    
    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Groq Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # Default frontend port
        "http://localhost:8000",  # Default backend port
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # LLM Settings
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Rate Limiting
    RATE_LIMIT: str = os.getenv("RATE_LIMIT", "100/minute")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
