import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Unitask"
    app_version: str = "0.1.0"
    app_description: str = "Unitask - A modern collaborative multi-tenant project management platform."
    environment: str = "development"
    debug: bool = True

    # Database configuration supporting MySQL and PostgreSQL
    db_type: str = "mysql"  # "mysql" | "postgresql" | "postgres"
    db_host: str = "localhost"
    db_port: int | None = None
    db_user: str = "ajay"
    db_password: str = "password"
    db_name: str = "project_management"
    database_url_override: str | None = None

    @property
    def database_url(self) -> str:
        """
        Constructs the SQLAlchemy connection URI dynamically.
        Seamlessly switches between MySQL (pymysql) and PostgreSQL (psycopg).
        Accepts explicit DATABASE_URL overrides if provided.
        """
        raw_url = self.database_url_override or os.environ.get("DATABASE_URL")
        if raw_url:
            if raw_url.startswith("postgres://"):
                return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
            elif raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+"):
                return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
            elif raw_url.startswith("mysql://") and not raw_url.startswith("mysql+"):
                return raw_url.replace("mysql://", "mysql+pymysql://", 1)
            return raw_url

        db_choice = (self.db_type or "mysql").strip().lower()
        if "postgres" in db_choice:
            port = self.db_port if (self.db_port and self.db_port != 3306) else 5432
            return (
                f"postgresql+psycopg://{self.db_user}:{self.db_password}@"
                f"{self.db_host}:{port}/{self.db_name}"
            )
        else:
            port = self.db_port if (self.db_port and self.db_port != 5432) else 3306
            return (
                f"mysql+pymysql://{self.db_user}:{self.db_password}@"
                f"{self.db_host}:{port}/{self.db_name}"
            )
    
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: list[str] = ["*"]

    # Email & OTP Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = "gingergin348@gmail.com"
    smtp_password: str = "rwpr xkch skvl bvad"
    smtp_tls: bool = True
    emails_from_email: str = "gingergin348@gmail.com"
    emails_from_name: str = "Unitask"
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