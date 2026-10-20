from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_user
from project_management_api.api.v1.endpoints.workspaces import require_workspace_membership
from project_management_api.crud import activity as crud_activity
from project_management_api.crud import project as crud_project
from project_management_api.crud import task as crud_task
from project_management_api.crud import user as crud_user
from project_management_api.crud import workspace as crud_workspace
from project_management_api.db.session import get_db
from project_management_api.models.project import Project, ProjectRole
from project_management_api.models.task import TaskPriority, TaskStatus
from project_management_api.models.user import User
from project_management_api.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from project_management_api.schemas.activity import TaskActivityResponse
from project_management_api.schemas.common import PaginatedResponse
from project_management_api.schemas.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter()


def require_project_context(
    slug: str,
    key: str,
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> tuple[Workspace, WorkspaceMember, Project]:
    """Validates workspace membership and access to the requested project."""
    workspace, ws_membership = context
    project = crud_project.get_project_by_key(db, workspace_id=workspace.id, key=key)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    is_admin_or_owner = current_user.is_superuser or ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    if not is_admin_or_owner:
        proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
        if not proj_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project.",
            )

    return workspace, ws_membership, project


@router.post(
    "/{slug}/projects/{key}/tasks/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
)
def create_task(
    task_in: TaskCreate,
    context: tuple[Workspace, WorkspaceMember, Project] = Depends(require_project_context),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a new task in the project with auto-incremented ticket numbering (e.g. MOB-1)."""
    workspace, ws_membership, project = context

    is_admin_or_owner = current_user.is_superuser or ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
    if not is_admin_or_owner and (not proj_membership or proj_membership.role == ProjectRole.VIEWER or ws_membership.role == WorkspaceRole.VIEWER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewers cannot create tasks in this project.",
        )

    assignee_id = None
    if task_in.assignee_email:
        assignee = crud_user.get_user_by_email(db, email=task_in.assignee_email)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found.",
            )
        if not crud_workspace.get_workspace_membership(db, workspace.id, assignee.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of the workspace.",
            )
        assignee_id = assignee.id

    return crud_task.create_task(
        db,
        task_in=task_in,
        project_id=project.id,
        creator_id=current_user.id,
        assignee_id=assignee_id,
    )


@router.get(
    "/{slug}/projects/{key}/tasks/",
    response_model=PaginatedResponse[TaskResponse],
    summary="List, search, filter, and paginate tasks",
)
def list_tasks(
    search: str | None = Query(None, description="Search term matching title or description"),
    status: TaskStatus | None = Query(None, description="Filter by status"),
    priority: TaskPriority | None = Query(None, description="Filter by priority"),
    sort_by: str = Query("task_number", description="Field to sort by (task_number, title, status, priority, created_at, due_date)"),
    sort_order: str = Query("asc", description="Sort direction ('asc' or 'desc')"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    context: tuple[Workspace, WorkspaceMember, Project] = Depends(require_project_context),
    db: Session = Depends(get_db),
):
    """Returns a paginated list of active tasks matching search, filter, and sort criteria."""
    _, _, project = context
    items, total = crud_task.get_tasks_paginated(
        db,
        project_id=project.id,
        search=search,
        status=status,
        priority=priority,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )
    return PaginatedResponse.create(items=items, total=total, page=page, size=size)


@router.get(
    "/{slug}/projects/{key}/tasks/{task_number}",
    response_model=TaskResponse,
    summary="Get task by number",
)
def get_task(
    task_number: int,
    context: tuple[Workspace, WorkspaceMember, Project] = Depends(require_project_context),
    db: Session = Depends(get_db),
):
    """Fetches a single task by its project ticket number (e.g. 1 for MOB-1)."""
    _, _, project = context
    task = crud_task.get_task_by_number(db, project_id=project.id, task_number=task_number)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {project.key}-{task_number} not found.",
        )
    return task


@router.patch(
    "/{slug}/projects/{key}/tasks/{task_number}",
    response_model=TaskResponse,
    summary="Update task",
)
def update_task(
    task_number: int,
    task_in: TaskUpdate,
    context: tuple[Workspace, WorkspaceMember, Project] = Depends(require_project_context),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates task status, priority, description, or reassigned user."""
    workspace, ws_membership, project = context

    is_admin_or_owner = current_user.is_superuser or ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
    if not is_admin_or_owner and (not proj_membership or proj_membership.role == ProjectRole.VIEWER or ws_membership.role == WorkspaceRole.VIEWER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewers cannot update tasks in this project.",
        )

    task = crud_task.get_task_by_number(db, project_id=project.id, task_number=task_number)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {project.key}-{task_number} not found.",
        )

    assignee_id = None
    if task_in.assignee_email is not None:
        assignee = crud_user.get_user_by_email(db, email=task_in.assignee_email)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found.",
            )
        if not crud_workspace.get_workspace_membership(db, workspace.id, assignee.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of the workspace.",
            )
        assignee_id = assignee.id

    return crud_task.update_task(
        db,
        db_task=task,
        task_in=task_in,
        actor_id=current_user.id,
        assignee_id=assignee_id,
    )


@router.delete(
    "/{slug}/projects/{key}/tasks/{task_number}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete task",
)
def delete_task(
    task_number: int,
    context: tuple[Workspace, WorkspaceMember, Project] = Depends(require_project_context),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-deletes task and cascades to comments."""
    workspace, ws_membership, project = context

    task = crud_task.get_task_by_number(db, project_id=project.id, task_number=task_number)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {project.key}-{task_number} not found.",
        )

    is_admin_or_owner = current_user.is_superuser or ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
    is_lead = proj_membership and proj_membership.role == ProjectRole.PROJECT_LEAD
    is_creator = task.creator_id == current_user.id

    if not (is_admin_or_owner or is_lead or is_creator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this task.",
        )

    crud_task.soft_delete_task(db, db_task=task, actor_id=current_user.id)


@router.get(
    "/{slug}/projects/{key}/tasks/{task_number}/activities/",
    response_model=list[TaskActivityResponse],
    summary="Get task activity history",
)
def get_task_activities(
    task_number: int,
    context: tuple[Workspace, WorkspaceMember, Project] = Depends(require_project_context),
    db: Session = Depends(get_db),
):
    """Returns the full audit trail of changes made to the task."""
    _, _, project = context
    task = crud_task.get_task_by_number(db, project_id=project.id, task_number=task_number)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {project.key}-{task_number} not found.",
        )

    return crud_activity.get_activities_for_task(db, task_id=task.id)
