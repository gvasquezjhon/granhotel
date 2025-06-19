from pydantic_settings import BaseSettings
import os
from typing import List, Union, Any

class Settings(BaseSettings):
    PROJECT_NAME: str = "Gran Hotel API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@db/granhoteldb")

    # Localization and Timezone
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "es_PE")
    TIMEZONE: str = os.getenv("TIMEZONE", "America/Lima")

    # CORS Settings
    # Pydantic-settings will attempt to parse a comma-separated string from env into a List[str] if the type hint is List[str].
    # If it's Union[str, List[str]], it will be a string if it contains commas, unless a custom validator is used.
    # For simplicity, FastAPI's CORSMiddleware can often handle a string of origins if it's just "*".
    # If multiple specific origins are needed from env, they should be processed into a list.
    # The current main.py handles this: `settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') and settings.CORS_ORIGINS else ["*"]`
    # and the post-processing logic for CORS_ORIGINS was removed in a previous step.
    # To make it a list directly from a comma-separated string in .env, a validator would be best in Pydantic v2.
    # For now, we rely on the consuming code (FastAPI middleware) to correctly interpret it or process it.
    CORS_ORIGINS: Union[str, List[str]] = os.getenv("CORS_ORIGINS", "*")

    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_super_secret_random_key_for_jwt_CHANGE_THIS")
    REFRESH_SECRET_KEY: str = os.getenv("REFRESH_SECRET_KEY", "your_super_secret_random_key_for_refresh_jwt_CHANGE_THIS")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

# If CORS_ORIGINS is a comma-separated string, split it into a list.
# This ensures that the setting is always a list of strings if it's not the wildcard "*".
if isinstance(settings.CORS_ORIGINS, str) and settings.CORS_ORIGINS != "*":
    settings.CORS_ORIGINS = [origin.strip() for origin in settings.CORS_ORIGINS.split(',')]
elif settings.CORS_ORIGINS == "*" and not isinstance(settings.CORS_ORIGINS, list):
    settings.CORS_ORIGINS = ["*"]
