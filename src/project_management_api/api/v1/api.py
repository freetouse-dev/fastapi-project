from fastapi import APIRouter
from project_management_api.api.v1.endpoints import (
    auth,
    comments,
    health,
    projects,
    tasks,
    users,
    workspaces,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])
api_router.include_router(projects.router, prefix="/workspaces", tags=["Projects"])
api_router.include_router(tasks.router, prefix="/workspaces", tags=["Tasks"])
api_router.include_router(comments.router, prefix="/workspaces", tags=["Comments"])