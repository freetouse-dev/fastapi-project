from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from project_management_api.api.v1.api import api_router
from project_management_api.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# @app.get("/", summary="Root Welcome")
# def read_root():
#     return {
#         "message": f"Welcome to the {settings.app_name}",
#         "environment": settings.environment,
#         "docs": "/docs",
#     }