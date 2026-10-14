import re
import secrets
from sqlalchemy.orm import Session

from project_management_api.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from project_management_api.schemas.workspace import WorkspaceCreate

def generate_unique_slug(db: Session, base_name: str) -> str:
    """Generates a clean URL slug from the name and ensures uniqueness."""
    slug = re.sub(r"[^a-z0-9]+", "-", base_name.lower()).strip("-")
    if not slug:
        slug = f"workspace-{secrets.token_hex(3)}"

    original_slug = slug
    counter = 1
    while db.query(Workspace).filter(Workspace.slug == slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1

    return slug

def create_workspace(db: Session, workspace_in: WorkspaceCreate, owner_id: int) -> Workspace:
    """Creates a workspace and automatically assigns the creator as OWNER."""
    slug = workspace_in.slug if workspace_in.slug else generate_unique_slug(db, workspace_in.name)

    db_workspace = Workspace(
        name=workspace_in.name,
        slug=slug,
        description=workspace_in.description,
        owner_id=owner_id,
    )
    db.add(db_workspace)
    db.flush()

    membership = WorkspaceMember(
        workspace_id=db_workspace.id,
        user_id=owner_id,
        role=WorkspaceRole.OWNER,
    )
    db.add(membership)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace

def get_workspaces_for_user(db: Session, user_id: int) -> list[Workspace]:
    """Returns all workspaces where the given user is a member."""
    return (
        db.query(Workspace)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .filter(WorkspaceMember.user_id == user_id)
        .all()
    )

def get_workspace_by_id(db: Session, workspace_id: int) -> Workspace | None:
    return db.query(Workspace).filter(Workspace.id == workspace_id).first()

def get_workspace_by_slug(db: Session, slug: str) -> Workspace | None:
    return db.query(Workspace).filter(Workspace.slug == slug).first()

def get_workspace_membership(db: Session, workspace_id: int, user_id: int) -> WorkspaceMember | None:
    """Checks whether a user is a member of the workspace."""
    return (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )

def get_workspace_members(db: Session, workspace_id: int) -> list[WorkspaceMember]:
    """Returns all members of a workspace."""
    return db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id).all()

def add_workspace_member(
    db: Session, workspace_id: int, user_id: int, role: WorkspaceRole = WorkspaceRole.MEMBER
) -> WorkspaceMember:
    """Adds a user to a workspace with the specified role."""
    membership = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user_id,
        role=role,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership