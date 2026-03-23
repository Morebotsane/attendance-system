"""
Core application settings and configuration
Uses pydantic-settings for type-safe config management
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Basic Info
    PROJECT_NAME: str = "Hospital Attendance System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "St200800821$"  # Change this!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/attendance_db"
    DB_ECHO: bool = False  # Set to True to see SQL queries
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "https://8000-firebase-attendance-system-1773135120418.cluster-vpxjqdstfzgs6qeiaf7rdlsqrc.cloudworkstations.dev",
        "https://80-firebase-attendance-system-1773135120418.cluster-vpxjqdstfzgs6qeiaf7rdlsqrc.cloudworkstations.dev"
    ]
    
    # Security
    QR_ENCRYPTION_KEY: str = "your-encryption-key-change-in-production"  # Fernet key
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Photo Storage
    PHOTO_STORAGE_TYPE: str = "local"  # 'local' or 's3'
    PHOTO_MAX_SIZE_MB: int = 5
    PHOTO_ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png"]
    
    # S3 Settings (if using cloud storage)
    S3_BUCKET: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = "us-east-1"
    
    # Geofencing
    DEFAULT_GEOFENCE_RADIUS_METERS: int = 100
    GEOFENCE_ACCURACY_REQUIRED_METERS: int = 50  # GPS accuracy threshold
    
    # Attendance Rules
    CHECK_IN_GRACE_PERIOD_MINUTES: int = 15
    LATE_THRESHOLD_MINUTES: int = 15
    DUPLICATE_CHECK_IN_PREVENTION_HOURS: int = 1
    
    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Feature Flags
    ENABLE_PHOTO_VERIFICATION: bool = True
    ENABLE_FACE_MATCHING: bool = False  # Advanced feature
    ENABLE_SMS_NOTIFICATIONS: bool = False
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    
    # Africa's Talking SMS
    AFRICAS_TALKING_USERNAME: str = "sandbox"
    AFRICAS_TALKING_API_KEY: str = ""
    
    # Twilio SMS (Backup)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    
    # Email (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    FROM_NAME: str = "Hospital Attendance System"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Create cached settings instance
    This ensures settings are only loaded once
    """
    return Settings()


# Create global settings instance
settings = get_settings()

