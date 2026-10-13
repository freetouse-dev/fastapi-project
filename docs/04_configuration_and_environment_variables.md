# Step 4: Configuration Management & Environment Variables

## 1. Overview
In this step, we introduced twelve-factor application configuration management using `pydantic-settings`. We replaced hardcoded application values with typed, validated environment variables read from `.env`.

---

## 2. Concepts Learned

### 2.1 The Twelve-Factor App Principle (Factor III: Config)
- Configuration (database URLs, API keys, environment modes) varies across deployments (local dev, staging, production), whereas code does not.
- Hardcoded secrets in source code pose major security hazards and make deployment inflexible.
- Configuration must be strictly separated from code and provided via environment variables.

### 2.2 Pydantic Settings (`BaseSettings`)
- **Type Safety & Coercion:** Environment variables are raw strings by default. Pydantic automatically parses and validates them into proper types (`bool`, `int`, etc.).
- **Defaults & Fallbacks:** Provides sensible defaults for local development while allowing overrides in staging/production.
- **Fail-Fast Validation:** If a mandatory variable is missing or malformed, the application stops immediately at startup with an informative error rather than failing silently later.
- **`@lru_cache`:** Caches the `Settings` instance so `.env` parsing occurs only once at startup rather than on every incoming HTTP request.

---

## 3. Implementation Details

### Configuration Module: `src/project_management_api/config.py`
```python
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
```

### Application Entry Point: `src/project_management_api/main.py`
Updated the FastAPI metadata and endpoints to consume `get_settings()` dynamically.

---

## 4. Verification & Testing
```bash
curl http://127.0.0.1:8000/health
```
Output:
```json
{
  "status": "healthy",
  "service": "Project Management API",
  "environment": "development",
  "debug": true
}
```
Environment values were loaded and typed properly into the health check response.
