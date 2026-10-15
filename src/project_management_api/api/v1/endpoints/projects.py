from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_user
from project_management_api.api.v1.endpoints.workspaces import require_workspace_membership
from project_management_api.crud import project as crud_project
from project_management_api.crud import user as crud_user
from project_management_api.crud import workspace as crud_workspace
from project_management_api.db.session import get_db
from project_management_api.models.project import Project, ProjectMember, ProjectRole
from project_management_api.models.user import User
from project_management_api.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from project_management_api.schemas.project import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectMemberResponse,
    ProjectResponse,
)

router = APIRouter()

@router.post(
    "/{slug}/projects/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project in a workspace",
)
def create_project(
    project_in: ProjectCreate,
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a new project in the workspace. Only OWNER or ADMIN can create projects."""
    workspace, membership = context

    if membership.role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners and admins can create projects.",
        )

    existing = crud_project.get_project_by_key(db, workspace_id=workspace.id, key=project_in.key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A project with key '{project_in.key}' already exists in this workspace.",
        )

    return crud_project.create_project(
        db,
        project_in=project_in,
        workspace_id=workspace.id,
        creator_id=current_user.id,
    )

@router.get(
    "/{slug}/projects/",
    response_model=list[ProjectResponse],
    summary="List projects in a workspace",
)
def list_projects(
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists projects visible to the current user in this workspace."""
    workspace, membership = context
    is_admin_or_owner = membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]

    return crud_project.get_projects_for_user(
        db,
        workspace_id=workspace.id,
        user_id=current_user.id,
        is_workspace_admin_or_owner=is_admin_or_owner,
    )

@router.get(
    "/{slug}/projects/{key}",
    response_model=ProjectResponse,
    summary="Get project by key",
)
def get_project(
    key: str,
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetches a project by its short key."""
    workspace, membership = context
    project = crud_project.get_project_by_key(db, workspace_id=workspace.id, key=key)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    is_admin_or_owner = membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    if not is_admin_or_owner:
        project_membership = crud_project.get_project_membership(
            db, project_id=project.id, user_id=current_user.id
        )
        if not project_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project.",
            )

    return project

@router.get(
    "/{slug}/projects/{key}/members",
    response_model=list[ProjectMemberResponse],
    summary="List project members",
)
def list_project_members(
    key: str,
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
):
    """Returns all members assigned to this project."""
    workspace, _ = context
    project = crud_project.get_project_by_key(db, workspace_id=workspace.id, key=key)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return crud_project.get_project_members(db, project_id=project.id)

@router.post(
    "/{slug}/projects/{key}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add member to project",
)
def add_member_to_project(
    key: str,
    member_in: ProjectMemberAdd,
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Adds an existing workspace member to the project."""
    workspace, ws_membership = context
    project = crud_project.get_project_by_key(db, workspace_id=workspace.id, key=key)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    is_admin_or_owner = ws_membership.role in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
    proj_membership = crud_project.get_project_membership(db, project.id, current_user.id)
    is_lead = proj_membership and proj_membership.role == ProjectRole.PROJECT_LEAD

    if not (is_admin_or_owner or is_lead):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace admins or project leads can add project members.",
        )

    user_to_add = crud_user.get_user_by_email(db, email=member_in.email)
    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not crud_workspace.get_workspace_membership(db, workspace.id, user_to_add.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be a member of the workspace before being added to a project.",
        )

    if crud_project.get_project_membership(db, project.id, user_to_add.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this project.",
        )

    return crud_project.add_project_member(
        db, project_id=project.id, user_id=user_to_add.id, role=member_in.role
    )