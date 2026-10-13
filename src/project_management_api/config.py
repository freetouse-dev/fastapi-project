from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Project Management API"
    app_version: str = "0.1.0"
    app_description: str = "A collaborative project management REST API built with FastAPI."
    environment: str = "development"
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton instance of application settings."""
    return Settings()