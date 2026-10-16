from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Project Management API"
    app_version: str = "0.1.0"
    app_description: str = "A collaborative project management REST API built with FastAPI."
    environment: str = "development"
    debug: bool = True

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "project_management"

    @property
    def database_url(self) -> str:
        """Constructs MySQL SQLAlchemy connection URI."""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: list[str] = ["*"]

    # Email & OTP Configuration
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = False
    emails_from_email: str = "noreply@projectapi.com"
    emails_from_name: str = "Project Management API"
    otp_expire_minutes: int = 10
    otp_max_attempts: int = 5
    password_reset_token_expire_minutes: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton instance of application settings."""
    return Settings()