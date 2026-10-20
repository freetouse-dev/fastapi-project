from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from project_management_api.api.deps import get_current_user
from project_management_api.core.permissions import can_manage_workspace, can_manage_workspace_members
from project_management_api.crud import user as crud_user
from project_management_api.crud import workspace as crud_workspace
from project_management_api.db.session import get_db
from project_management_api.models.user import User
from project_management_api.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from project_management_api.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)

router = APIRouter()


def require_workspace_membership(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> tuple[Workspace, WorkspaceMember]:
    """
    Validates that active workspace exists and the user is an active member or superuser.
    Returns (workspace, membership). If user is superuser but not an explicit member,
    synthesizes a virtual owner membership.
    """
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
        if current_user.is_superuser:
            # Superuser gets synthesized OWNER privileges
            virtual_membership = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=current_user.id,
                role=WorkspaceRole.OWNER,
            )
            return workspace, virtual_membership

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
        existing = crud_workspace.get_workspace_by_slug(db, slug=workspace_in.slug, include_deleted=True)
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
    """Returns all active workspaces the current user is a member of (or all if superuser)."""
    if current_user.is_superuser:
        return crud_workspace.get_all_workspaces(db, include_deleted=False)
    return crud_workspace.get_workspaces_for_user(db, user_id=current_user.id)


@router.get(
    "/{slug}",
    response_model=WorkspaceResponse,
    summary="Get workspace by slug",
)
def get_workspace(
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
):
    """Gets workspace details if the user is an authorized member or admin."""
    workspace, _ = context
    return workspace


@router.patch(
    "/{slug}",
    response_model=WorkspaceResponse,
    summary="Update workspace",
)
def update_workspace(
    workspace_in: WorkspaceUpdate,
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates workspace details. Only OWNER or ADMIN can perform updates."""
    workspace, membership = context

    if not can_manage_workspace(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners and admins can update this workspace.",
        )

    return crud_workspace.update_workspace(
        db, db_workspace=workspace, workspace_in=workspace_in, actor_id=current_user.id
    )


@router.delete(
    "/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete workspace",
)
def delete_workspace(
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft-deletes a workspace and cascades to child projects, tasks, and comments.
    Preserves historical records for audit and reporting.
    """
    workspace, membership = context

    if not can_manage_workspace(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners and admins can delete this workspace.",
        )

    crud_workspace.soft_delete_workspace(db, db_workspace=workspace, actor_id=current_user.id)


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
    current_user: User = Depends(get_current_user),
):
    """Allows OWNER or ADMIN to add a new member to the workspace."""
    workspace, membership = context

    if not can_manage_workspace_members(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners and admins can add members.",
        )

    # An ADMIN cannot grant OWNER access
    if membership.role == WorkspaceRole.ADMIN and member_in.role == WorkspaceRole.OWNER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins cannot grant OWNER privileges.",
        )

    user_to_add = crud_user.get_user_by_email(db, email=member_in.email)
    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found.",
        )

    existing_member = crud_workspace.get_workspace_membership(
        db, workspace_id=workspace.id, user_id=user_to_add.id
    )
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this workspace.",
        )

    return crud_workspace.add_workspace_member(
        db,
        workspace_id=workspace.id,
        user_id=user_to_add.id,
        role=member_in.role,
        actor_id=current_user.id,
    )


@router.patch(
    "/{slug}/members/{user_id}",
    response_model=WorkspaceMemberResponse,
    summary="Update workspace member role",
)
def update_member_role(
    user_id: int,
    member_in: WorkspaceMemberUpdate,
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates member role within the workspace. Enforces owner demotion safety."""
    workspace, membership = context

    if not can_manage_workspace_members(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners and admins can modify member roles.",
        )

    target_membership = crud_workspace.get_workspace_membership(
        db, workspace_id=workspace.id, user_id=user_id
    )
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this workspace.",
        )

    # ADMIN cannot grant or revoke OWNER access
    is_super = current_user.is_superuser
    if membership.role == WorkspaceRole.ADMIN and not is_super:
        if member_in.role == WorkspaceRole.OWNER or target_membership.role == WorkspaceRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins cannot grant or revoke OWNER access.",
            )
        # ADMIN cannot elevate themselves
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins cannot alter their own privileges.",
            )

    return crud_workspace.update_workspace_member_role(
        db, membership=target_membership, new_role=member_in.role, actor_id=current_user.id
    )


@router.delete(
    "/{slug}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member from workspace",
)
def remove_member(
    user_id: int,
    context: tuple[Workspace, WorkspaceMember] = Depends(require_workspace_membership),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Removes a member from the workspace. Prevents removing the last active OWNER."""
    workspace, membership = context

    if not can_manage_workspace_members(membership, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners and admins can remove members.",
        )

    target_membership = crud_workspace.get_workspace_membership(
        db, workspace_id=workspace.id, user_id=user_id
    )
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this workspace.",
        )

    if membership.role == WorkspaceRole.ADMIN and not current_user.is_superuser:
        if target_membership.role == WorkspaceRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins cannot remove workspace owners.",
            )

    crud_workspace.remove_workspace_member(db, membership=target_membership, actor_id=current_user.id)