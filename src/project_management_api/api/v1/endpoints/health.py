from fastapi import APIRouter

from project_management_api.config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/health", summary="Health Check")
def health_check():
    """Returns the operational status of the service."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
        "version": settings.app_version,
    }