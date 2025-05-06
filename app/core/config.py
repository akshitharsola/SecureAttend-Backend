# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional, List
import secrets
from pathlib import Path

class Settings(BaseSettings):
    # Base configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SecureAttend"
    
    # Secret key for JWT
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"  # Add this line if missing
    # Token configuration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    TOKEN_ALGORITHM: str = "HS256"
    
    # Database configuration
    DATABASE_TYPE: str = "sqlite"  # "sqlite" or "postgresql"
    
    # SQLite settings (for development)
    SQLITE_DB_PATH: str = "secureattend.db"
    
    # PostgreSQL settings (for production)
    POSTGRES_SERVER: Optional[str] = "localhost"
    POSTGRES_PORT: Optional[str] = "5432"
    POSTGRES_USER: Optional[str] = "postgres"
    POSTGRES_PASSWORD: Optional[str] = "password"
    POSTGRES_DB: Optional[str] = "secureattend"
    
    # QR code configuration
    QR_CODE_STORAGE_PATH: str = "static/qr_codes"
    QR_CODE_EXPIRY_MINUTES: int = 15
    # Admin user
    ADMIN_EMAIL: str = "admin@secureattend.com"
    ADMIN_PASSWORD: str = "secureadmin"
    
    # CORS configuration
    CORS_ORIGINS: List[str] = ["*"]
    
    @property
    def DATABASE_URI(self) -> str:
        if self.DATABASE_TYPE == "sqlite":
            return f"sqlite:///{self.SQLITE_DB_PATH}"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"


settings = Settings()