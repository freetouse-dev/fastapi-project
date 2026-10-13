from fastapi import FastAPI
from project_management_api.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
)

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to the {settings.app_name}",
        "environment": settings.environment,
        "docs": "/docs",
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
        "debug": settings.debug,
    }