import re
import secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from project_management_api.crud.audit import create_audit_log
from project_management_api.models.comment import TaskComment
from project_management_api.models.project import Project
from project_management_api.models.task import Task
from project_management_api.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from project_management_api.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


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


def create_workspace(
    db: Session,
    workspace_in: WorkspaceCreate,
    owner_id: int,
    company_id: int | None = None,
) -> Workspace:
    """Creates a workspace and automatically assigns the creator as OWNER."""
    slug = workspace_in.slug if workspace_in.slug else generate_unique_slug(db, workspace_in.name)

    db_workspace = Workspace(
        name=workspace_in.name,
        slug=slug,
        description=workspace_in.description,
        owner_id=owner_id,
        company_id=company_id,
    )
    db.add(db_workspace)
    db.flush()

    membership = WorkspaceMember(
        workspace_id=db_workspace.id,
        user_id=owner_id,
        role=WorkspaceRole.OWNER,
    )
    db.add(membership)

    create_audit_log(
        db,
        action="WORKSPACE_CREATED",
        resource_type="WORKSPACE",
        resource_id=db_workspace.id,
        actor_id=owner_id,
        details={"name": db_workspace.name, "slug": db_workspace.slug, "company_id": company_id},
    )

    db.commit()
    db.refresh(db_workspace)
    return db_workspace


def get_workspaces_for_user(db: Session, user_id: int, company_id: int | None = None) -> list[Workspace]:
    """Returns all active workspaces where the given user is a member, optionally scoped to company."""
    query = (
        db.query(Workspace)
        .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
        .filter(
            WorkspaceMember.user_id == user_id,
            Workspace.deleted_at.is_(None),
        )
    )
    if company_id is not None:
        query = query.filter(Workspace.company_id == company_id)
    return query.all()


def get_workspaces_for_company(db: Session, company_id: int, include_deleted: bool = False) -> list[Workspace]:
    """Returns all workspaces belonging to a company."""
    query = db.query(Workspace).filter(Workspace.company_id == company_id)
    if not include_deleted:
        query = query.filter(Workspace.deleted_at.is_(None))
    return query.order_by(Workspace.created_at.desc()).all()


def get_all_workspaces(db: Session, include_deleted: bool = False) -> list[Workspace]:
    """Admin function: returns all workspaces."""
    query = db.query(Workspace)
    if not include_deleted:
        query = query.filter(Workspace.deleted_at.is_(None))
    return query.order_by(Workspace.created_at.desc()).all()


def get_workspace_by_id(db: Session, workspace_id: int, include_deleted: bool = False) -> Workspace | None:
    query = db.query(Workspace).filter(Workspace.id == workspace_id)
    if not include_deleted:
        query = query.filter(Workspace.deleted_at.is_(None))
    return query.first()


def get_workspace_by_slug(db: Session, slug: str, include_deleted: bool = False) -> Workspace | None:
    query = db.query(Workspace).filter(Workspace.slug == slug)
    if not include_deleted:
        query = query.filter(Workspace.deleted_at.is_(None))
    return query.first()


def update_workspace(
    db: Session,
    db_workspace: Workspace,
    workspace_in: WorkspaceUpdate,
    actor_id: int,
) -> Workspace:
    """Updates workspace details and writes an audit log."""
    old_data = {"name": db_workspace.name, "description": db_workspace.description}
    update_data = workspace_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_workspace, field, value)

    create_audit_log(
        db,
        action="WORKSPACE_UPDATED",
        resource_type="WORKSPACE",
        resource_id=db_workspace.id,
        actor_id=actor_id,
        details={"before": old_data, "after": update_data},
    )

    db.commit()
    db.refresh(db_workspace)
    return db_workspace


def soft_delete_workspace(db: Session, db_workspace: Workspace, actor_id: int) -> Workspace:
    """
    Soft-deletes a workspace and cascades to child projects, tasks, and comments
    within an atomic transaction. Preserves historical data and logs audit trail.
    """
    if db_workspace.deleted_at is not None:
        return db_workspace

    now = datetime.now(timezone.utc)
    db_workspace.deleted_at = now
    db_workspace.deleted_by_id = actor_id

    # 1. Find child projects
    projects = (
        db.query(Project)
        .filter(Project.workspace_id == db_workspace.id, Project.deleted_at.is_(None))
        .all()
    )

    for project in projects:
        project.deleted_at = now
        project.deleted_by_id = actor_id

        # 2. Find child tasks
        tasks = (
            db.query(Task)
            .filter(Task.project_id == project.id, Task.deleted_at.is_(None))
            .all()
        )
        for task in tasks:
            task.deleted_at = now
            task.deleted_by_id = actor_id

            # 3. Soft delete task comments
            db.query(TaskComment).filter(
                TaskComment.task_id == task.id,
                TaskComment.deleted_at.is_(None),
            ).update(
                {"deleted_at": now, "deleted_by_id": actor_id},
                synchronize_session=False,
            )

    create_audit_log(
        db,
        action="WORKSPACE_DELETED",
        resource_type="WORKSPACE",
        resource_id=db_workspace.id,
        actor_id=actor_id,
        details={"name": db_workspace.name, "slug": db_workspace.slug, "projects_count": len(projects)},
    )

    db.commit()
    db.refresh(db_workspace)
    return db_workspace


def restore_workspace(db: Session, db_workspace: Workspace, actor_id: int) -> Workspace:
    """Restores a soft-deleted workspace and records an audit log."""
    if db_workspace.deleted_at is None:
        return db_workspace

    db_workspace.deleted_at = None
    db_workspace.deleted_by_id = None

    create_audit_log(
        db,
        action="WORKSPACE_RESTORED",
        resource_type="WORKSPACE",
        resource_id=db_workspace.id,
        actor_id=actor_id,
        details={"name": db_workspace.name, "slug": db_workspace.slug},
    )

    db.commit()
    db.refresh(db_workspace)
    return db_workspace


def get_workspace_membership(db: Session, workspace_id: int, user_id: int) -> WorkspaceMember | None:
    """Checks whether a user is an active member of the workspace."""
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


def count_workspace_owners(db: Session, workspace_id: int) -> int:
    """Returns count of active owners in a workspace."""
    return (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.role == WorkspaceRole.OWNER,
        )
        .count()
    )


def add_workspace_member(
    db: Session,
    workspace_id: int,
    user_id: int,
    role: WorkspaceRole = WorkspaceRole.MEMBER,
    actor_id: int | None = None,
) -> WorkspaceMember:
    """Adds a user to a workspace with the specified role and logs audit trail."""
    membership = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user_id,
        role=role,
    )
    db.add(membership)

    create_audit_log(
        db,
        action="WORKSPACE_MEMBER_ADDED",
        resource_type="MEMBERSHIP",
        resource_id=f"{workspace_id}:{user_id}",
        actor_id=actor_id,
        details={"workspace_id": workspace_id, "user_id": user_id, "role": role.value},
    )

    db.commit()
    db.refresh(membership)
    return membership


def update_workspace_member_role(
    db: Session,
    membership: WorkspaceMember,
    new_role: WorkspaceRole,
    actor_id: int,
) -> WorkspaceMember:
    """
    Updates a workspace member's role.
    Prevents demoting the last active OWNER.
    """
    if membership.role == WorkspaceRole.OWNER and new_role != WorkspaceRole.OWNER:
        owner_count = count_workspace_owners(db, membership.workspace_id)
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last remaining owner of the workspace.",
            )

    old_role = membership.role
    membership.role = new_role

    create_audit_log(
        db,
        action="WORKSPACE_MEMBER_ROLE_UPDATED",
        resource_type="MEMBERSHIP",
        resource_id=f"{membership.workspace_id}:{membership.user_id}",
        actor_id=actor_id,
        details={"workspace_id": membership.workspace_id, "user_id": membership.user_id, "old_role": old_role.value, "new_role": new_role.value},
    )

    db.commit()
    db.refresh(membership)
    return membership


def remove_workspace_member(
    db: Session,
    membership: WorkspaceMember,
    actor_id: int,
) -> None:
    """
    Removes a member from a workspace.
    Prevents removing the last active OWNER.
    """
    if membership.role == WorkspaceRole.OWNER:
        owner_count = count_workspace_owners(db, membership.workspace_id)
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last remaining owner of the workspace.",
            )

    create_audit_log(
        db,
        action="WORKSPACE_MEMBER_REMOVED",
        resource_type="MEMBERSHIP",
        resource_id=f"{membership.workspace_id}:{membership.user_id}",
        actor_id=actor_id,
        details={"workspace_id": membership.workspace_id, "user_id": membership.user_id, "role": membership.role.value},
    )

    db.delete(membership)
    db.commit()