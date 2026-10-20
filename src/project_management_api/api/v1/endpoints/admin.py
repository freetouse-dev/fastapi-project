from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_user
from project_management_api.core.permissions import require_superuser
from project_management_api.crud import audit as crud_audit
from project_management_api.crud import comment as crud_comment
from project_management_api.crud import project as crud_project
from project_management_api.crud import task as crud_task
from project_management_api.crud import user as crud_user
from project_management_api.crud import workspace as crud_workspace
from project_management_api.db.session import get_db
from project_management_api.models.task import TaskPriority, TaskStatus
from project_management_api.models.user import User
from project_management_api.schemas.audit import AdminStatsResponse, AuditLogResponse
from project_management_api.schemas.comment import CommentResponse
from project_management_api.schemas.common import PaginatedResponse
from project_management_api.schemas.project import ProjectResponse
from project_management_api.schemas.task import TaskResponse
from project_management_api.schemas.user import UserAdminUpdate, UserResponse
from project_management_api.schemas.workspace import WorkspaceResponse

router = APIRouter(dependencies=[Depends(require_superuser)])


@router.get("/stats", response_model=AdminStatsResponse, summary="Admin Dashboard overview stats")
def get_stats(db: Session = Depends(get_db)):
    """Computes high-level counts and statistics for the Admin Dashboard."""
    return crud_user.get_admin_stats(db)


@router.get("/users", response_model=PaginatedResponse[UserResponse], summary="List all users")
def list_users(
    search: str | None = Query(None, description="Search by name or email"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_verified: bool | None = Query(None, description="Filter by verified status"),
    is_superuser: bool | None = Query(None, description="Filter by superuser role"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Returns a paginated list of all registered platform users."""
    items, total = crud_user.get_users_paginated(
        db,
        search=search,
        is_active=is_active,
        is_verified=is_verified,
        is_superuser=is_superuser,
        page=page,
        size=size,
    )
    return PaginatedResponse.create(items=items, total=total, page=page, size=size)


@router.patch("/users/{user_id}", response_model=UserResponse, summary="Modify user status or role")
def update_user_status(
    user_id: int,
    user_in: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin endpoint to activate/deactivate users or toggle superuser privileges."""
    target_user = crud_user.get_user_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Prevent a superuser from removing their own superuser privileges accidentally
    if target_user.id == current_user.id and user_in.is_superuser is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot revoke your own superuser privileges.",
        )

    return crud_user.update_user_admin(
        db, db_user=target_user, user_in=user_in, actor_id=current_user.id
    )


@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogResponse], summary="View system audit logs")
def list_audit_logs(
    actor_id: int | None = Query(None, description="Filter by actor ID"),
    action: str | None = Query(None, description="Filter by action name"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    resource_id: str | None = Query(None, description="Filter by resource ID"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Returns paginated, searchable system audit trails for administrative review."""
    items, total = crud_audit.get_audit_logs(
        db,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        page=page,
        size=size,
    )
    return PaginatedResponse.create(items=items, total=total, page=page, size=size)


@router.get("/workspaces", response_model=list[WorkspaceResponse], summary="List all workspaces (admin)")
def list_all_workspaces(
    include_deleted: bool = Query(False, description="Include soft-deleted workspaces"),
    db: Session = Depends(get_db),
):
    """Returns all workspaces across the platform."""
    return crud_workspace.get_all_workspaces(db, include_deleted=include_deleted)


@router.get("/projects", response_model=list[ProjectResponse], summary="List all projects (admin)")
def list_all_projects(
    include_deleted: bool = Query(False, description="Include soft-deleted projects"),
    db: Session = Depends(get_db),
):
    """Returns all projects across the platform."""
    return crud_project.get_all_projects(db, include_deleted=include_deleted)


@router.get("/tasks", response_model=PaginatedResponse[TaskResponse], summary="List all tasks (admin)")
def list_all_tasks(
    search: str | None = Query(None),
    status: TaskStatus | None = Query(None),
    priority: TaskPriority | None = Query(None),
    project_id: int | None = Query(None),
    include_deleted: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Returns paginated tasks across all projects."""
    items, total = crud_task.get_all_tasks_paginated(
        db,
        search=search,
        status=status,
        priority=priority,
        project_id=project_id,
        page=page,
        size=size,
        include_deleted=include_deleted,
    )
    return PaginatedResponse.create(items=items, total=total, page=page, size=size)


@router.get("/comments", response_model=PaginatedResponse[CommentResponse], summary="List all comments (admin)")
def list_all_comments(
    include_deleted: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Returns paginated comments for moderation."""
    items, total = crud_comment.get_all_comments_paginated(
        db, page=page, size=size, include_deleted=include_deleted
    )
    return PaginatedResponse.create(items=items, total=total, page=page, size=size)
