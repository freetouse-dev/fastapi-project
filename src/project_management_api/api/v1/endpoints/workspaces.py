from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_user
from project_management_api.crud import user as crud_user
from project_management_api.crud import workspace as crud_workspace
from project_management_api.db.session import get_db
from project_management_api.models.user import User
from project_management_api.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from project_management_api.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)

router = APIRouter()

def require_workspace_membership(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> tuple[Workspace, WorkspaceMember]:
    """Validates that workspace exists and the user is an active member."""
    workspace = crud_workspace.get_workspace_by_slug(db, slug=slug)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    membership = crud_workspace.get_workspace_membership(
        db, workspace_id=workspace.id, user_id=current_user.id
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace.",
        )

    return workspace, membership

@router.post(
    "/",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workspace",
)
def create_new_workspace(
    workspace_in: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a workspace and automatically assigns current_user as OWNER."""
    if workspace_in.slug:
        existing = crud_workspace.get_workspace_by_slug(db, slug=workspace_in.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A workspace with this slug already exists.",
            )

    return crud_workspace.create_workspace(
        db, workspace_in=workspace_in, owner_id=current_user.id
    )

@router.get(
    "/",
    response_model=list[WorkspaceResponse],
    summary="List my workspaces",
)
def list_my_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all workspaces the current user is a member of."""
    return crud_workspace.get_workspaces_for_user(db, user_id=current_user.id)

@router.get(
    "/{slug}",
    response_model=WorkspaceResponse,
    summary="Get workspace by slug",
)
def get_workspace(
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
):
    """Gets workspace details if the user is a member."""
    workspace, _ = context
    return workspace

@router.get(
    "/{slug}/members",
    response_model=list[WorkspaceMemberResponse],
    summary="List workspace members",
)
def list_workspace_members(
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
):
    """Returns all members of the workspace."""
    workspace, _ = context
    return crud_workspace.get_workspace_members(db, workspace_id=workspace.id)

@router.post(
    "/{slug}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add member to workspace",
)
def add_member_to_workspace(
    member_in: WorkspaceMemberAdd,
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
):
    """Allows OWNER or ADMIN to add a new member to the workspace."""
    workspace, membership = context

    # Role-Based Permission Check
    if membership.role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners and admins can add members.",
        )

    # Find the user to add
    user_to_add = crud_user.get_user_by_email(db, email=member_in.email)
    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found.",
        )

    # Check if already a member
    existing_member = crud_workspace.get_workspace_membership(
        db, workspace_id=workspace.id, user_id=user_to_add.id
    )
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this workspace.",
        )

    return crud_workspace.add_workspace_member(
        db, workspace_id=workspace.id, user_id=user_to_add.id, role=member_in.role
    )