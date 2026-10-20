from sqlalchemy import or_
from sqlalchemy.orm import Session

from project_management_api.core.security import hash_password
from project_management_api.crud.audit import create_audit_log
from project_management_api.models.audit import AuditLog
from project_management_api.models.comment import TaskComment
from project_management_api.models.project import Project
from project_management_api.models.task import Task
from project_management_api.models.user import User
from project_management_api.models.workspace import Workspace
from project_management_api.schemas.audit import AdminStatsResponse
from project_management_api.schemas.user import UserAdminUpdate, UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    """Finds a user by email address."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Finds a user by primary key ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """Creates a new user record with hashed password."""
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
        is_active=user_in.is_active,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def get_users_paginated(
    db: Session,
    search: str | None = None,
    is_active: bool | None = None,
    is_verified: bool | None = None,
    is_superuser: bool | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[User], int]:
    """Admin function: returns filtered and paginated list of all users."""
    query = db.query(User)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
            )
        )
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)
    if is_superuser is not None:
        query = query.filter(User.is_superuser == is_superuser)

    total = query.count()
    items = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return items, total


def update_user_admin(
    db: Session, db_user: User, user_in: UserAdminUpdate, actor_id: int
) -> User:
    """Admin function: modifies user status, superuser privileges, or details with audit trail."""
    update_data = user_in.model_dump(exclude_unset=True)

    changes = {}
    for field, new_val in update_data.items():
        old_val = getattr(db_user, field)
        if old_val != new_val:
            changes[field] = {"old": old_val, "new": new_val}
            setattr(db_user, field, new_val)

    if changes:
        create_audit_log(
            db,
            action="USER_ADMIN_UPDATED",
            resource_type="USER",
            resource_id=db_user.id,
            actor_id=actor_id,
            details={"email": db_user.email, "changes": changes},
        )

    db.commit()
    db.refresh(db_user)
    return db_user


def get_admin_stats(db: Session) -> AdminStatsResponse:
    """Calculates platform-wide counts for the Admin Dashboard."""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    unverified_users = db.query(User).filter(User.is_verified == False).count()

    total_workspaces = db.query(Workspace).filter(Workspace.deleted_at.is_(None)).count()
    total_projects = db.query(Project).filter(Project.deleted_at.is_(None)).count()
    total_tasks = db.query(Task).filter(Task.deleted_at.is_(None)).count()
    total_comments = db.query(TaskComment).filter(TaskComment.deleted_at.is_(None)).count()
    total_audit_logs = db.query(AuditLog).count()

    return AdminStatsResponse(
        total_users=total_users,
        active_users=active_users,
        unverified_users=unverified_users,
        total_workspaces=total_workspaces,
        total_projects=total_projects,
        total_tasks=total_tasks,
        total_comments=total_comments,
        total_audit_logs=total_audit_logs,
    )