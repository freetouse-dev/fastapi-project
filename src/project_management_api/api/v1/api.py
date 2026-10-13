from fastapi import APIRouter

from project_management_api.api.v1.endpoints import health

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, tags=["Health"])