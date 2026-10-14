from fastapi import FastAPI

from project_management_api.api.v1.api import api_router
from project_management_api.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
)

app.include_router(api_router, prefix="/api/v1")

# @app.get("/", summary="Root Welcome")
# def read_root():
#     return {
#         "message": f"Welcome to the {settings.app_name}",
#         "environment": settings.environment,
#         "docs": "/docs",
#     }