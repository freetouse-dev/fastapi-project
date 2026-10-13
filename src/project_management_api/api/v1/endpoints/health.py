from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from project_management_api.config import get_settings
from project_management_api.db.session import get_db

router = APIRouter()
settings = get_settings()


@router.get("/health", summary="Health Check")
def health_check(db: Session = Depends(get_db)):
    """Returns the operational status of the service and database."""
    db_status = "unhealthy"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"disconnected: {exc}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": settings.app_name,
        "environment": settings.environment,
        "version": settings.app_version,
        "database": db_status,
    }