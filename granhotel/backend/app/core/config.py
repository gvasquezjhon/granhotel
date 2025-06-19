from pydantic_settings import BaseSettings
import os
from typing import List, Union, Any # Added Any

class Settings(BaseSettings):
    PROJECT_NAME: str = "Gran Hotel API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@db/granhoteldb") # Changed localhost to db for docker-compose

    # JWT Settings (to be added later)
    # SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key")
    # ALGORITHM: str = "HS256"
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Settings
    CORS_ORIGINS: Union[str, List[str]] = os.getenv("CORS_ORIGINS", "*") # Default to all, can be comma-separated string

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'

        # If CORS_ORIGINS is a string from .env, convert it to a list
        # This is a Pydantic v1 way, for Pydantic v2 `model_validator` or `field_validator` would be used
        # For pydantic-settings, we might need to adjust if direct parsing isn't supported this way.
        # However, pydantic-settings usually handles simple type coercion.
        # If complex parsing is needed, it's often done after settings object creation.
        # For now, let's assume it's processed by the application where it's used, or keep it simple.
        # The logic in main.py `settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') ...` handles it being potentially a string.
        # For a cleaner approach with pydantic-settings, one might use a validator if the value needs to be strictly a list.
        # Let's simplify and assume the consumer of this config (FastAPI middleware) can handle a string or list,
        # or we process it in main.py before passing. The provided code in main.py already checks hasattr.
        # The provided parse_env_var is for Pydantic v1. Pydantic-settings handles .env loading differently.
        # Let's remove the custom parse_env_var for now as pydantic-settings has its own mechanisms.
        # The value will be loaded as a string if it's a comma-separated list, and FastAPI will need to handle that.
        # Or we can process it after loading settings.
        # For simplicity, the FastAPI middleware will get the string, and it might not work as expected if it expects a list.
        # A better way for pydantic-settings >v2 is to use a validator.
        # Let's stick to the provided snippet's intention.

    @classmethod
    def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
        if field_name == 'CORS_ORIGINS' and isinstance(raw_val, str) and raw_val != "*":
            return [origin.strip() for origin in raw_val.split(',')]
        return raw_val

settings = Settings()

# Post-process CORS_ORIGINS if it's a string from env and not "*"
if isinstance(settings.CORS_ORIGINS, str) and settings.CORS_ORIGINS != "*":
    settings.CORS_ORIGINS = [origin.strip() for origin in settings.CORS_ORIGINS.split(',')]
elif settings.CORS_ORIGINS == "*":
    settings.CORS_ORIGINS = ["*"] # Ensure it's a list for consistency if it's the wildcard string
